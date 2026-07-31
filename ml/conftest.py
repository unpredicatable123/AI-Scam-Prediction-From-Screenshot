import sys
from pathlib import Path

# Mirrors generate.py's own sys.path setup, so tests can do
# `from features.text_features import ...` without installing the package.
sys.path.insert(0, str(Path(__file__).parent / "src"))
