"""Renders SourceRow objects into chat/email screenshot PNGs via a headless
Chromium (Playwright), using the chat.html.jinja template.

HTML/CSS + a real browser engine was chosen over drawing pixels directly
(e.g. with Pillow) because the downstream OCR/CV pipeline will encounter
*real* app screenshots — box-model layout and real font rendering get much
closer to that than manually positioned rectangles, and it's far less
per-platform code to maintain.
"""

import io
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image
from playwright.sync_api import sync_playwright

from .ingest import SourceRow
from .qr import extract_or_synthesize_payload, qr_data_uri
from .variation import build_variation

_SENDER_RE = re.compile(r"^\s*(?:\"?([^\"<]*?)\"?\s*)?<?([\w.+-]+@[\w.-]+)>?\s*$")
_EMBEDDED_SUBJECT_RE = re.compile(r"^\s*Subject:\s*(.+?)\s*\n+", re.IGNORECASE)

TEMPLATES_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "jinja"]),
)
_template = _env.get_template("chat.html.jinja")


def _split_embedded_subject(text: str):
    """Some corpora embed 'Subject: X' as the first line of the body itself
    rather than a separate column. Pull it out so it isn't both mis-derived
    into a duplicate/garbled header AND left sitting in the body."""
    m = _EMBEDDED_SUBJECT_RE.match(text)
    if m:
        return m.group(1).strip(), text[m.end():].lstrip()
    return None, text


def _derive_email_subject(row: SourceRow, body_text: str) -> str:
    if row.subject:
        return row.subject.strip()
    words = body_text.split()
    snippet = " ".join(words[:9])
    return snippet[:70] + ("…" if len(snippet) < len(body_text) else "")


def _parse_sender(sender: str):
    """'Name <a@b.com>' -> ('Name', 'a@b.com'); bare emails/names handled loosely."""
    m = _SENDER_RE.match(sender)
    if not m:
        return None, None
    name, email = m.group(1), m.group(2)
    return (name.strip() if name else None), email


def build_render_context(row: SourceRow, source_type: str, rng_for_qr, qr_image_pool=None):
    forced_platform = "email" if source_type == "email" else None
    embed_qr = source_type == "qr"

    ctx = build_variation(row.row_id, forced_platform=forced_platform, embed_qr=embed_qr)

    embedded_subject, body_text = _split_embedded_subject(row.text)
    if ctx["platform"] == "email":
        ctx["message_text"] = body_text
        ctx["email_subject"] = row.subject.strip() if row.subject else (embedded_subject or _derive_email_subject(row, body_text))
    else:
        # Chat bubbles never show a subject line, embedded or otherwise.
        ctx["message_text"] = body_text
        ctx["email_subject"] = None

    # Real metadata beats faked metadata whenever the source dataset has it.
    if ctx["platform"] == "email" and row.sender:
        name, email = _parse_sender(row.sender)
        if email:
            ctx["contact_email"] = email
            ctx["contact_name"] = name or email.split("@")[0]
            ctx["avatar_label"] = (ctx["contact_name"] or email)[0].upper()

    if embed_qr:
        if qr_image_pool is not None:
            ctx["qr_data_uri"] = qr_image_pool.random_data_uri(rng_for_qr)
            ctx["qr_payload"] = ""
            ctx["qr_source"] = "real"
        else:
            payload = extract_or_synthesize_payload(row.text, rng_for_qr)
            ctx["qr_data_uri"] = qr_data_uri(payload)
            ctx["qr_payload"] = payload
            ctx["qr_source"] = "synthetic"
    else:
        ctx["qr_data_uri"] = None
        ctx["qr_payload"] = None
        ctx["qr_source"] = None

    return ctx


_BROWSER_ARGS = ["--font-render-hinting=none", "--disable-lcd-text", "--disable-font-subpixel-positioning"]
_RECYCLE_EVERY = 40


class ScreenshotRenderer:
    """Owns a browser instance, recycled periodically across the batch.

    Two real, distinct failures showed up in testing at real scale:
    1. A single long-lived *page* taking hundreds of consecutive full-page
       screenshots hit "Protocol error (Page.captureScreenshot): Unable to
       capture screenshot" at sample 531 of one run.
    2. Recycling only the page wasn't enough — a second run got to sample
       563 before the retry's own `new_page()` call failed with
       "Target page, context or browser has been closed": the whole
       *browser process* (not just the page) had become unstable and died,
       a known resource-leak pattern in long-running headless Chromium
       (Windows GDI handles are a common culprit).
    The fix operates at the layer that actually failed: the entire
    browser (pw + browser + context + page) is torn down and relaunched
    every _RECYCLE_EVERY captures, plus once more as a retry if a capture
    fails outright before then.
    """

    def __enter__(self):
        self._capture_count = 0
        self._launch()
        return self

    def __exit__(self, *exc):
        self._teardown()

    def _launch(self):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(args=_BROWSER_ARGS)
        # device_scale_factor=2 (not 3): still solidly high-DPI (matches most
        # non-flagship Android phones) and the LCD-text-disable flags above
        # are what actually eliminate subpixel fringing, not the scale factor
        # — but a 3x buffer on a memory-constrained machine (this one runs at
        # ~4GB free of 16GB even at idle) was the real cause of repeated,
        # non-deterministic "Unable to capture screenshot" crashes at real
        # batch scale. 2x roughly halves the screenshot buffer memory.
        self._context = self._browser.new_context(device_scale_factor=2)
        self._page = self._context.new_page()

    def _teardown(self):
        try:
            self._page.close()
            self._context.close()
            self._browser.close()
            self._pw.stop()
        except Exception:
            pass  # already dead — that's exactly why we're tearing down

    def _recycle(self):
        self._teardown()
        self._launch()
        self._capture_count = 0

    def capture(self, html: str, device_width: int) -> bytes:
        if self._capture_count >= _RECYCLE_EVERY:
            self._recycle()

        def _try_capture():
            self._page.set_viewport_size({"width": device_width, "height": 800})
            self._page.set_content(html, wait_until="load")
            body_height = self._page.evaluate("document.body.scrollHeight")
            # Capped well below Chromium's screenshot buffer limit — real
            # chat/email content essentially never needs this much height
            # anyway, and every pixel here is a further multiplier on the
            # memory pressure that was causing capture failures at real
            # batch scale on this machine.
            self._page.set_viewport_size(
                {"width": device_width, "height": min(max(body_height, 640), 1600)}
            )
            return self._page.screenshot(full_page=True)

        try:
            result = _try_capture()
        except Exception:
            # Full browser recycle on retry, not just a new page — a page
            # crash can mean the whole browser process is already gone.
            self._recycle()
            result = _try_capture()

        self._capture_count += 1
        return result


def render_row(renderer: ScreenshotRenderer, row: SourceRow, source_type: str, rng_for_qr, qr_image_pool=None):
    ctx = build_render_context(row, source_type, rng_for_qr, qr_image_pool=qr_image_pool)
    html = _template.render(**ctx)
    png_bytes = renderer.capture(html, ctx["device_width"])

    final_bytes = png_bytes
    final_ext = "png"
    if ctx["compression_quality"] is not None:
        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=ctx["compression_quality"])
        final_bytes = buf.getvalue()
        final_ext = "jpg"

    return final_bytes, final_ext, ctx
