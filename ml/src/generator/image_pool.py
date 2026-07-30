"""Loads a directory of real images (e.g. the user's benign QR photo set) for
embedding directly into rendered screenshots, instead of always synthesizing
a fake QR code. Real pixel data where it exists beats synthesized data."""

import base64
import random
from pathlib import Path

_MIME = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}


def _file_to_data_uri(path: Path) -> str:
    ext = path.suffix.lstrip(".").lower()
    mime = _MIME.get(ext, "image/png")
    data = path.read_bytes()
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


class ImagePool:
    def __init__(self, directory):
        directory = Path(directory)
        self.paths = sorted(
            p for p in directory.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg")
        )
        if not self.paths:
            raise ValueError(f"No images found in {directory}")

    def __len__(self):
        return len(self.paths)

    def random_data_uri(self, rng: random.Random) -> str:
        path = rng.choice(self.paths)
        return _file_to_data_uri(path)
