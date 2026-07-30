"""Text-only brand-impersonation detection.

Fuzzy-matches brand-like tokens in OCR'd text against a small list of
commonly-impersonated brand names, catching typosquats like "amaz0n",
"Paytmm", "Gooogle". This is deliberately NOT visual logo/color/font
verification — no brand-image-matching model exists in this codebase, and
building one is out of scope here (same reasoning as omitting Logo
Detection/Visual Analysis on the result page — see
memory/project_ml_pipeline_status.md). An exact brand-name match is not
flagged; naming a real brand isn't evidence of impersonating it, only a
close-but-wrong spelling is.
"""

import re

KNOWN_BRANDS = [
    "amazon", "google", "paypal", "microsoft", "apple", "facebook", "instagram",
    "whatsapp", "netflix", "paytm", "phonepe", "flipkart", "irctc", "uidai",
    "sbi", "hdfc", "icici", "kotak", "axis",
]

TOKEN_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9]{2,20}\b")


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a or not b:
        return max(len(a), len(b))
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
        prev = cur
    return prev[-1]


def detect_brand_typosquat(text: str) -> dict:
    """Returns the closest-matching brand typosquat found, or an all-empty
    result.

    Edit distance is capped at exactly 1, universally — not scaled by brand
    length. Real testing surfaced two distinct false-positive classes at
    distance 2: short brands ("axis") matching unrelated common words
    ("this", "basis"), and longer brands with a short common-word prefix
    ("phonepe" matching "phone"). Every genuine typosquat example tested
    (amaz0n/amazon, Paytmm/paytm, Gooogle/google, microsofy/microsoft,
    icic/icici) is distance 1 — one substitution, insertion, or deletion —
    so distance 1 loses no real detections while rejecting both false-
    positive classes.

    Candidates are collected and ranked rather than returned on first match:
    tokens come from a `set()` for dedup, whose iteration order isn't
    guaranteed, so "first match found" would have been nondeterministic."""
    tokens = set(TOKEN_RE.findall(text or ""))
    candidates = []
    for token in tokens:
        token_lower = token.lower()
        if len(token_lower) < 4:
            continue
        for brand in KNOWN_BRANDS:
            if token_lower == brand:
                continue
            if abs(len(token_lower) - len(brand)) > 1:
                continue
            dist = levenshtein(token_lower, brand)
            if dist == 1:
                candidates.append((token, brand))

    if not candidates:
        return {"is_impersonation": False, "matched_brand": None, "suspicious_token": None, "confidence": 0.0}

    # Prefer the longer brand name when multiple candidates tie on distance —
    # a match against a longer, more distinctive brand name is less likely
    # to be coincidental than one against a short brand.
    token, brand = max(candidates, key=lambda c: len(c[1]))
    return {
        "is_impersonation": True,
        "matched_brand": brand,
        "suspicious_token": token,
        "confidence": round(1 - 1 / max(len(brand), len(token)), 2),
    }
