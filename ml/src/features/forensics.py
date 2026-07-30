"""A small, honest screenshot-authenticity check.

Full forgery detection (Error Level Analysis, per-word font-consistency,
compression-artifact mapping) needs real image-forensics work this pass
explicitly scoped out of — see memory/project_ml_pipeline_status.md. What's
here is much narrower: EXIF metadata inspection via Pillow. Missing EXIF on
a format that normally carries it, or an editor-software tag (Photoshop,
GIMP, etc.), is a real, cheap, honest signal — but a weak one. Plenty of
legitimate screenshots have no EXIF at all (most phone screenshot tools
strip it), so this is surfaced as a low-confidence hint, never as "forgery
detected."
"""

from PIL import Image
from PIL.ExifTags import TAGS

EDITOR_SOFTWARE_MARKERS = (
    "photoshop", "gimp", "affinity photo", "paint.net", "pixelmator",
    "canva", "picsart",
)


def check_exif_anomaly(image_path: str) -> dict:
    """Returns {possible_editing_signal, reason} — reason is None when no
    signal is found. Never raises: a read failure just means no signal,
    matching the pipeline-wide degradation policy (blueprint §5.3 rule 2).

    Deliberately does NOT flag missing EXIF on its own. This product analyzes
    messaging-app screenshots, not camera photos — and screenshot-capture
    tools essentially never embed camera EXIF, real or faked, so "no EXIF"
    would fire on nearly every legitimate upload (confirmed by testing
    against this project's own synthetic screenshots, which correctly have
    none). The only signal kept is an explicit editor-software tag, which
    means the file really was opened in an image editor — that's true
    regardless of whether the source was a photo or a screenshot."""
    try:
        with Image.open(image_path) as img:
            exif = img.getexif()
    except Exception:
        return {"possible_editing_signal": False, "reason": None}

    if not exif:
        return {"possible_editing_signal": False, "reason": None}

    software = None
    for tag_id, value in exif.items():
        if TAGS.get(tag_id) == "Software":
            software = str(value)
            break

    if software and any(marker in software.lower() for marker in EDITOR_SOFTWARE_MARKERS):
        return {
            "possible_editing_signal": True,
            "reason": f'Image metadata lists editing software: "{software}"',
        }

    return {"possible_editing_signal": False, "reason": None}
