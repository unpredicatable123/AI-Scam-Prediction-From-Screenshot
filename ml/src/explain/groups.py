"""Feature -> group mapping for grouped SHAP attribution (blueprint §14.3).

Grouping exists because raw per-feature SHAP values would surface things
like "financial_verb_count contributed 0.04" — technically correct, useless
to a user. Grouped, the same evidence becomes "Financial request" with a
human-readable reason attached in nlg.py.
"""

FEATURE_GROUPS = {
    "urgency_count": "urgency", "has_urgency": "urgency",
    "authority_count": "authority", "has_authority_claim": "authority",
    "reward_count": "reward", "has_reward_claim": "reward",
    "threat_count": "threat", "has_threat": "threat",
    "secrecy_count": "secrecy", "has_secrecy": "secrecy",
    "financial_verb_count": "financial_request", "has_financial_request": "financial_request",
    "fee_framing_count": "financial_request", "has_fee_framing": "financial_request",
    "has_amount": "financial_request", "amount_value_bucket": "financial_request",
    "financial_request_score": "financial_request", "pay_to_receive_inversion": "financial_request",
    "credential_request_count": "credential_request", "has_credential_request": "credential_request",
    "contact_shift_count": "contact_shift", "has_contact_shift": "contact_shift",
    "url_count": "url_risk", "has_url": "url_risk", "url_max_risk": "url_risk",
    "has_shortener_url": "url_risk", "has_ip_url": "url_risk",
    "exclamation_count": "grammar_style", "capital_ratio": "grammar_style",
    "message_length": "grammar_style", "word_count": "grammar_style",
    "avg_word_length": "grammar_style", "emoji_count": "grammar_style",
    "qr_detected": "qr_risk", "qr_count": "qr_risk", "qr_is_payment_intent": "qr_risk",
    "qr_has_prefilled_amount": "qr_risk", "qr_is_url": "qr_risk", "qr_is_url_risky": "qr_risk",
    "platform_whatsapp": "platform", "platform_telegram": "platform", "platform_sms": "platform",
    "platform_instagram": "platform", "platform_email": "platform",
    "is_forwarded": "layout", "is_unknown_number": "layout", "has_reply": "layout",
    # Psychology-of-manipulation categories, payment identifiers, brand
    # typosquat, and conversation escalation (intelligence-layer expansion —
    # see memory/project_ml_pipeline_status.md).
    "scarcity_count": "scarcity", "has_scarcity": "scarcity",
    "greed_count": "greed", "has_greed": "greed",
    "romance_count": "romance", "has_romance": "romance",
    "investment_count": "investment_pitch", "has_investment_pitch": "investment_pitch",
    "lottery_count": "lottery", "has_lottery_claim": "lottery",
    "job_offer_count": "job_offer", "has_job_offer_lure": "job_offer",
    "has_upi_id": "payment_identifier", "has_ifsc_code": "payment_identifier",
    "has_crypto_wallet": "payment_identifier",
    "has_brand_typosquat": "brand_impersonation",
    "has_mixed_script_url": "url_risk", "has_typosquat_url": "url_risk",
    "conversation_stage_count": "conversation_flow",
    "conversation_ends_in_ask_or_threat": "conversation_flow",
}

GROUP_LABELS = {
    "urgency": "Urgency language",
    "authority": "Claims authority",
    "reward": "Reward or prize claim",
    "threat": "Threat or fear language",
    "secrecy": "Asks for secrecy",
    "financial_request": "Financial request",
    "credential_request": "Credential request",
    "contact_shift": "Asks to change contact channel",
    "url_risk": "Suspicious link",
    "grammar_style": "Writing style",
    "qr_risk": "QR code risk",
    "platform": "Platform",
    "layout": "Message layout",
    "scarcity": "Scarcity pressure",
    "greed": "Unrealistic earnings promise",
    "romance": "Romantic or emotional language",
    "investment_pitch": "Investment pitch",
    "lottery": "Lottery or prize claim",
    "job_offer": "Job offer lure",
    "payment_identifier": "Payment details found",
    "brand_impersonation": "Possible brand impersonation",
    "conversation_flow": "Escalating conversation pattern",
}

# Only these groups are ever surfaced as "reasons" to the user — platform and
# grammar_style are real, useful model signal, but "written in a particular
# style" is not a legible reason a person can act on (blueprint §14.3: the
# interpretable features must outrank the opaque/marginal ones in explanations).
EXPLANATION_ELIGIBLE_GROUPS = {
    "urgency", "authority", "reward", "threat", "secrecy", "financial_request",
    "credential_request", "contact_shift", "url_risk", "qr_risk", "layout",
    "scarcity", "greed", "romance", "investment_pitch", "lottery", "job_offer",
    "payment_identifier", "brand_impersonation", "conversation_flow",
}
