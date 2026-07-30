"""Evidence-grounded reason generation (blueprint §14.5).

Deliberately template-based, not LLM-generated: deterministic, reproducible,
cannot hallucinate evidence that isn't actually in the text, and adds no
latency or external dependency. Every reason is grounded in an actual quoted
phrase from the message wherever the underlying lexicon match makes that
possible — "urgency_score: 0.81" is exactly what this is designed to avoid.
"""

import re

from features.text_features import (
    AUTHORITY_WORDS, CONTACT_SHIFT_WORDS, CREDENTIAL_WORDS, FEE_FRAMING_WORDS,
    GREED_WORDS, INVESTMENT_WORDS, JOB_OFFER_WORDS, LOTTERY_WORDS,
    REWARD_WORDS, ROMANCE_WORDS, SCARCITY_WORDS, SECRECY_WORDS, THREAT_WORDS,
    URGENCY_WORDS, IFSC_RE, UPI_ID_RE, CRYPTO_WALLET_RE, _lexicon_pattern,
)
from features.brand_guard import detect_brand_typosquat
from features.conversation_flow import analyze_conversation_flow

from .groups import GROUP_LABELS


def _quote_first_match(text, words):
    m = _lexicon_pattern(words).search(text.lower())
    if not m:
        return None
    return text[m.start():m.end()]


def _reason_for_group(group, text, fused):
    if group == "urgency":
        phrase = _quote_first_match(text, URGENCY_WORDS)
        return f'Uses time-pressure language — "{phrase}"' if phrase else "Uses urgency language pressuring quick action"
    if group == "authority":
        phrase = _quote_first_match(text, AUTHORITY_WORDS)
        return f'Claims an official identity — mentions "{phrase}"' if phrase else "Claims to be from an official or authoritative source"
    if group == "reward":
        phrase = _quote_first_match(text, REWARD_WORDS)
        return f'Promises a reward — "{phrase}"' if phrase else "Promises a prize, reward, or guaranteed win"
    if group == "threat":
        phrase = _quote_first_match(text, THREAT_WORDS)
        return f'Threatens a consequence — "{phrase}"' if phrase else "Uses threatening language about account or legal consequences"
    if group == "secrecy":
        phrase = _quote_first_match(text, SECRECY_WORDS)
        return f'Asks you to keep this secret — "{phrase}"' if phrase else "Asks the recipient to keep the message confidential"
    if group == "financial_request":
        if fused.get("pay_to_receive_inversion"):
            return "Asks you to pay in order to receive money or a prize — a strong scam pattern"
        fee_phrase = _quote_first_match(text, FEE_FRAMING_WORDS)
        if fee_phrase:
            return f'Frames a payment as a required fee — "{fee_phrase}"'
        if fused.get("has_amount"):
            return "Asks for a specific monetary payment"
        return "Asks the recipient to send or transfer money"
    if group == "credential_request":
        phrase = _quote_first_match(text, CREDENTIAL_WORDS)
        return f'Asks for a sensitive credential — "{phrase}"' if phrase else "Asks for an OTP, PIN, password, or similar credential"
    if group == "contact_shift":
        phrase = _quote_first_match(text, CONTACT_SHIFT_WORDS)
        return f'Asks to move the conversation elsewhere — "{phrase}"' if phrase else "Asks to continue the conversation on another channel"
    if group == "url_risk":
        if fused.get("has_shortener_url"):
            return "Contains a shortened link that hides its real destination"
        if fused.get("has_ip_url"):
            return "Links to a raw IP address instead of a real domain"
        return "Contains a link with suspicious characteristics"
    if group == "qr_risk":
        if fused.get("qr_is_payment_intent") and fused.get("qr_has_prefilled_amount"):
            return "Contains a QR code that requests a payment with the amount pre-filled"
        if fused.get("qr_is_payment_intent"):
            return "Contains a QR code that initiates a payment"
        if fused.get("qr_is_url_risky"):
            return "Contains a QR code linking to a suspicious URL"
        return "Contains a QR code"
    if group == "layout":
        if fused.get("is_unknown_number"):
            return "Sent by a number not in your contacts"
        if fused.get("is_forwarded"):
            return "This message has been forwarded, common for mass-distributed scams"
        return "Reply pattern is consistent with a scripted scam conversation"
    if group == "scarcity":
        phrase = _quote_first_match(text, SCARCITY_WORDS)
        return f'Claims limited availability — "{phrase}"' if phrase else "Claims limited availability to pressure a fast decision"
    if group == "greed":
        phrase = _quote_first_match(text, GREED_WORDS)
        return f'Promises unusually high earnings — "{phrase}"' if phrase else "Promises unusually high or effortless earnings"
    if group == "romance":
        phrase = _quote_first_match(text, ROMANCE_WORDS)
        return f'Uses romantic language — "{phrase}"' if phrase else "Uses romantic or emotionally intimate language"
    if group == "investment_pitch":
        phrase = _quote_first_match(text, INVESTMENT_WORDS)
        return f'Pitches an investment — "{phrase}"' if phrase else "Pitches an investment or trading opportunity"
    if group == "lottery":
        phrase = _quote_first_match(text, LOTTERY_WORDS)
        return f'Claims a prize win — "{phrase}"' if phrase else "Claims a lottery, jackpot, or sweepstake win"
    if group == "job_offer":
        phrase = _quote_first_match(text, JOB_OFFER_WORDS)
        return f'Offers a job — "{phrase}"' if phrase else "Offers a job with vague or unusually easy requirements"
    if group == "payment_identifier":
        for label, pattern in (("UPI ID", UPI_ID_RE), ("IFSC code", IFSC_RE), ("crypto wallet address", CRYPTO_WALLET_RE)):
            m = pattern.search(text)
            if m:
                return f'Contains a real {label} — "{m.group(0)}"'
        return "Contains a payment identifier"
    if group == "brand_impersonation":
        check = detect_brand_typosquat(text)
        if check["is_impersonation"]:
            return f'Uses "{check["suspicious_token"]}", resembling the real brand "{check["matched_brand"]}"'
        return "Uses a name resembling a real company's brand"
    if group == "conversation_flow":
        flow = analyze_conversation_flow(text)
        if flow["sequence"]:
            readable = " → ".join(GROUP_LABELS.get(s, s) for s in flow["sequence"])
            return f"Message escalates through: {readable}"
        return "Message follows an escalating, scripted conversation pattern"
    return GROUP_LABELS.get(group, group)


