"""Feature fusion — the single ordered schema consumed by the models.

This is the module blueprint docs/BLUEPRINT.md §5.2[14] and §11.10 describe:
one place that defines feature order, so a silent reordering between
training and serving is structurally impossible (both call `to_vector`
against the same `FEATURE_SCHEMA`).

Layout signals (is_forwarded, is_unknown_number, has_reply, platform) come
free from the synthetic generator's own render metadata for training data.
At real inference time (an uploaded screenshot with no such metadata) these
default to 0/"unknown" — a known limitation: this pipeline does not include
a standalone layout-detection stage, so those three signals are only as good
as the training data's synthetic ground truth, not independently verified on
real uploads. Flagged, not hidden.
"""

from .cv_features import FEATURE_NAMES as CV_FEATURE_NAMES
from .text_features import FEATURE_NAMES as TEXT_FEATURE_NAMES

PLATFORMS = ["whatsapp", "telegram", "sms", "instagram", "email"]
PLATFORM_FEATURES = [f"platform_{p}" for p in PLATFORMS]
LAYOUT_FEATURES = ["is_forwarded", "is_unknown_number", "has_reply"]

FEATURE_SCHEMA = TEXT_FEATURE_NAMES + CV_FEATURE_NAMES + PLATFORM_FEATURES + LAYOUT_FEATURES
FEATURE_SCHEMA_VERSION = "v1"


def _to_bool_int(v):
    if isinstance(v, str):
        return int(v.strip().lower() in ("true", "1", "yes"))
    return int(bool(v))


def fuse_features(text_features: dict, cv_features: dict | None = None, meta: dict | None = None) -> dict:
    """Combines branch outputs into one ordered dict matching FEATURE_SCHEMA.

    text_features: output of text_features.extract_text_features
    cv_features: output of cv_features.extract_cv_features, or None if the
        visual branch was skipped/unavailable (missing-value policy: for QR
        features, "no QR branch result" and "no QR present" are the same
        thing — a QR either is or isn't in the image — so 0-fill is correct
        here, unlike features where "unknown" must be distinguished from
        "false" per the blueprint's general missing-value discussion).
    meta: optional dict with platform / is_forwarded / is_unknown_number / has_reply
    """
    meta = meta or {}
    fused = {}

    for name in TEXT_FEATURE_NAMES:
        fused[name] = text_features.get(name, 0)

    cv_features = cv_features or {}
    for name in CV_FEATURE_NAMES:
        fused[name] = cv_features.get(name, 0)

    platform = (meta.get("platform") or "").lower()
    for p, feat_name in zip(PLATFORMS, PLATFORM_FEATURES):
        fused[feat_name] = int(platform == p)

    for name in LAYOUT_FEATURES:
        fused[name] = _to_bool_int(meta.get(name, 0))

    return fused


def to_vector(fused: dict):
    """Orders a fused feature dict into a list matching FEATURE_SCHEMA — the
    only function anything downstream (training or serving) should use to
    turn features into model input."""
    return [fused.get(name, 0) for name in FEATURE_SCHEMA]
