# Synthetic screenshot generator

Converts raw text/CSV scam, phishing, QR, and email-scam datasets into
rendered chat/email screenshots (WhatsApp/Telegram/SMS/Instagram/Email-style)
for OCR/NLP/CV training. See `docs/BLUEPRINT.md` §5, §12, §18.3, and §19 for
the design rationale, and `memory/project_blueprint_decisions.md` for why
this exists (the actual datasets are text, not screenshots).

## Setup

```sh
pip install -r requirements.txt
python -m playwright install chromium
```

## Usage

Drop your CSV(s) into `data/raw/`, then:

```sh
python generate.py --input data/raw/your_scam_dataset.csv --source-type scam --output-dir data/generated
python generate.py --input data/raw/your_qr_dataset.csv --source-type qr --output-dir data/generated
python generate.py --input data/raw/your_email_dataset.csv --source-type email --output-dir data/generated
```

`--source-type`:
- `scam` / `phishing` — rendered onto a random chat platform (WhatsApp/Telegram/SMS/Instagram).
- `qr` — same, plus a real generated QR code embedded in the message (payload is extracted from the text if a URL/UPI handle is present, otherwise synthesized).
- `email` — forced onto the email-client layout.

The text-column and label-column names are auto-detected from common headers
(`text`/`message`/`body`/`content`, `label`/`class`/`is_scam`, ...). Override
with `--text-col` / `--label-col` / `--category-col` if your CSV uses
something else. Rows are all labeled `fraudulent` by default (`--default-label
genuine` for a legitimate-message dataset — **the pipeline currently has no
genuine/legitimate source**, which is a real gap: the Stage-1 binary
classifier needs negative examples too).

Output: `data/generated/images/*.png` (or `.jpg` for samples that simulate
forwarded-message recompression) plus `data/generated/manifest.csv`, one row
per sample with fields mirroring the `datasetSamples` Firestore schema in
`docs/BLUEPRINT.md` §7.2 — `group_key` is the source row's stable ID, so any
train/val/test split done later must keep everything sharing a `group_key`
in the same split (leakage protection, §18.3 R10).

Every random choice (contact name, avatar colour, theme, device width,
forwarded/unknown-number/business flags, bubble-colour jitter) is seeded per
source row, so reruns are reproducible.

## Running tests

```sh
pip install -r requirements-dev.txt
pytest
```

Covers the pure feature-extraction functions in `src/features/` (lexicon
matching, brand-typosquat detection, conversation-flow escalation analysis,
the EXIF forensics signal, and the fusion/schema contract). These aren't
placeholder tests — several lock in real bugs found by hand-testing earlier
in the project (e.g. "now" matching inside "know", "axis" false-positiving
on "basis", missing-EXIF false-positiving on every screenshot). No tests
yet for `cv_features.py`'s QR decoding, the generator/render pipeline, or
`apps/ai-service/` — those need real image fixtures or a running OCR/model
stack and are a reasonable next step, not covered here.

## What this does *not* do yet

- No genuine/legitimate-message dataset — only fraudulent-labeled sources exist so far.
- No annotation workbench — `category_hint` is a guess (from the source file or `--source-type`), not the verified 7-class taxonomy label.
- No dataset splitting — that's a separate step, and must be group-aware (see above).