def _has_evidence(group, fused):
    """A group's SHAP contribution can be positive even when its underlying
    signal is absent — tree interactions mean "low urgency" can still push a
    specific prediction toward fraudulent. Showing a reason anyway would be
    an unbacked claim (blueprint §14.5). Each group's reason is only ever
    emitted when its defining feature is actually present in this sample."""
    checks = {
        "urgency": fused.get("has_urgency"),
        "authority": fused.get("has_authority_claim"),
        "reward": fused.get("has_reward_claim"),
        "threat": fused.get("has_threat"),
        "secrecy": fused.get("has_secrecy"),
        "financial_request": fused.get("has_financial_request") or fused.get("has_fee_framing") or fused.get("has_amount"),
        "credential_request": fused.get("has_credential_request"),
        "contact_shift": fused.get("has_contact_shift"),
        "url_risk": fused.get("has_url"),
        "qr_risk": fused.get("qr_detected"),
        "layout": fused.get("is_forwarded") or fused.get("is_unknown_number"),
        "scarcity": fused.get("has_scarcity"),
        "greed": fused.get("has_greed"),
        "romance": fused.get("has_romance"),
        "investment_pitch": fused.get("has_investment_pitch"),
        "lottery": fused.get("has_lottery_claim"),
        "job_offer": fused.get("has_job_offer_lure"),
        "payment_identifier": fused.get("has_upi_id") or fused.get("has_ifsc_code") or fused.get("has_crypto_wallet"),
        "brand_impersonation": fused.get("has_brand_typosquat"),
        "conversation_flow": fused.get("conversation_ends_in_ask_or_threat"),
    }
    return bool(checks.get(group, False))


def generate_reasons(ranked_groups, text, fused, k=5, min_contribution=1e-4):
    """ranked_groups: output of shap_explainer.top_groups (pass a generous
    candidate count — this function filters by evidence presence first, so
    fewer than k may survive, and truncating the candidate list too early
    would understate genuinely available reasons).
    Returns a list of {group, label, text, contribution}, evidence-grounded
    and ordered by SHAP contribution magnitude, capped at k.

    Two independent gates, both required: `_has_evidence` (the underlying
    fact is actually true for this sample — catches the case where a
    group's aggregate SHAP value is positive purely from tree interactions
    even though the feature itself is absent) and `min_contribution` (the
    model actually weighted this group toward "fraudulent" — catches the
    opposite case, a true fact the model didn't meaningfully use, which
    surfaced as a real 0.0-contribution "reason" during testing)."""
    reasons = []
    for group, contribution in ranked_groups:
        if contribution < min_contribution:
            continue
        if not _has_evidence(group, fused):
            continue
        reasons.append({
            "group": group,
            "label": GROUP_LABELS.get(group, group),
            "text": _reason_for_group(group, text, fused),
            "contribution": round(contribution, 4),
        })
        if len(reasons) >= k:
            break
    return reasons
