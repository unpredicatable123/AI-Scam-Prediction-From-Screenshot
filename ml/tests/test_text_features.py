"""Tests for the interpretable text feature extractor.

Covers the real regex-based signals added this project (UPI/IFSC/crypto
payment identifiers, URL homograph + typosquat detection) plus the schema
contract that caused a real production bug once already (the FastAPI
service crashed with "Feature shape mismatch, expected: 47, got 67" when
the model bundle and the feature code fell out of sync).
"""

from features.text_features import extract_text_features, FEATURE_NAMES


def test_schema_completeness():
    # Every declared feature name must actually be returned, and nothing
    # extra -- this is the exact contract whose violation once caused a
    # live "Feature shape mismatch" 500 error.
    result = extract_text_features("any text")
    assert set(result.keys()) == set(FEATURE_NAMES)
    assert len(result) == len(FEATURE_NAMES)


def test_valid_upi_id_is_detected():
    f = extract_text_features("Pay to scamalert@okhdfcbank now")
    assert f["has_upi_id"] == 1


def test_invalid_upi_handle_is_not_detected():
    # "okhdfc" is not a real NPCI-issued handle suffix -- "okhdfcbank" is.
    # The allowlist must not loosely match arbitrary "word@word" text.
    f = extract_text_features("Pay to scamalert@okhdfc now")
    assert f["has_upi_id"] == 0


def test_valid_ifsc_code_is_detected():
    f = extract_text_features("IFSC code HDFC0001234 for transfer")
    assert f["has_ifsc_code"] == 1


def test_ethereum_wallet_is_detected():
    f = extract_text_features("Send funds to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1")
    assert f["has_crypto_wallet"] == 1


def test_bitcoin_wallet_is_detected():
    f = extract_text_features("Send funds to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    assert f["has_crypto_wallet"] == 1


def test_mixed_script_homograph_url_is_detected():
    # Cyrillic 'а' (U+0430) instead of Latin 'a' in "amazon".
    f = extract_text_features("Verify at http://аmazon-secure.com now")
    assert f["has_mixed_script_url"] == 1


def test_close_typosquat_domain_is_detected():
    f = extract_text_features("Verify your account at http://amaz0n.com immediately")
    assert f["has_typosquat_url"] == 1


def test_clean_url_is_not_flagged_as_typosquat_or_mixed_script():
    f = extract_text_features("See our site at http://example.com")
    assert f["has_typosquat_url"] == 0
    assert f["has_mixed_script_url"] == 0
    assert f["has_url"] == 1
    assert f["url_count"] == 1


def test_pay_to_receive_inversion():
    f = extract_text_features("Congratulations you won! Pay a small fee to claim your prize")
    assert f["pay_to_receive_inversion"] == 1


def test_no_pay_to_receive_inversion_without_both_signals():
    f = extract_text_features("Congratulations, you won a free gift")
    assert f["pay_to_receive_inversion"] == 0


def test_capital_ratio_with_no_letters_does_not_divide_by_zero():
    f = extract_text_features("12345 !!! ????")
    assert f["capital_ratio"] == 0.0


def test_empty_text_does_not_raise():
    f = extract_text_features("")
    assert f["word_count"] == 1  # max(len(words), 1) floor
    assert f["message_length"] == 0
    f_none = extract_text_features(None)
    assert f_none["message_length"] == 0


def test_urgency_and_credential_words_are_counted():
    f = extract_text_features("URGENT: verify your OTP immediately")
    assert f["has_urgency"] == 1
    assert f["has_credential_request"] == 1
