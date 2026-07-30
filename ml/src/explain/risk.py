"""Risk score — deliberately separate from model confidence (blueprint §14.4).

Confidence measures how sure the model is. Risk measures how dangerous the
situation is *for the user*. A message asking for a credential is high-risk
even at moderate confidence, because the downside of being wrong in the
"safe" direction is catastrophic and the safe advice doesn't change either way.
"""

RISK_BANDS = [
    (20, "safe"),
    (40, "low"),
    (60, "medium"),
    (80, "high"),
    (101, "critical"),
]


def compute_risk_score(fraud_probability: float, fused: dict) -> float:
    severity = (
        0.15 * fused.get("has_credential_request", 0)
        + 0.15 * (fused.get("qr_is_payment_intent", 0) and fused.get("qr_has_prefilled_amount", 0))
        + 0.10 * fused.get("financial_request_score", 0)
        + 0.05 * fused.get("has_threat", 0)
    )
    score = 0.55 * fraud_probability + severity
    return round(min(max(score, 0.0), 1.0) * 100, 1)


def risk_band(score: float) -> str:
    for threshold, band in RISK_BANDS:
        if score < threshold:
            return band
    return "critical"
