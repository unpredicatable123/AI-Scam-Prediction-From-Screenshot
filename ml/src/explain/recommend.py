"""Recommendation engine (blueprint §14.6, §AI-20).

Keyed by detected signals rather than the (unverified) category hint — more
robust given category_hint is a source-file label, not annotated ground
truth, and the safety advice for "asks for a credential" or "asks for
payment via QR" is the same regardless of which of the 7 categories it
technically belongs to.
"""


def recommend(fused: dict, risk_band_name: str) -> list[str]:
    if risk_band_name in ("safe", "low"):
        return ["No strong scam signals detected — still, verify unfamiliar senders independently before acting."]

    actions = []
    if fused.get("has_credential_request"):
        actions.append("Never share an OTP, PIN, password, or CVV — no legitimate service will ever ask for one this way.")
    if fused.get("qr_is_payment_intent"):
        actions.append("Do not scan this QR code — scanning a payment QR sends money, it never receives it.")
    if fused.get("has_financial_request") or fused.get("has_fee_framing"):
        actions.append("Don't pay any upfront fee, deposit, or 'registration charge' — legitimate opportunities don't require this.")
    if fused.get("has_url") and (fused.get("has_shortener_url") or fused.get("has_ip_url") or fused.get("url_max_risk", 0) > 0.3):
        actions.append("Don't click the link — go to the organization's official site or app directly instead.")
    if fused.get("has_contact_shift"):
        actions.append("Be cautious about moving the conversation to a new number or app — this is a common tactic to escape platform safety checks.")
    if fused.get("is_unknown_number"):
        actions.append("This is from a number not in your contacts — verify the sender's identity through a separate, trusted channel.")

    actions.append("Report and block this sender.")
    # De-duplicate while preserving order (multiple signals can suggest the
    # same action).
    seen = set()
    deduped = []
    for a in actions:
        if a not in seen:
            deduped.append(a)
            seen.add(a)
    return deduped
