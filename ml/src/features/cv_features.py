"""Visual/QR feature extraction (blueprint docs/BLUEPRINT.md §12).

QR payloads are decoded but never fetched — same "no network access on
extracted content" rule as the URL features in text_features.py.
"""

import re
from urllib.parse import parse_qs, urlparse

import contextlib
import os

import cv2
import numpy as np
from pyzbar.pyzbar import decode as zbar_decode

from .forensics import check_exif_anomaly


@contextlib.contextmanager
def _suppress_native_stderr():
    """zbar's C decoder prints harmless internal assertion warnings to the
    raw OS stderr fd when probing symbologies (e.g. Databar) that don't match
    a given QR code — cosmetic noise, not an error, but not something Python
    exception handling can silence since it bypasses sys.stderr entirely."""
    try:
        fd = os.dup(2)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 2)
    except Exception:
        yield
        return
    try:
        yield
    finally:
        os.dup2(fd, 2)
        os.close(fd)
        os.close(devnull)

FEATURE_NAMES = [
    "qr_detected", "qr_count", "qr_is_payment_intent", "qr_has_prefilled_amount",
    "qr_is_url", "qr_is_url_risky",
]


def _decode_qr_codes(image_bgr):
    """Detection cascade per blueprint §12.2: pyzbar first (fast, multi-symbology),
    OpenCV's QRCodeDetector as a fallback for codes pyzbar misses."""
    payloads = []
    try:
        with _suppress_native_stderr():
            decoded = zbar_decode(image_bgr)
        for obj in decoded:
            try:
                payloads.append(obj.data.decode("utf-8", errors="replace"))
            except Exception:
                pass
    except Exception:
        pass

    if not payloads:
        try:
            detector = cv2.QRCodeDetector()
            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            ok, decoded_info, _, _ = detector.detectAndDecodeMulti(gray)
            if ok:
                payloads.extend([d for d in decoded_info if d])
        except Exception:
            pass

    return payloads


_URL_IN_PAYLOAD_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_UPI_IN_PAYLOAD_RE = re.compile(r"upi://\S+", re.IGNORECASE)


def _clean_payload(payload: str) -> str:
    """Extracts the actual URI from a decoded QR payload, tolerating junk
    before/after it. Found necessary because this project's own
    `data/raw/benign/` real-QR corpus turned out to encode a stringified
    pandas Series repr instead of a clean URL (e.g. "0    https://...\\n
    Name: url, dtype: object") — a data-generation bug upstream of this
    code, not something worth re-rendering 5,992 images to fix when the
    real value is trivially recoverable from the payload itself. A no-op
    for an already-clean payload: the match starts at position 0 and
    `\\S+` runs to the same end the whole string would have anyway."""
    m = _URL_IN_PAYLOAD_RE.search(payload) or _UPI_IN_PAYLOAD_RE.search(payload)
    return m.group(0) if m else payload


def _classify_payload(payload):
    is_url = bool(re.match(r"^https?://", payload, re.IGNORECASE))
    is_payment_intent = payload.lower().startswith("upi://")
    has_prefilled_amount = False
    if is_payment_intent:
        try:
            query = parse_qs(urlparse(payload).query)
            amt = query.get("am", [""])[0]
            has_prefilled_amount = bool(amt) and float(amt) > 0
        except Exception:
            pass
    return is_url, is_payment_intent, has_prefilled_amount


def extract_cv_features(image_path: str) -> dict:
    """Pure function: image path -> named CV feature dict. Never raises —
    a decode failure degrades to an all-zero feature vector plus a flag,
    matching the pipeline-wide degradation policy (blueprint §5.3 rule 2)."""
    # Computed unconditionally, independent of whether a QR code is found —
    # merged into whichever dict this function returns below.
    forensics = check_exif_anomaly(image_path)

    try:
        image_bgr = cv2.imread(image_path)
        if image_bgr is None:
            return _empty_features(forensics)
        payloads = _decode_qr_codes(image_bgr)
    except Exception:
        return _empty_features(forensics)

    if not payloads:
        return _empty_features(forensics)

    payloads = [_clean_payload(p) for p in payloads]

    classified = [_classify_payload(p) for p in payloads]
    is_url_any = any(c[0] for c in classified)
    is_payment_any = any(c[1] for c in classified)
    has_amount_any = any(c[2] for c in classified)
    url_risky = False
    if is_url_any:
        from .text_features import _url_risk_score

        url_risky = any(_url_risk_score(p) > 0.3 for p, c in zip(payloads, classified) if c[0])

    return {
        "qr_detected": 1,
        "qr_count": len(payloads),
        "qr_is_payment_intent": int(is_payment_any),
        "qr_has_prefilled_amount": int(has_amount_any),
        "qr_is_url": int(is_url_any),
        "qr_is_url_risky": int(url_risky),
        # Not model features (deliberately absent from FEATURE_NAMES, so
        # fuse_features's schema-driven copy loop ignores them) — display-only,
        # read directly off this dict by the API layer. qr_payload_preview is
        # the first payload only; if multiple codes are present this previews
        # just one of them.
        "qr_payload_preview": payloads[0][:80],
        "possible_editing_signal": int(forensics["possible_editing_signal"]),
        "editing_signal_reason": forensics["reason"],
    }


def _empty_features(forensics=None):
    features = {name: 0 for name in FEATURE_NAMES}
    if forensics:
        features["possible_editing_signal"] = int(forensics["possible_editing_signal"])
        features["editing_signal_reason"] = forensics["reason"]
    return features


CV_FEATURE_DESCRIPTIONS = {
    "qr_detected": "Contains a QR code",
    "qr_is_payment_intent": "The QR code is a payment request, not just a link",
    "qr_has_prefilled_amount": "The QR code has a pre-filled payment amount",
    "qr_is_url_risky": "The QR code links to a suspicious-looking URL",
}
