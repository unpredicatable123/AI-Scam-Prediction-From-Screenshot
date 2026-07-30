"""Interpretable NLP feature extraction (blueprint docs/BLUEPRINT.md §11.5).

Deliberately lexicon/regex-based rather than embedding-based: this machine is
disk-constrained (a full sentence-transformer + torch install was avoided
after a real disk-full incident during dataset generation), and interpretable
features are what the explanation layer (SHAP + NLG) actually needs to
produce grounded, human-readable reasons rather than opaque scores.

This module is the single source of truth for feature extraction — imported
by both training (ml/src/training/) and the serving API (apps/ai-service/),
per the blueprint's explicit rule against training/serving skew (§3.3).
"""

import re

from .brand_guard import detect_brand_typosquat, levenshtein
from .conversation_flow import analyze_conversation_flow

# Lexicons live in lexicons.py (conversation_flow.py needs them too, and
# importing them from here would be circular since this module imports
# analyze_conversation_flow from conversation_flow.py). Re-exported under
# the same names so existing callers (nlg.py, fusion.py) are unaffected.
from .lexicons import (  # noqa: F401
    AUTHORITY_WORDS, CONTACT_SHIFT_WORDS, CREDENTIAL_WORDS, FEE_FRAMING_WORDS,
    FINANCIAL_VERBS, GREED_WORDS, INVESTMENT_WORDS, JOB_OFFER_WORDS,
    LOTTERY_WORDS, REWARD_WORDS, ROMANCE_WORDS, SCARCITY_WORDS, SECRECY_WORDS,
    SHORTENER_DOMAINS, SUSPICIOUS_TLDS, THREAT_WORDS, URGENCY_WORDS,
    _count_hits, _lexicon_pattern,
)

