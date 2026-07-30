"""OCR extraction via Tesseract (blueprint §10).

Real per-token confidence is aggregated to a whole-image score and used as
both a feature and a gate — below MIN_CONFIDENCE the pipeline returns
`insufficient_evidence` rather than guessing on a verdict built from garbled
text (blueprint §10.4 / §5.2[2]).
"""

import pytesseract

TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    "tesseract",  # falls back to PATH on non-Windows / if already configured
]

for path in TESSERACT_PATHS:
    try:
        pytesseract.pytesseract.tesseract_cmd = path
        pytesseract.get_tesseract_version()
        break
    except Exception:
        continue

MIN_AGGREGATE_CONFIDENCE = 35.0


def run_ocr(image_path: str) -> dict:
    """Returns {text, confidence, insufficient}. Never raises — an OCR
    failure degrades to empty text + zero confidence, matching the
    pipeline-wide degradation policy (blueprint §5.3 rule 2)."""
    try:
        data = pytesseract.image_to_data(image_path, output_type=pytesseract.Output.DICT)
    except Exception:
        return {"text": "", "confidence": 0.0, "insufficient": True}

    words, confidences = [], []
    for text, conf in zip(data.get("text", []), data.get("conf", [])):
        text = text.strip()
        try:
            conf = float(conf)
        except (TypeError, ValueError):
            continue
        if text and conf >= 0:
            words.append(text)
            confidences.append(conf)

    full_text = " ".join(words)
    aggregate_confidence = round(sum(confidences) / len(confidences), 1) if confidences else 0.0

    return {
        "text": full_text,
        "confidence": aggregate_confidence,
        "insufficient": aggregate_confidence < MIN_AGGREGATE_CONFIDENCE or not full_text.strip(),
    }
