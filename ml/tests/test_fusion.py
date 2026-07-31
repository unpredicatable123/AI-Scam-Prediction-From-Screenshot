"""Tests for the feature-fusion schema contract.

This is the module meant to make a training/serving feature mismatch
structurally impossible (see fusion.py's own docstring) -- but a real
version of exactly that mismatch happened anyway earlier this project: the
FastAPI service kept running against an old model bundle after
text_features.py grew from 47 to 67 features, and every request failed with
"Feature shape mismatch, expected: 47, got 67". These tests don't catch that
specific deployment mistake (wrong model on disk), but they do lock in the
one thing that must always be true of the code itself: fuse_features'
output and to_vector's length always match FEATURE_SCHEMA exactly.
"""

from features.fusion import fuse_features, to_vector, FEATURE_SCHEMA, PLATFORMS
from features.text_features import extract_text_features, FEATURE_NAMES as TEXT_FEATURE_NAMES
from features.cv_features import FEATURE_NAMES as CV_FEATURE_NAMES


def test_schema_length_is_67():
    # Pinned to the actual trained model's expected input size. If this
    # changes, a retrain is required -- see docs/DATASET.md / memory.
    assert len(FEATURE_SCHEMA) == 67


def test_schema_is_text_plus_cv_plus_platform_plus_layout():
    assert len(FEATURE_SCHEMA) == len(TEXT_FEATURE_NAMES) + len(CV_FEATURE_NAMES) + len(PLATFORMS) + 3


def test_fused_keys_exactly_match_schema():
    tf = extract_text_features("urgent: verify now")
    fused = fuse_features(tf, cv_features=None, meta={"platform": "whatsapp"})
    assert set(fused.keys()) == set(FEATURE_SCHEMA)


def test_to_vector_length_always_matches_schema():
    tf = extract_text_features("any text")
    fused = fuse_features(tf)
    assert len(to_vector(fused)) == len(FEATURE_SCHEMA)


def test_to_vector_order_matches_schema_order():
    tf = extract_text_features("urgent")
    fused = fuse_features(tf, meta={"platform": "sms"})
    vec = to_vector(fused)
    schema_index = FEATURE_SCHEMA.index("platform_sms")
    assert vec[schema_index] == 1


def test_missing_cv_features_default_to_zero():
    tf = extract_text_features("no qr here")
    fused = fuse_features(tf, cv_features=None)
    assert fused["qr_detected"] == 0
    assert fused["qr_is_payment_intent"] == 0


def test_platform_one_hot_is_mutually_exclusive():
    tf = extract_text_features("hi")
    fused = fuse_features(tf, meta={"platform": "whatsapp"})
    platform_flags = {p: fused[f"platform_{p}"] for p in PLATFORMS}
    assert platform_flags["whatsapp"] == 1
    assert sum(platform_flags.values()) == 1


def test_unknown_platform_sets_no_flag():
    tf = extract_text_features("hi")
    fused = fuse_features(tf, meta={"platform": "carrier_pigeon"})
    assert sum(fused[f"platform_{p}"] for p in PLATFORMS) == 0


def test_no_meta_defaults_everything_to_zero_or_unset():
    tf = extract_text_features("hi")
    fused = fuse_features(tf)
    assert sum(fused[f"platform_{p}"] for p in PLATFORMS) == 0
    assert fused["is_forwarded"] == 0
    assert fused["is_unknown_number"] == 0
    assert fused["has_reply"] == 0


def test_layout_flags_accept_string_booleans():
    # meta values coming from JSON/CSV can arrive as strings.
    tf = extract_text_features("hi")
    fused = fuse_features(tf, meta={"is_forwarded": "true", "has_reply": "false"})
    assert fused["is_forwarded"] == 1
    assert fused["has_reply"] == 0
