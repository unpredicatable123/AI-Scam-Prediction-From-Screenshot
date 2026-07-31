"""Tests for QR payload cleaning/classification.

Real bug found and fixed here: every image in ml/data/raw/benign/ (5,992
real donated QR photos, used as genuine-QR training examples) turns out to
encode a stringified pandas Series repr instead of a clean URL --
e.g. "0    https://www.google.com\\nName: url, dtype: object" -- a
data-generation bug upstream of this project's code. `_classify_payload`'s
`re.match(r"^https?://", ...)` anchors at the literal start of the string,
so it silently returned `is_url=False` for every one of those images. Fixed
by extracting the real URI out of the payload before classifying, rather
than trusting the decoded payload is already clean.
"""

from pathlib import Path

from features.cv_features import _clean_payload, _classify_payload, extract_cv_features

BENIGN_DIR = Path(__file__).parent.parent / "data" / "raw" / "benign"


def test_clean_url_payload_is_a_noop():
    payload = "https://paypal-secure.info/verify"
    assert _clean_payload(payload) == payload


def test_clean_upi_payload_is_a_noop():
    payload = "upi://pay?pa=collect1234@ybl&am=999&cu=INR"
    assert _clean_payload(payload) == payload


def test_pandas_repr_garbage_is_cleaned_to_the_real_url():
    garbage = "0    https://www.google.com\nName: url, dtype: object"
    assert _clean_payload(garbage) == "https://www.google.com"


def test_non_uri_payload_passes_through_unchanged():
    assert _clean_payload("just some plain text") == "just some plain text"


def test_classification_after_cleaning_a_garbage_payload():
    cleaned = _clean_payload("0    https://www.google.com\nName: url, dtype: object")
    is_url, is_payment_intent, has_amount = _classify_payload(cleaned)
    assert is_url is True
    assert is_payment_intent is False


def test_upi_amount_is_still_parsed_correctly():
    is_url, is_payment_intent, has_amount = _classify_payload("upi://pay?pa=x@ybl&am=999&cu=INR")
    assert is_payment_intent is True
    assert has_amount is True


# --- Regression against the actual corrupted corpus, not just synthetic strings ---


def _benign_samples():
    if not BENIGN_DIR.is_dir():
        return []
    return sorted(BENIGN_DIR.glob("*.png"))[:5]


def test_real_benign_qr_images_are_correctly_classified_as_urls():
    samples = _benign_samples()
    if not samples:
        import pytest

        pytest.skip("ml/data/raw/benign/ not present in this checkout")
    for path in samples:
        result = extract_cv_features(str(path))
        assert result["qr_detected"] == 1
        # This is the exact regression: before the fix, every one of these
        # came back qr_is_url=0 despite genuinely encoding a URL.
        assert result["qr_is_url"] == 1
        assert result["qr_payload_preview"].startswith("http")
        assert "dtype:" not in result["qr_payload_preview"]
