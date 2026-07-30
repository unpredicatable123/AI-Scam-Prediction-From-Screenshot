"""FastAPI microservice — the Python AI service from blueprint §4/§8.4.

Scope note: this is a local-first build of the pipeline actually implemented
so far (OCR + interpretable NLP features + QR/CV features + Stage-1 binary
classifier + SHAP explanation + risk score + recommendations). It does not
yet include Firestore/Storage integration, auth, or the full blueprint
feature set (brand/logo matching, layout detector, Stage-2 taxonomy is
preliminary) — those remain explicitly out of scope pending the
infrastructure decisions noted in memory/project_infra_open_questions.md.
"""

import os
import shutil
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .pipeline import Pipeline

MODEL_DIR = os.environ.get("MODEL_DIR", "D:/ai-scam-detection-data/model_v1")
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

pipeline_holder = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not Path(MODEL_DIR).exists():
        raise RuntimeError(
            f"Model directory not found: {MODEL_DIR}. Train a model first (ml/src/training/train.py) "
            "or set the MODEL_DIR environment variable."
        )
    pipeline_holder["pipeline"] = Pipeline(MODEL_DIR)
    yield
    pipeline_holder.clear()


app = FastAPI(title="Scam Detection AI Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.get("/v1/health")
def health():
    return {"status": "ok"}


@app.get("/v1/ready")
def ready():
    if "pipeline" not in pipeline_holder:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ready"}


@app.get("/v1/model/info")
def model_info():
    pipeline = pipeline_holder.get("pipeline")
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {
        "modelVersion": pipeline.model_version,
        "featureSchemaVersion": pipeline.feature_schema_version,
        "metadata": pipeline.metadata,
    }


@app.post("/v1/predict")
async def predict(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported content type: {file.content_type}")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
    if len(contents) == 0:
        raise HTTPException(status_code=422, detail="Empty file")

    pipeline = pipeline_holder.get("pipeline")
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    suffix = Path(file.filename or "upload.png").suffix or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = pipeline.predict(tmp_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return result
