"""Conversation-flow / escalation-order analysis.

Lexicon counts alone can't distinguish a message that happens to mention
"bank" and "urgent" in unrelated sentences from one that opens with a claimed
authority, escalates to urgency, then asks for money or credentials, then
threatens a consequence — the second is the actual scam pattern the category
counts were originally meant to approximate. This finds *where* each existing
lexicon category first appears in the text and checks whether they occur in
that escalation order, rather than just whether they occur at all.
"""

from .lexicons import (
    AUTHORITY_WORDS,
    CREDENTIAL_WORDS,
    FEE_FRAMING_WORDS,
    FINANCIAL_VERBS,
    THREAT_WORDS,
    URGENCY_WORDS,
    _lexicon_pattern,
)

# A fixed module-level list (not built per-call) so `_lexicon_pattern`'s
# id()-keyed cache actually caches instead of growing unbounded — passing a
# freshly-concatenated list on every call would give it a new id() each time.
FINANCIAL_REQUEST_WORDS = FINANCIAL_VERBS + FEE_FRAMING_WORDS

STAGE_LEXICONS = [
    ("authority", AUTHORITY_WORDS),
    ("urgency", URGENCY_WORDS),
    ("financial_request", FINANCIAL_REQUEST_WORDS),
    ("credential_request", CREDENTIAL_WORDS),
    ("threat", THREAT_WORDS),
]

ASK_OR_THREAT_STAGES = {"financial_request", "credential_request", "threat"}


def analyze_conversation_flow(text: str) -> dict:
    """Returns which of the 5 stages appear, in what order, and a
    conversation_risk label. Stage count and "ends in an ask or threat" are
    also exposed as plain values so callers can turn them into model
    features without re-deriving the escalation logic."""
    text_lower = (text or "").lower()
    positions = {}
    for name, words in STAGE_LEXICONS:
        m = _lexicon_pattern(words).search(text_lower)
        if m:
            positions[name] = m.start()

    ordered = sorted(positions.items(), key=lambda kv: kv[1])
    sequence = [name for name, _ in ordered]
    stage_count = len(sequence)
    ends_in_ask_or_threat = bool(sequence) and sequence[-1] in ASK_OR_THREAT_STAGES

    if stage_count >= 4 and ends_in_ask_or_threat:
        risk = "critical"
    elif stage_count == 3 and ends_in_ask_or_threat:
        risk = "high"
    elif stage_count >= 2:
        risk = "medium"
    else:
        risk = "low"

    return {
        "conversation_risk": risk,
        "stage_count": stage_count,
        "ends_in_ask_or_threat": ends_in_ask_or_threat,
        "sequence": sequence,
    }
