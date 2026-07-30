"""Per-sample randomization: contact identity, theme, device size, layout
signals, and colour jitter.

Wide randomisation here is the leakage mitigation from
docs/BLUEPRINT.md §18.3 (R10) — if every sample rendered the same fixed
palette/name/layout, the model could learn "bubble colour == platform"
instead of the actual text/visual signal. Seeded per source row so reruns
are reproducible without needing to persist every random choice.
"""

import random

from faker import Faker

PLATFORMS = ["whatsapp", "telegram", "sms", "instagram", "email"]
DEVICE_WIDTHS = [360, 390, 412, 430]

# Base hue (degrees) per platform for the "outgoing bubble" family — jittered
# per sample so the model can't shortcut on one exact fixed colour.
PLATFORM_BASE_HUE = {
    "whatsapp": 142,
    "telegram": 205,
    "sms": 210,
    "instagram": 320,
    "email": 255,
}

GENERIC_REPLIES = [
    "Who is this?",
    "Is this real?",
    "Ok",
    "I don't understand",
    "Can you call me instead?",
]

_faker = Faker()


def build_variation(row_id: str, forced_platform: str | None = None, embed_qr: bool = False):
    rng = random.Random(row_id)
    Faker.seed(rng.randint(0, 2**31))

    platform = forced_platform or rng.choice(PLATFORMS)
    theme = rng.choice(["light", "dark"])
    device_width = rng.choice(DEVICE_WIDTHS)

    is_unknown_number = platform != "email" and rng.random() < 0.35
    contact_name = None if is_unknown_number else _faker.name()
    contact_phone = _faker.phone_number() if platform != "email" else None
    contact_email = _faker.email() if platform == "email" else None
    avatar_label = (contact_name or contact_phone or "?").strip()[0].upper()

    is_forwarded = platform != "email" and rng.random() < 0.25
    is_business = rng.random() < 0.15
    avatar_hue = (PLATFORM_BASE_HUE[platform] + rng.randint(-20, 20)) % 360
    bubble_hue = (PLATFORM_BASE_HUE[platform] + rng.randint(-15, 15)) % 360

    has_reply = platform != "email" and rng.random() < 0.3
    reply_text = rng.choice(GENERIC_REPLIES) if has_reply else None

    hour = rng.randint(0, 23)
    minute = rng.randint(0, 59)
    timestamp = f"{hour:02d}:{minute:02d}"

    # Fresh screenshots stay lossless; forwarded ones simulate recompression
    # generations (blueprint §12.5 provenance signal).
    compression_quality = None if not is_forwarded else rng.randint(55, 90)

    return {
        "platform": platform,
        "theme": theme,
        "device_width": device_width,
        "contact_name": contact_name,
        "contact_phone": contact_phone,
        "contact_email": contact_email,
        "avatar_label": avatar_label,
        "avatar_hue": avatar_hue,
        "bubble_hue": bubble_hue,
        "is_unknown_number": is_unknown_number,
        "is_forwarded": is_forwarded,
        "is_business": is_business,
        "has_reply": has_reply,
        "reply_text": reply_text,
        "timestamp": timestamp,
        "compression_quality": compression_quality,
        "embed_qr": embed_qr,
    }
