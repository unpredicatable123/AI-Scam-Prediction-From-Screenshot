"""Orchestrates the full request pipeline: OCR -> features -> fusion ->
predict -> explain -> respond. Mirrors blueprint §5.1's stage sequence,
scoped to what this local-first build actually implements: no NLP-embedding
branch, no logo/brand matching, no layout detector (those default to 0 —
see fusion.py's documented limitation on layout signals at real inference time).
"""

import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import joblib

ML_SRC = Path(__file__).resolve().parents[3] / "ml" / "src"
sys.path.insert(0, str(ML_SRC))

from explain.groups import EXPLANATION_ELIGIBLE_GROUPS, GROUP_LABELS  # noqa: E402
from explain.nlg import generate_reasons  # noqa: E402
from explain.recommend import recommend  # noqa: E402
from explain.risk import compute_risk_score, risk_band  # noqa: E402
from explain.shap_explainer import build_explainer, explain_row, top_groups  # noqa: E402
from features.brand_guard import detect_brand_typosquat  # noqa: E402
from features.conversation_flow import analyze_conversation_flow  # noqa: E402
from features.cv_features import extract_cv_features  # noqa: E402
from features.fusion import FEATURE_SCHEMA, fuse_features, to_vector  # noqa: E402
from features.text_features import extract_text_features  # noqa: E402

from .ocr import run_ocr


def _risk_breakdown(grouped_shap: dict) -> list:
    """Percentage breakdown of what actually drove a fraudulent prediction —
    real SHAP group contributions, not fabricated category weights. Only
    positive, explanation-eligible contributions count (the same gate
    generate_reasons uses), normalized to sum to 100 across just those."""
    positive = {g: v for g, v in grouped_shap.items() if g in EXPLANATION_ELIGIBLE_GROUPS and v > 0}
    total = sum(positive.values())
    if total <= 0:
        return []
    return [
        {"group": g, "label": GROUP_LABELS.get(g, g), "percentage": round(v / total * 100, 1)}
        for g, v in sorted(positive.items(), key=lambda kv: kv[1], reverse=True)
    ]


