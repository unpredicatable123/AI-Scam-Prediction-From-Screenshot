"""Thin entrypoint so this can be run as `python generate.py ...` from the
ml/ directory without needing to know Python's package/module machinery."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from generator.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