URL_RE = re.compile(r"(https?://[^\s]+|www\.[^\s]+|\b[a-z0-9-]+\.(?:com|net|org|info|xyz|top|club|online|site|work|click|biz)\b[^\s]*)", re.IGNORECASE)
AMOUNT_RE = re.compile(r"[$₹€£]\s?[\d,]+(?:\.\d+)?|\b\d[\d,]{2,}\s?(?:usd|inr|rs\.?|rupees|dollars)\b", re.IGNORECASE)
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U0001F000-\U0001F02F\U00002600-\U000026FF]"
)
IP_URL_RE = re.compile(r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")

# --- Payment identifiers --------------------------------------------------
# Real, well-defined formats — not fuzzy heuristics. UPI handle suffixes are
# bank/PSP-issued and finite, so an allowlist of suffixes is far more
# precise than a generic "word@word" pattern (which would match any email).
UPI_HANDLE_SUFFIXES = (
    "ybl", "okhdfcbank", "oksbi", "okicici", "okaxis", "paytm", "apl",
    "ibl", "axl", "upi", "okbizaxis", "airtel", "jio",
)
UPI_ID_RE = re.compile(rf"\b[\w.\-]{{2,256}}@(?:{'|'.join(UPI_HANDLE_SUFFIXES)})\b", re.IGNORECASE)
# Real RBI-defined format: 4 letters (bank code) + 0 + 6 alphanumeric (branch).
IFSC_RE = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")
CRYPTO_WALLET_RE = re.compile(
    r"\b0x[a-fA-F0-9]{40}\b"  # Ethereum
    r"|\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b"  # Bitcoin (legacy/P2SH)
    r"|\bbc1[a-z0-9]{25,39}\b"  # Bitcoin (bech32)
)

# --- URL homograph / lookalike-domain detection ---------------------------
# Cyrillic/Greek characters that render near-identically to common Latin
# letters — a classic homograph-attack technique (e.g. "аmazon.com" with a
# Cyrillic а, U+0430, instead of Latin a, U+0061).
CONFUSABLE_CHARS = set("аеорсухАЕОРСУХіІѕ")
BRAND_DOMAINS = {
    "amazon": "amazon.com", "google": "google.com", "paypal": "paypal.com",
    "microsoft": "microsoft.com", "apple": "apple.com", "facebook": "facebook.com",
    "paytm": "paytm.com", "flipkart": "flipkart.com", "sbi": "onlinesbi.com",
    "hdfc": "hdfcbank.com", "icici": "icicibank.com",
}


def _has_mixed_script(url: str) -> bool:
    has_latin = any(c.isascii() and c.isalpha() for c in url)
    has_confusable = any(c in CONFUSABLE_CHARS for c in url)
    return has_latin and has_confusable


def _typosquat_domain_match(url: str):
    """Distance-1 match against a short list of commonly-impersonated
    domains — same reasoning as brand_guard.detect_brand_typosquat (distance
    capped at 1 after real testing showed distance 2 false-positives on
    short/common substrings)."""
    m = re.search(r"://(?:www\.)?([a-z0-9\-.]+)", url.lower())
    host = m.group(1) if m else url.lower()
    for brand, domain in BRAND_DOMAINS.items():
        if host == domain:
            continue
        if abs(len(host) - len(domain)) > 1:
            continue
        if levenshtein(host, domain) == 1:
            return brand
    return None


def _extract_urls(text):
    return URL_RE.findall(text)


def _url_risk_score(url):
    """0-1 lexical risk score for a single URL — no network access, ever
    (blueprint §11.7 / §5.3 rule 5: never fetch an extracted URL)."""
    score = 0.0
    url_lower = url.lower()
    if any(d in url_lower for d in SHORTENER_DOMAINS):
        score += 0.3
    if any(url_lower.endswith(t) or f"{t}/" in url_lower for t in SUSPICIOUS_TLDS):
        score += 0.25
    if IP_URL_RE.match(url):
        score += 0.35
    if url_lower.count("-") >= 2:
        score += 0.1
    if len(url) > 60:
        score += 0.1
    if _has_mixed_script(url):
        score += 0.35
    if _typosquat_domain_match(url):
        score += 0.35
    return min(score, 1.0)


FEATURE_NAMES = [
    "urgency_count", "has_urgency",
    "authority_count", "has_authority_claim",
    "reward_count", "has_reward_claim",
    "threat_count", "has_threat",
    "secrecy_count", "has_secrecy",
    "financial_verb_count", "has_financial_request",
    "fee_framing_count", "has_fee_framing",
    "has_amount", "amount_value_bucket",
    "credential_request_count", "has_credential_request",
    "contact_shift_count", "has_contact_shift",
    "url_count", "has_url", "url_max_risk", "has_shortener_url", "has_ip_url",
    "has_mixed_script_url", "has_typosquat_url",
    "exclamation_count", "capital_ratio", "message_length", "word_count",
    "avg_word_length", "emoji_count",
    "pay_to_receive_inversion",
    "financial_request_score",
    # Psychology-of-manipulation categories (item 3 of the intelligence-layer
    # expansion — see memory/project_ml_pipeline_status.md).
    "scarcity_count", "has_scarcity",
    "greed_count", "has_greed",
    "romance_count", "has_romance",
    "investment_count", "has_investment_pitch",
    "lottery_count", "has_lottery_claim",
    "job_offer_count", "has_job_offer_lure",
    # Payment identifier detection (item 6).
    "has_upi_id", "has_ifsc_code", "has_crypto_wallet",
    # Brand typosquat detection, text-only (item 4 — no logo/visual model exists).
    "has_brand_typosquat",
    # Conversation escalation order (item 2).
    "conversation_stage_count", "conversation_ends_in_ask_or_threat",
]


def extract_text_features(text: str) -> dict:
    """Pure function: text -> named interpretable feature dict.

    Every feature here is deliberately explanation-eligible — this is the
    feature set the SHAP layer attributes against, so names and semantics
    must stay human-readable (blueprint §14.3).
    """
    text = text or ""
    text_lower = text.lower()
    words = text.split()
    word_count = max(len(words), 1)

    urls = _extract_urls(text)
    url_risks = [_url_risk_score(u) for u in urls]

    amounts = AMOUNT_RE.findall(text)
    has_amount = len(amounts) > 0
    # Bucketed, not raw value, so it stays a stable, low-cardinality feature.
    amount_bucket = 0
    if has_amount:
        digits = re.sub(r"[^\d]", "", amounts[0])
        val = int(digits) if digits else 0
        amount_bucket = 1 if val < 500 else 2 if val < 5000 else 3 if val < 50000 else 4

    financial_verb_count = _count_hits(text_lower, FINANCIAL_VERBS)
    fee_count = _count_hits(text_lower, FEE_FRAMING_WORDS)
    reward_count = _count_hits(text_lower, REWARD_WORDS)

    # "pay to receive" inversion: reward/claim language co-occurring with a
    # financial ask — near-decisive for lottery/job/delivery scams per the
    # blueprint's NLP strategy (§11.8) and one of the few genuinely composite
    # (non-lexicon-lookup) features here.
    pay_to_receive = 1 if (reward_count > 0 and (financial_verb_count > 0 or fee_count > 0)) else 0

    financial_request_score = min(
        1.0, 0.35 * min(financial_verb_count, 2) + 0.35 * min(fee_count, 2) + 0.3 * has_amount
    )

    capitals = sum(1 for c in text if c.isupper())
    letters = sum(1 for c in text if c.isalpha())
    capital_ratio = round(capitals / letters, 3) if letters else 0.0

    scarcity_count = _count_hits(text_lower, SCARCITY_WORDS)
    greed_count = _count_hits(text_lower, GREED_WORDS)
    romance_count = _count_hits(text_lower, ROMANCE_WORDS)
    investment_count = _count_hits(text_lower, INVESTMENT_WORDS)
    lottery_count = _count_hits(text_lower, LOTTERY_WORDS)
    job_offer_count = _count_hits(text_lower, JOB_OFFER_WORDS)

    brand_check = detect_brand_typosquat(text)
    flow = analyze_conversation_flow(text)

    return {
        "urgency_count": _count_hits(text_lower, URGENCY_WORDS),
        "has_urgency": int(_count_hits(text_lower, URGENCY_WORDS) > 0),
        "authority_count": _count_hits(text_lower, AUTHORITY_WORDS),
        "has_authority_claim": int(_count_hits(text_lower, AUTHORITY_WORDS) > 0),
        "reward_count": reward_count,
        "has_reward_claim": int(reward_count > 0),
        "threat_count": _count_hits(text_lower, THREAT_WORDS),
        "has_threat": int(_count_hits(text_lower, THREAT_WORDS) > 0),
        "secrecy_count": _count_hits(text_lower, SECRECY_WORDS),
        "has_secrecy": int(_count_hits(text_lower, SECRECY_WORDS) > 0),
        "financial_verb_count": financial_verb_count,
        "has_financial_request": int(financial_verb_count > 0),
        "fee_framing_count": fee_count,
        "has_fee_framing": int(fee_count > 0),
        "has_amount": int(has_amount),
        "amount_value_bucket": amount_bucket,
        "credential_request_count": _count_hits(text_lower, CREDENTIAL_WORDS),
        "has_credential_request": int(_count_hits(text_lower, CREDENTIAL_WORDS) > 0),
        "contact_shift_count": _count_hits(text_lower, CONTACT_SHIFT_WORDS),
        "has_contact_shift": int(_count_hits(text_lower, CONTACT_SHIFT_WORDS) > 0),
        "url_count": len(urls),
        "has_url": int(len(urls) > 0),
        "url_max_risk": round(max(url_risks), 3) if url_risks else 0.0,
        "has_shortener_url": int(any(d in u.lower() for u in urls for d in SHORTENER_DOMAINS)),
        "has_ip_url": int(any(IP_URL_RE.match(u) for u in urls)),
        "has_mixed_script_url": int(any(_has_mixed_script(u) for u in urls)),
        "has_typosquat_url": int(any(_typosquat_domain_match(u) for u in urls)),
        "exclamation_count": text.count("!"),
        "capital_ratio": capital_ratio,
        "message_length": len(text),
        "word_count": word_count,
        "avg_word_length": round(sum(len(w) for w in words) / word_count, 2) if words else 0.0,
        "emoji_count": len(EMOJI_RE.findall(text)),
        "pay_to_receive_inversion": pay_to_receive,
        "financial_request_score": round(financial_request_score, 3),
        "scarcity_count": scarcity_count,
        "has_scarcity": int(scarcity_count > 0),
        "greed_count": greed_count,
        "has_greed": int(greed_count > 0),
        "romance_count": romance_count,
        "has_romance": int(romance_count > 0),
        "investment_count": investment_count,
        "has_investment_pitch": int(investment_count > 0),
        "lottery_count": lottery_count,
        "has_lottery_claim": int(lottery_count > 0),
        "job_offer_count": job_offer_count,
        "has_job_offer_lure": int(job_offer_count > 0),
        "has_upi_id": int(bool(UPI_ID_RE.search(text))),
        "has_ifsc_code": int(bool(IFSC_RE.search(text))),
        "has_crypto_wallet": int(bool(CRYPTO_WALLET_RE.search(text))),
        "has_brand_typosquat": int(brand_check["is_impersonation"]),
        "conversation_stage_count": flow["stage_count"],
        "conversation_ends_in_ask_or_threat": int(flow["ends_in_ask_or_threat"]),
    }


# Human-readable descriptions for the explanation layer (blueprint §11.10:
# every feature declares a description used by NLG templates).
FEATURE_DESCRIPTIONS = {
    "has_urgency": "Uses urgency or time-pressure language",
    "has_authority_claim": "Claims to be from a bank, government body, or official department",
    "has_reward_claim": "Promises a prize, reward, or guaranteed win",
    "has_threat": "Threatens account suspension, penalties, or legal action",
    "has_secrecy": "Asks the recipient to keep the message confidential",
    "has_financial_request": "Asks the recipient to pay, send, or transfer money",
    "has_fee_framing": "Frames a payment as a required fee, deposit, or charge",
    "has_amount": "Mentions a specific monetary amount",
    "has_credential_request": "Asks for an OTP, PIN, password, or other credential",
    "has_contact_shift": "Asks to move the conversation to another number or app",
    "has_url": "Contains a link",
    "has_shortener_url": "Uses a URL shortener, hiding the real destination",
    "has_ip_url": "Links to a raw IP address instead of a domain name",
    "has_mixed_script_url": "Link uses look-alike characters to disguise its real domain",
    "has_typosquat_url": "Link's domain is a near-misspelling of a known brand's real domain",
    "pay_to_receive_inversion": "Asks for payment in order to receive money or a prize",
    "has_scarcity": "Claims limited availability to pressure a fast decision",
    "has_greed": "Promises unusually high or effortless earnings",
    "has_romance": "Uses romantic or emotionally intimate language",
    "has_investment_pitch": "Pitches an investment or trading opportunity",
    "has_lottery_claim": "Claims a lottery, jackpot, or sweepstake win",
    "has_job_offer_lure": "Offers a job with vague or unusually easy requirements",
    "has_upi_id": "Contains a UPI payment ID",
    "has_ifsc_code": "Contains a bank IFSC code",
    "has_crypto_wallet": "Contains a cryptocurrency wallet address",
    "has_brand_typosquat": "Uses a misspelled brand name resembling a real company",
    "conversation_ends_in_ask_or_threat": "The message builds up to a money/credential request or a threat",
}