class Pipeline:
    """Loads the model bundle once at startup; `predict` is the only method
    called per request. Model version and feature-schema version are
    verified at load time and stamped onto every response — reproducibility
    per blueprint §5.2[21]."""

    def __init__(self, model_dir: str):
        model_dir = Path(model_dir)
        self.calibrated_model = joblib.load(model_dir / "stage1_model.joblib")
        raw_model = joblib.load(model_dir / "stage1_model_raw.joblib")
        self.explainer = build_explainer(raw_model)

        stage2_path = model_dir / "stage2_model.joblib"
        self.stage2_model = joblib.load(stage2_path) if stage2_path.exists() else None

        import json

        with open(model_dir / "metadata.json", encoding="utf-8") as f:
            self.metadata = json.load(f)
        # Derived from the actual loaded directory rather than hardcoded —
        # this was previously a fixed "v1" string regardless of which model
        # directory MODEL_DIR actually pointed at, silently wrong for anyone
        # running a different model version.
        self.model_version = model_dir.name.replace("model_", "") or "v1"
        self.feature_schema_version = self.metadata["feature_schema_version"]

    def predict(self, image_path: str) -> dict:
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        scan_started_at = datetime.now(timezone.utc)
        timings = {}
        degraded = []

        t0 = time.perf_counter()
        ocr_result = run_ocr(image_path)
        timings["ocr_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        if ocr_result["insufficient"]:
            degraded.append("ocr_insufficient_confidence")

        t0 = time.perf_counter()
        text_feat = extract_text_features(ocr_result["text"])
        timings["text_features_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        t0 = time.perf_counter()
        try:
            cv_feat = extract_cv_features(image_path)
        except Exception:
            cv_feat = None
            degraded.append("cv_branch_failed")
        timings["cv_features_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        # No standalone layout detector in this build (see module docstring)
        # — platform/forwarded/unknown-number signals default to unknown.
        meta = {"platform": "", "is_forwarded": 0, "is_unknown_number": 0, "has_reply": 0}
        fused = fuse_features(text_feat, cv_feat, meta)
        vector = to_vector(fused)

        t0 = time.perf_counter()
        proba = float(self.calibrated_model.predict_proba([vector])[0][1])
        label = "fraudulent" if proba >= 0.5 else "genuine"
        timings["inference_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        category = None
        if label == "fraudulent" and self.stage2_model is not None:
            try:
                category = str(self.stage2_model.predict([vector])[0])
            except Exception:
                pass

        t0 = time.perf_counter()
        reasons = []
        breakdown = []
        if label == "fraudulent":
            _, grouped_shap = explain_row(self.explainer, vector, FEATURE_SCHEMA)
            ranked = top_groups(grouped_shap, EXPLANATION_ELIGIBLE_GROUPS, k=len(EXPLANATION_ELIGIBLE_GROUPS))
            reasons = generate_reasons(ranked, ocr_result["text"], fused, k=5)
            breakdown = _risk_breakdown(grouped_shap)
        timings["explain_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        risk_score = compute_risk_score(proba, fused)
        band = risk_band(risk_score)
        actions = recommend(fused, band) if label == "fraudulent" else []

        # Real, independent of the ML verdict — these are factual detections
        # on the extracted text, same footing as hasUrl/hasQr below.
        brand_check = detect_brand_typosquat(ocr_result["text"])
        flow = analyze_conversation_flow(ocr_result["text"])

        return {
            "requestId": request_id,
            "modelVersion": self.model_version,
            "featureSchemaVersion": self.feature_schema_version,
            "scanTimestamp": scan_started_at.isoformat(),
            "scanDurationMs": round(sum(timings.values()), 1),
            "ocr": {"text": ocr_result["text"], "confidence": ocr_result["confidence"]},
            "entities": {
                "hasUrl": bool(fused.get("has_url")),
                "hasAmount": bool(fused.get("has_amount")),
                "hasShortenerUrl": bool(fused.get("has_shortener_url")),
                "hasIpUrl": bool(fused.get("has_ip_url")),
                "hasMixedScriptUrl": bool(fused.get("has_mixed_script_url")),
                "hasTyposquatUrl": bool(fused.get("has_typosquat_url")),
                "urlMaxRisk": fused.get("url_max_risk", 0),
                "hasQr": bool(fused.get("qr_detected")),
                "qrIsPaymentIntent": bool(fused.get("qr_is_payment_intent")),
                "qrHasPrefilledAmount": bool(fused.get("qr_has_prefilled_amount")),
                "qrIsUrl": bool(fused.get("qr_is_url")),
                "qrIsUrlRisky": bool(fused.get("qr_is_url_risky")),
                "qrPayloadPreview": (cv_feat or {}).get("qr_payload_preview"),
                "hasUpiId": bool(fused.get("has_upi_id")),
                "hasIfscCode": bool(fused.get("has_ifsc_code")),
                "hasCryptoWallet": bool(fused.get("has_crypto_wallet")),
                "brandImpersonation": brand_check if brand_check["is_impersonation"] else None,
                "possibleEditingSignal": bool((cv_feat or {}).get("possible_editing_signal")),
                "editingSignalReason": (cv_feat or {}).get("editing_signal_reason"),
                "psychology": {
                    "scarcity": bool(fused.get("has_scarcity")),
                    "greed": bool(fused.get("has_greed")),
                    "romance": bool(fused.get("has_romance")),
                    "investmentPitch": bool(fused.get("has_investment_pitch")),
                    "lotteryClaim": bool(fused.get("has_lottery_claim")),
                    "jobOfferLure": bool(fused.get("has_job_offer_lure")),
                },
            },
            "conversationFlow": {
                "risk": flow["conversation_risk"],
                "stageCount": flow["stage_count"],
                "sequence": [GROUP_LABELS.get(s, s) for s in flow["sequence"]],
            },
            "prediction": {
                "label": label,
                "confidence": round(proba * 100 if label == "fraudulent" else (1 - proba) * 100, 1),
                "category": category,
                "riskScore": risk_score,
                "riskBand": band,
            },
            "explanation": {"reasons": reasons, "riskBreakdown": breakdown},
            "recommendations": actions,
            "degraded": degraded,
            "timings": timings,
        }
