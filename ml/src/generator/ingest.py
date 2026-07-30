"""Loads raw scam/phishing/QR/email text datasets into a normalized row format.

The user's actual CSV schemas aren't known in advance, so column detection is
heuristic (common header names) with an explicit override available via CLI
flags. Category is deliberately kept as a *hint*, not ground truth — assigning
the real 7-class taxonomy is the annotation workbench's job (blueprint AD-01),
not something this script should silently fabricate.
"""

import csv
import hashlib
import random
import sys
from dataclasses import dataclass, field

# Some real corpora (Nazario, etc.) have email bodies well past Python's
# default 131072-byte csv field limit. Raise it as high as the platform allows.
_limit = sys.maxsize
while True:
    try:
        csv.field_size_limit(_limit)
        break
    except OverflowError:
        _limit = int(_limit / 10)

TEXT_COLUMN_CANDIDATES = ["text", "message", "body", "content", "email_text", "sms", "email", "v2", "text_combined"]
LABEL_COLUMN_CANDIDATES = ["label", "class", "is_scam", "target", "fraudulent", "v1"]
CATEGORY_COLUMN_CANDIDATES = ["category", "scam_category", "type", "subcategory", "phishing_type"]
SENDER_COLUMN_CANDIDATES = ["sender", "from", "from_email"]
SUBJECT_COLUMN_CANDIDATES = ["subject", "email_subject"]

FRAUDULENT_TRUE_VALUES = {"1", "true", "scam", "spam", "phishing", "fraud", "fraudulent", "yes"}
GENUINE_VALUES = {"0", "false", "ham", "genuine", "legit", "legitimate", "no", "not_spam"}

# Real email corpora can run to tens of KB per body. A screenshot only ever
# shows what fits on a screen, so anything past this is cut — this also
# prevents Chromium's full-page screenshot from failing on absurdly tall pages.
MAX_TEXT_CHARS = 1800


@dataclass
class SourceRow:
    row_id: str
    text: str
    label: str  # "fraudulent" | "genuine"
    category_hint: str | None
    group_key: str
    sender: str | None = None
    subject: str | None = None
    extra: dict = field(default_factory=dict)


def _find_column(fieldnames, candidates, override=None):
    if override:
        return override
    lower_map = {f.lower().strip(): f for f in fieldnames}
    for c in candidates:
        if c in lower_map:
            return lower_map[c]
    return None


def _normalize_label(raw, default_label):
    if raw is None or str(raw).strip() == "":
        return default_label
    v = str(raw).strip().lower()
    if v in FRAUDULENT_TRUE_VALUES:
        return "fraudulent"
    if v in GENUINE_VALUES:
        return "genuine"
    return default_label


def _stable_id(source_name, index, text):
    h = hashlib.sha1(f"{source_name}:{index}:{text}".encode("utf-8")).hexdigest()[:12]
    return f"{source_name}_{index}_{h}"


def load_dataset(
    path,
    source_name,
    default_label="fraudulent",
    text_col=None,
    text_cols=None,
    label_col=None,
    category_col=None,
    limit=None,
    label_filter=None,
    sample=None,
    sample_seed=42,
):
    """Reads a CSV into a list of SourceRow.

    text_cols (list[str] | None): if given, these columns are concatenated
    (in order, skipping blanks) instead of relying on single-column
    auto-detection — needed for datasets like job postings where the message
    is split across title/description/requirements/etc.

    label_filter ("genuine" | "fraudulent" | None): keep only rows with this
    normalized label. Several real corpora here turned out to be sorted or
    clustered by label (verified by sampling early/mid/late rows) — `limit`
    alone would silently produce a badly skewed batch on those files, so
    label-aware sampling is a separate, deliberate step.

    sample (int | None): after filtering, randomly sample this many rows
    (seeded, reproducible) instead of taking them in file order.
    """
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        resolved_text_col = None
        if not text_cols:
            resolved_text_col = _find_column(fieldnames, TEXT_COLUMN_CANDIDATES, text_col)
            if not resolved_text_col:
                raise ValueError(
                    f"Could not find a text column in {path}. "
                    f"Columns present: {fieldnames}. Pass --text-col or --text-cols explicitly."
                )
        resolved_label_col = _find_column(fieldnames, LABEL_COLUMN_CANDIDATES, label_col)
        resolved_category_col = _find_column(fieldnames, CATEGORY_COLUMN_CANDIDATES, category_col)
        resolved_sender_col = _find_column(fieldnames, SENDER_COLUMN_CANDIDATES)
        resolved_subject_col = _find_column(fieldnames, SUBJECT_COLUMN_CANDIDATES)

        rows = []
        for i, raw_row in enumerate(reader):
            if limit is not None and i >= limit:
                break

            if text_cols:
                parts = [(raw_row.get(c) or "").strip() for c in text_cols]
                text = "\n\n".join(p for p in parts if p)
            else:
                text = (raw_row.get(resolved_text_col) or "").strip()
            if not text:
                continue
            if len(text) > MAX_TEXT_CHARS:
                text = text[:MAX_TEXT_CHARS].rsplit(" ", 1)[0] + "…"

            label = _normalize_label(
                raw_row.get(resolved_label_col) if resolved_label_col else None, default_label
            )
            if label_filter is not None and label != label_filter:
                continue
            category_hint = (
                raw_row.get(resolved_category_col, "").strip() or None
                if resolved_category_col
                else None
            )
            sender = (raw_row.get(resolved_sender_col, "").strip() or None) if resolved_sender_col else None
            subject = (raw_row.get(resolved_subject_col, "").strip() or None) if resolved_subject_col else None

            rows.append(
                SourceRow(
                    row_id=_stable_id(source_name, i, text),
                    text=text,
                    label=label,
                    category_hint=category_hint,
                    group_key=_stable_id(source_name, i, text),  # one render family per source row
                    sender=sender,
                    subject=subject,
                    extra=raw_row,
                )
            )

    if sample is not None and sample < len(rows):
        rows = random.Random(sample_seed).sample(rows, sample)
    return rows
