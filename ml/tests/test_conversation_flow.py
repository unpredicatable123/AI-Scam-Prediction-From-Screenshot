"""Tests for escalation-order analysis.

Every expected value below was confirmed by actually running the function
(not hand-derived) -- see the live-verification note in
memory/project_ml_pipeline_status.md for the first case, which was also
checked end-to-end through the real OCR/API pipeline earlier in the project.
"""

from features.conversation_flow import analyze_conversation_flow


def test_full_escalation_is_critical():
    text = (
        "Hi, this is urgent, please respond right away. Your bank account "
        "requires immediate verification of your password and OTP. If you "
        "do not comply within 1 hour your account will be blocked and "
        "legal action will be taken against you."
    )
    result = analyze_conversation_flow(text)
    assert result["conversation_risk"] == "critical"
    assert result["stage_count"] == 4
    assert result["ends_in_ask_or_threat"] is True
    assert result["sequence"] == ["urgency", "authority", "credential_request", "threat"]


def test_two_stages_ending_in_urgency_is_medium_not_high():
    text = "Congratulations! Pay Rs 499 UPI ID scamalert@okhdfcbank to claim your prize NOW before it expires. Reply URGENT to confirm."
    result = analyze_conversation_flow(text)
    assert result["conversation_risk"] == "medium"
    assert result["stage_count"] == 2
    assert result["ends_in_ask_or_threat"] is False
    assert result["sequence"] == ["financial_request", "urgency"]


def test_clean_message_is_low_with_empty_sequence():
    text = "Hey, are we still meeting for coffee tomorrow at 5pm near the station? Let me know if that works for you, no rush at all."
    result = analyze_conversation_flow(text)
    assert result == {
        "conversation_risk": "low",
        "stage_count": 0,
        "ends_in_ask_or_threat": False,
        "sequence": [],
    }


def test_single_isolated_stage_is_low_not_medium():
    # One mention of an authority word alone isn't an escalation pattern.
    result = analyze_conversation_flow("I went to the bank today")
    assert result["conversation_risk"] == "low"
    assert result["stage_count"] == 1


def test_three_stages_ending_in_ask_is_high():
    text = "This is your bank. Please respond immediately. You must pay now to avoid issues."
    result = analyze_conversation_flow(text)
    assert result["conversation_risk"] == "high"
    assert result["stage_count"] == 3
    assert result["ends_in_ask_or_threat"] is True
    assert result["sequence"] == ["authority", "urgency", "financial_request"]


def test_many_stages_not_ending_in_ask_or_threat_is_medium_not_critical():
    # >=4 stages alone isn't enough for "critical" -- it must also *end* in
    # an ask/threat stage. Here "authority" (not ask-or-threat) comes last.
    text = "Please pay now. Enter your password. Your account was suspended. This is the bank."
    result = analyze_conversation_flow(text)
    assert result["conversation_risk"] == "medium"
    assert result["ends_in_ask_or_threat"] is False
    assert result["sequence"][-1] == "authority"


def test_empty_text_does_not_raise():
    result = analyze_conversation_flow("")
    assert result["stage_count"] == 0
    assert result["conversation_risk"] == "low"
    result_none = analyze_conversation_flow(None)
    assert result_none["stage_count"] == 0
