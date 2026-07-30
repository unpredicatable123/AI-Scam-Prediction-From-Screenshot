"""CLI entrypoint: reads a raw text/CSV scam dataset and writes rendered
chat/email screenshots + a manifest CSV to an output directory.

Usage (from the ml/ directory, or via the ml/generate.py wrapper):
    python generate.py --input data/samples/demo_scam_messages.csv \
        --source-type scam --output-dir data/generated --seed 42
"""

import argparse
import csv
import random
from datetime import datetime, timezone
from pathlib import Path

from .image_pool import ImagePool
from .ingest import load_dataset
from .render import ScreenshotRenderer, render_row

MANIFEST_FIELDS = [
    "sample_id",
    "source_dataset",
    "source_row_id",
    "group_key",
    "platform",
    "label",
    "category_hint",
    "image_path",
    "ocr_ground_truth",
    "theme",
    "device_width",
    "is_forwarded",
    "is_unknown_number",
    "has_reply",
    "qr_payload",
    "qr_source",
    "created_at",
]


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Render a text scam dataset into synthetic chat/email screenshots.")
    p.add_argument("--input", required=True, help="Path to the source CSV")
    p.add_argument(
        "--source-type",
        required=True,
        choices=["scam", "qr", "phishing", "email"],
        help="scam/phishing -> random chat platform. qr -> random chat platform + embedded QR. email -> forced email layout.",
    )
    p.add_argument("--output-dir", required=True, help="Directory to write images + manifest.csv into")
    p.add_argument("--default-label", default="fraudulent", choices=["fraudulent", "genuine"])
    p.add_argument("--text-col", default=None, help="Override auto-detected text column name")
    p.add_argument(
        "--text-cols",
        default=None,
        help="Comma-separated list of columns to concatenate into the message text "
        "(e.g. 'title,description,requirements' for job-posting datasets). Overrides --text-col.",
    )
    p.add_argument("--label-col", default=None, help="Override auto-detected label column name")
    p.add_argument("--category-col", default=None, help="Override auto-detected category column name")
    p.add_argument(
        "--qr-image-dir",
        default=None,
        help="Directory of real QR images to embed instead of synthesizing one (only used with --source-type qr)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only scan the first N raw rows (for quick smoke tests only — several source files "
        "are label-sorted, so this is NOT a safe way to sample a balanced batch; use --sample instead)",
    )
    p.add_argument(
        "--label-filter",
        choices=["genuine", "fraudulent"],
        default=None,
        help="Keep only rows with this label before sampling",
    )
    p.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Randomly sample this many rows (after --label-filter), instead of taking file order",
    )
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    text_cols = [c.strip() for c in args.text_cols.split(",")] if args.text_cols else None

    source_name = input_path.stem
    rows = load_dataset(
        input_path,
        source_name=source_name,
        default_label=args.default_label,
        text_col=args.text_col,
        text_cols=text_cols,
        label_col=args.label_col,
        category_col=args.category_col,
        limit=args.limit,
        label_filter=args.label_filter,
        sample=args.sample,
        sample_seed=args.seed,
    )
    if not rows:
        print(f"No usable rows found in {input_path}")
        return

    qr_image_pool = ImagePool(args.qr_image_dir) if args.qr_image_dir else None
    if qr_image_pool:
        print(f"Using {len(qr_image_pool)} real QR images from {args.qr_image_dir}")

    rng = random.Random(args.seed)
    manifest_path = output_dir / "manifest.csv"
    write_header = not manifest_path.exists()
    written = 0

    # Manifest rows are written and flushed per-sample, not buffered until
    # the loop finishes — a mid-batch crash (a real, observed failure mode,
    # see ScreenshotRenderer) must not leave successfully-rendered images
    # with no corresponding manifest entry.
    with ScreenshotRenderer() as renderer, open(manifest_path, "a", newline="", encoding="utf-8") as mf:
        writer = csv.DictWriter(mf, fieldnames=MANIFEST_FIELDS)
        if write_header:
            writer.writeheader()

        for i, row in enumerate(rows):
            image_bytes, ext, ctx = render_row(renderer, row, args.source_type, rng, qr_image_pool=qr_image_pool)
            # row.row_id (source+original-index+content-hash) rather than a
            # per-run positional index — otherwise two runs against the same
            # output-dir (e.g. one per --label-filter) collide and overwrite
            # each other's images.
            sample_id = row.row_id
            image_rel_path = f"images/{sample_id}.{ext}"
            (output_dir / image_rel_path).write_bytes(image_bytes)

            # Ground truth must match what's actually visible in the image,
            # not the raw source text — the subject line, if embedded in the
            # body text, gets split out into the header and must not appear
            # twice (or be missing) in the recorded ground truth.
            visible_text = (
                f"{ctx['email_subject']}\n\n{ctx['message_text']}" if ctx.get("email_subject") else ctx["message_text"]
            )

            writer.writerow(
                {
                    "sample_id": sample_id,
                    "source_dataset": source_name,
                    "source_row_id": row.row_id,
                    "group_key": row.group_key,
                    "platform": ctx["platform"],
                    "label": row.label,
                    # source-type is only a meaningful category hint for the
                    # fraudulent class — a "genuine" row sampled from a
                    # phishing/scam file's negative examples is not itself
                    # phishing, so it must not inherit that hint.
                    "category_hint": row.category_hint or (args.source_type if row.label == "fraudulent" else ""),
                    "image_path": image_rel_path,
                    "ocr_ground_truth": visible_text,
                    "theme": ctx["theme"],
                    "device_width": ctx["device_width"],
                    "is_forwarded": ctx["is_forwarded"],
                    "is_unknown_number": ctx["is_unknown_number"],
                    "has_reply": ctx["has_reply"],
                    "qr_payload": ctx.get("qr_payload") or "",
                    "qr_source": ctx.get("qr_source") or "",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            mf.flush()
            written += 1
            print(f"[{i + 1}/{len(rows)}] rendered {image_rel_path} ({ctx['platform']}, {ctx['theme']}, {row.label})")

    print(f"\nWrote {written} samples. Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
