"""Trains the two-stage classifier (blueprint §13).

Stage 1 (binary genuine/fraudulent) trains on real, reliable labels — every
source dataset's own ground truth. Stage 2 (7-class category) trains on
`category_hint`, which is explicitly NOT verified ground truth (see
ingest.py's own docstring and README) — it is the source file/source-type
name, not an annotated label. Stage 2 output is reported and saved but
flagged everywhere as preliminary pending real annotation (blueprint AD-01).
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from xgboost import XGBClassifier

sys.path.insert(0, str(Path(__file__).parent.parent))
from features.fusion import FEATURE_SCHEMA, FEATURE_SCHEMA_VERSION  # noqa: E402
from training.dataset import build_feature_matrix, load_split_manifest, split_by  # noqa: E402


def train_stage1(X_train, y_train_bin, X_val, y_val_bin):
    """Trains RF and XGBoost, reports both, promotes the higher-macro-F1 one —
    the model comparison the abstract itself promises, not a default pick."""
    candidates = {
        "random_forest": RandomForestClassifier(
            n_estimators=300, max_depth=14, min_samples_leaf=2, class_weight="balanced",
            random_state=42, n_jobs=-1,
        ),
        "xgboost": XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.08, subsample=0.85,
            colsample_bytree=0.85, eval_metric="logloss", random_state=42, n_jobs=-1,
        ),
    }

    results = {}
    for name, model in candidates.items():
        model.fit(X_train, y_train_bin)
        val_pred = model.predict(X_val)
        macro_f1 = f1_score(y_val_bin, val_pred, average="macro")
        results[name] = {"model": model, "val_macro_f1": macro_f1}
        print(f"  {name}: val macro-F1 = {macro_f1:.4f}")

    winner = max(results, key=lambda k: results[k]["val_macro_f1"])
    print(f"  -> promoted: {winner}")
    return results[winner]["model"], winner, {k: v["val_macro_f1"] for k, v in results.items()}


def calibrate(model, X_cal, y_cal_bin):
    # cv="prefit" was removed in newer sklearn — FrozenEstimator is the
    # replacement for "calibrate this already-fitted model, don't refit it".
    calibrated = CalibratedClassifierCV(FrozenEstimator(model), method="isotonic")
    calibrated.fit(X_cal, y_cal_bin)
    return calibrated


def evaluate_stage1(model, X_test, y_test_bin):
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = {
        "accuracy": accuracy_score(y_test_bin, pred),
        "precision": precision_score(y_test_bin, pred, zero_division=0),
        "recall": recall_score(y_test_bin, pred, zero_division=0),
        "f1": f1_score(y_test_bin, pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test_bin, proba) if len(set(y_test_bin)) > 1 else None,
        "pr_auc": average_precision_score(y_test_bin, proba) if len(set(y_test_bin)) > 1 else None,
        "brier_score": brier_score_loss(y_test_bin, proba),
        "confusion_matrix": confusion_matrix(y_test_bin, pred).tolist(),
        "n_test": int(len(y_test_bin)),
    }
    return metrics


def train_stage2(X_train, cat_train, X_val, cat_val, min_per_category=15):
    """Category classifier trained on category_hint — explicitly preliminary,
    see module docstring. Categories below `min_per_category` in the training
    split are reported as under-powered rather than silently included
    (blueprint §13.1's own instruction for rare-category honesty)."""
    from collections import Counter

    counts = Counter(c for c in cat_train if c)
    usable_categories = {c for c, n in counts.items() if n >= min_per_category}
    mask_train = np.array([c in usable_categories for c in cat_train])
    mask_val = np.array([c in usable_categories for c in cat_val])

    if mask_train.sum() < 20 or len(usable_categories) < 2:
        print("  Not enough labeled+usable categories yet for a Stage 2 fit — skipped.")
        return None, {"skipped": True, "category_counts": dict(counts)}

    model = RandomForestClassifier(
        n_estimators=300, max_depth=14, min_samples_leaf=2, class_weight="balanced",
        random_state=42, n_jobs=-1,
    )
    model.fit(X_train[mask_train], cat_train[mask_train])

    val_report = {}
    if mask_val.sum() > 0:
        val_pred = model.predict(X_val[mask_val])
        val_report["macro_f1"] = f1_score(cat_val[mask_val], val_pred, average="macro", zero_division=0)

    under_powered = {c: n for c, n in counts.items() if 0 < n < min_per_category}
    return model, {
        "skipped": False,
        "categories_used": sorted(usable_categories),
        "under_powered_categories": under_powered,
        "category_counts": dict(counts),
        "val_macro_f1": val_report.get("macro_f1"),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True, help="manifest_with_splits.csv")
    p.add_argument("--images-base-dir", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--skip-cv", action="store_true", help="skip QR/CV features (faster smoke test)")
    args = p.parse_args()

    print("Loading manifest and building features...")
    rows = load_split_manifest(args.manifest)
    X, y_label, y_category, groups, splits, feature_names = build_feature_matrix(
        rows, args.images_base_dir, run_cv=not args.skip_cv
    )
    y_bin = (y_label == "fraudulent").astype(int)

    X_train, y_train_label, cat_train = split_by(X, y_label, y_category, splits, "train")
    X_val, y_val_label, cat_val = split_by(X, y_label, y_category, splits, "val")
    X_cal, y_cal_label, _ = split_by(X, y_label, y_category, splits, "calibration")
    X_test, y_test_label, _ = split_by(X, y_label, y_category, splits, "test")

    y_train_bin = (y_train_label == "fraudulent").astype(int)
    y_val_bin = (y_val_label == "fraudulent").astype(int)
    y_cal_bin = (y_cal_label == "fraudulent").astype(int)
    y_test_bin = (y_test_label == "fraudulent").astype(int)

    print(f"\nSplit sizes: train={len(X_train)} val={len(X_val)} calibration={len(X_cal)} test={len(X_test)}")

    print("\n=== Stage 1: binary classifier ===")
    stage1_model, stage1_winner, stage1_comparison = train_stage1(X_train, y_train_bin, X_val, y_val_bin)

    print("\nCalibrating on the calibration split...")
    stage1_calibrated = calibrate(stage1_model, X_cal, y_cal_bin)

    print("Evaluating on the held-out test split...")
    stage1_metrics = evaluate_stage1(stage1_calibrated, X_test, y_test_bin)
    print(json.dumps({k: v for k, v in stage1_metrics.items() if k != "confusion_matrix"}, indent=2))
    print("confusion_matrix [[TN,FP],[FN,TP]]:", stage1_metrics["confusion_matrix"])

    print("\n=== Stage 2: category classifier (preliminary — see docstring) ===")
    stage2_model, stage2_report = train_stage2(X_train, cat_train, X_val, cat_val)
    print(json.dumps(stage2_report, indent=2))

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(stage1_calibrated, out_dir / "stage1_model.joblib")
    # SHAP's TreeExplainer needs the raw tree model directly, not the
    # CalibratedClassifierCV wrapper — calibration only rescales the final
    # probability monotonically, so explaining against the pre-calibration
    # model is standard practice and avoids unwrapping FrozenEstimator internals.
    joblib.dump(stage1_model, out_dir / "stage1_model_raw.joblib")
    if stage2_model is not None:
        joblib.dump(stage2_model, out_dir / "stage2_model.joblib")

    metadata = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_names": feature_names,
        "stage1_algorithm": stage1_winner,
        "stage1_model_comparison_val_macro_f1": stage1_comparison,
        "stage1_test_metrics": stage1_metrics,
        "stage2_report": stage2_report,
        "dataset_manifest": str(args.manifest),
        "n_total_samples": int(len(rows)),
        "known_limitations": [
            "All images are synthetically rendered from real text — no real-screenshot test subset exists yet (blueprint §18.3 R10 not fully mitigated).",
            "Stage 2 category labels are unverified source hints, not annotated ground truth.",
            "Text features trained on ground-truth text, not actual OCR output — real OCR noise is a serving-time gap not reflected in these test metrics.",
        ],
    }
    with open(out_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSaved model bundle to {out_dir}")


if __name__ == "__main__":
    main()
