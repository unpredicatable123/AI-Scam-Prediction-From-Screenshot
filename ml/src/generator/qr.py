"""Generates real, scannable QR code images for QR-category samples.

The user's QR-related dataset is text (payload URLs / UPI-style strings), not
QR pixel data (see memory/project_blueprint_decisions.md — A5). So instead of
expecting QR images directly, a payload is extracted from the source text
when present, or a plausible one is synthesized, and a genuine QR code is
generated to embed in the rendered screenshot.
"""

import base64
import io
import re

import qrcode

URL_RE = re.compile(r"https?://[^\s]+|www\.[^\s]+", re.IGNORECASE)
UPI_RE = re.compile(r"[\w.\-]+@[a-zA-Z]{2,}(?:pay|upi|ybl|okhdfcbank|oksbi|axl)\b", re.IGNORECASE)


def extract_or_synthesize_payload(text: str, rng) -> str:
    """Prefers a real URL/UPI handle found in the source text; falls back to
    a synthesized-but-plausible UPI payment payload so the QR is never empty."""
    url_match = URL_RE.search(text)
    if url_match:
        return url_match.group(0)
    upi_match = UPI_RE.search(text)
    if upi_match:
        amount = rng.choice([500, 999, 1500, 2000, 4999])
        return f"upi://pay?pa={upi_match.group(0)}&am={amount}&cu=INR"
    amount = rng.choice([500, 999, 1500, 2000, 4999])
    fake_vpa = f"collect{rng.randint(1000, 9999)}@ybl"
    return f"upi://pay?pa={fake_vpa}&am={amount}&cu=INR"


def qr_data_uri(payload: str, box_size: int = 6) -> str:
    img = qrcode.make(payload, box_size=box_size, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
