"""Shared word-lists and lexicon-matching helpers.

Split out of text_features.py so conversation_flow.py can reuse the same
lexicons without importing text_features.py itself, which would create a
circular import (text_features.py imports analyze_conversation_flow from
conversation_flow.py). text_features.py re-exports these names, so nothing
that already imports lexicons from `features.text_features` needs to change.
"""

import re

URGENCY_WORDS = [
    "immediately", "urgent", "urgently", "now", "asap", "expire", "expires",
    "expiring", "today only", "act now", "last chance", "final notice",
    "within 24 hours", "within 5 minutes", "hurry", "limited time",
    "before it's too late", "don't miss", "deadline", "right away",
]

AUTHORITY_WORDS = [
    "bank", "official", "support team", "customer service", "government",
    "irs", "tax", "police", "legal action", "compliance", "department",
    "administrator", "verified", "security team", "helpdesk", "head office",
]

REWARD_WORDS = [
    "congratulations", "winner", "won", "selected", "prize", "reward",
    "cashback", "bonus", "free", "guaranteed", "lucky", "claim your",
    "you have been chosen", "exclusive offer", "no risk",
]

THREAT_WORDS = [
    "suspended", "locked", "blocked", "terminated", "penalty", "fine",
    "legal action", "arrest", "closed permanently", "restricted",
    "unauthorized access", "account will be closed", "deactivated",
]

SECRECY_WORDS = [
    "don't tell", "do not tell", "confidential", "keep this between us",
    "don't share with", "do not share with", "just between", "secret",
    "private matter", "not authorized to discuss",
]

FINANCIAL_VERBS = [
    "pay", "send", "transfer", "deposit", "recharge", "wire", "remit",
    "purchase gift cards", "buy gift cards",
]

FEE_FRAMING_WORDS = [
    "registration fee", "processing fee", "processing charge", "security deposit",
    "verification fee", "handling fee", "gst", "customs fee", "clearance fee",
    "activation fee", "convenience fee",
]

CREDENTIAL_WORDS = [
    "otp", "one time password", "one-time password", "pin", "cvv",
    "password", "aadhaar", "pan card", "ssn", "social security",
    "verification code", "security code", "bank details", "account number",
    "card number",
]

CONTACT_SHIFT_WORDS = [
    "whatsapp me", "message me on", "telegram me", "contact me on",
    "call this number", "reply to this number", "click to join group",
    "add me on", "reach out on",
]

# Psychology-of-manipulation categories, distinct from the overlapping ones
# above where possible — e.g. LOTTERY_WORDS deliberately avoids re-listing
# "lucky"/"claim your", which REWARD_WORDS already covers, so a lottery
# message doesn't just silently double-count as generic reward language.
SCARCITY_WORDS = [
    "limited stock", "only 2 left", "few remaining", "while supplies last",
    "limited seats", "almost sold out", "limited slots", "closing soon",
]

GREED_WORDS = [
    "easy money", "get rich quick", "double your money", "guaranteed returns",
    "high returns", "passive income", "unlimited earning", "earn daily",
    "earn while you sleep",
]

ROMANCE_WORDS = [
    "my love", "my dear", "soulmate", "miss you so much", "lonely heart",
    "true love", "meant to be", "destiny brought us",
]

INVESTMENT_WORDS = [
    "invest now", "trading profit", "forex trading", "crypto investment",
    "investment opportunity", "high roi", "stock tip", "guaranteed profit",
]

LOTTERY_WORDS = [
    "lottery", "jackpot", "sweepstake", "winning ticket", "lucky draw", "raffle",
]

JOB_OFFER_WORDS = [
    "work from home", "part time job", "earn per day", "no experience required",
    "data entry job", "online job offer", "job vacancy", "flexible working hours",
]

SHORTENER_DOMAINS = [
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly",
    "rebrand.ly", "cutt.ly",
]

SUSPICIOUS_TLDS = [".xyz", ".info", ".top", ".club", ".online", ".site", ".work", ".click"]


_lexicon_pattern_cache = {}


def _lexicon_pattern(words):
    """Compiles a word-boundary regex for a lexicon, cached by identity of
    the list object (the module-level lexicons never change at runtime)."""
    key = id(words)
    if key not in _lexicon_pattern_cache:
        alternatives = "|".join(re.escape(w) for w in words)
        _lexicon_pattern_cache[key] = re.compile(rf"\b(?:{alternatives})\b")
    return _lexicon_pattern_cache[key]


def _count_hits(text_lower, words):
    # Word-boundary matching, not naive substring search — "now" must not
    # match inside "know"/"known" (a real false-positive caught by testing
    # against a genuine sample: "know" silently contains "now").
    return len(_lexicon_pattern(words).findall(text_lower))
