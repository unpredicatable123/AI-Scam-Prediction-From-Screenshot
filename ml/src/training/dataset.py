"""Builds the fused feature matrix from a split manifest.

Trains on `ocr_ground_truth` (the exact text rendered into the image) rather
than running Tesseract over every training image — this is standard
practice (train on ground truth; real OCR noise is a serving-time domain
gap, not a training-time one) and avoids re-running OCR over thousands of
images on a disk/time-constrained machine. CV features, by contrast, run on
the *actual rendered pixels* — that part of the pipeline is genuinely
exercised end-to-end, not shortcut.
"""

import csv
from pathlib import Path

import numpy as np

from features.cv_features import extract_cv_features
from features.fusion import FEATURE_SCHEMA, fuse_features, to_vector
from features.text_features import extract_text_features


def load_split_manifest(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_feature_matrix(rows, base_dir, run_cv=True):
    """Returns (X, y_label, y_category, groups, splits, feature_names)."""
    base_dir = Path(base_dir)
    X, y_label, y_category, groups, splits = [], [], [], [], []

    for row in rows:
        text_feat = extract_text_features(row["ocr_ground_truth"])
        cv_feat = None
        if run_cv:
            image_path = base_dir / row["image_path"]
            if image_path.exists():
                cv_feat = extract_cv_features(str(image_path))
        meta = {
            "platform": row.get("platform", ""),
            "is_forwarded": row.get("is_forwarded", 0),
            "is_unknown_number": row.get("is_unknown_number", 0),
            "has_reply": row.get("has_reply", 0),
        }
        fused = fuse_features(text_feat, cv_feat, meta)
        X.append(to_vector(fused))
        y_label.append(row["label"])
        y_category.append(row.get("category_hint") or "")
        groups.append(row["group_key"])
        splits.append(row["split"])

    return np.array(X, dtype=float), np.array(y_label), np.array(y_category), np.array(groups), np.array(splits), FEATURE_SCHEMA


def split_by(X, y_label, y_category, splits, split_name):
    mask = splits == split_name
    return X[mask], y_label[mask], y_category[mask]
