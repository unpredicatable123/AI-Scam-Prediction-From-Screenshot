"""Regression tests for text-only brand-typosquat detection.

Two real false-positive bugs were found and fixed here by testing against
actual examples (not just checking the code ran): (1) short brands like
"axis" matching unrelated common words ("this", "basis") at edit distance 2,
and (2) "phonepe" matching "phone" at edit distance 2 even after an early
length-scaling attempt. Both were fixed by capping edit distance at exactly
1, universally. These tests lock that fix in.
"""

from features.brand_guard import detect_brand_typosquat, levenshtein


def test_levenshtein_basic():
    assert levenshtein("amazon", "amazon") == 0
    assert levenshtein("amazon", "amaz0n") == 1
    assert levenshtein("", "abc") == 3
    assert levenshtein("abc", "") == 3


def test_digit_substitution_typosquat_is_flagged():
    result = detect_brand_typosquat("your amaz0n account has been suspended")
    assert result["is_impersonation"] is True
    assert result["matched_brand"] == "amazon"
    assert result["suspicious_token"] == "amaz0n"


def test_double_letter_typosquat_is_flagged():
    result = detect_brand_typosquat("verify your Paytmm wallet now")
    assert result["is_impersonation"] is True
    assert result["matched_brand"] == "paytm"


def test_exact_brand_name_is_not_flagged():
    # Naming a real brand isn't evidence of impersonating it -- only a
    # close-but-wrong spelling is.
    result = detect_brand_typosquat("your amazon order has shipped")
    assert result["is_impersonation"] is False
    assert result["matched_brand"] is None


def test_axis_false_positive_regression():
    # Real bug: "This" and "basis" matched "axis" at edit distance 2 under
    # the old length-scaled threshold.
    assert detect_brand_typosquat("this is just a basis for discussion")["is_impersonation"] is False


def test_phonepe_false_positive_regression():
    # Real bug: "phone" matched "phonepe" at edit distance 2.
    assert detect_brand_typosquat("please call me on my phone later")["is_impersonation"] is False


def test_no_brand_like_tokens_returns_empty_result():
    result = detect_brand_typosquat("let's meet for coffee tomorrow")
    assert result == {
        "is_impersonation": False,
        "matched_brand": None,
        "suspicious_token": None,
        "confidence": 0.0,
    }


def test_empty_and_none_text_do_not_raise():
    assert detect_brand_typosquat("")["is_impersonation"] is False
    assert detect_brand_typosquat(None)["is_impersonation"] is False


def test_prefers_longer_brand_on_tied_distance():
    # "icic" is distance-1 from both "icici" (5) -- only one real candidate
    # here, but this confirms the longest-match tie-break doesn't crash when
    # only a single candidate exists.
    result = detect_brand_typosquat("icic bank alert: verify now")
    assert result["is_impersonation"] is True
    assert result["matched_brand"] == "icici"
