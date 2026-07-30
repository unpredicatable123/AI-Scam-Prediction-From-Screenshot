"""Group-aware, label-stratified dataset splitting (blueprint §13.3).

The single most important methodological safeguard in this project: every
sample sharing a `group_key` (i.e. rendered from the same source text row)
must land in the same split. A naive random split would let near-duplicate
renders of one source row (or even the same row twice under a different
platform) leak between train and test, inflating reported accuracy in a way
that would not survive contact with real screenshots.

Uses StratifiedGroupKFold (10 folds) so both the group constraint and label
balance are respected simultaneously: 1 fold -> test, 1 -> calibration,
1 -> val, the remaining 7 -> train (70/10/10/10, per §13.1).

Known limitation, stated rather than hidden: there is currently no
real-screenshot subset in this dataset (see memory/project_blueprint_decisions.md)
— every image is synthetically rendered from real text. The blueprint's
"real-only test subset" leakage safeguard (§18.3 R10) cannot be applied yet.
"""

import argparse
import csv
from pathlib import Path

from sklearn.model_selection import StratifiedGroupKFold

FOLD_ASSIGNMENT = {0: "test", 1: "calibration", 2: "val"}  # folds 3-9 -> train


def split_manifest(manifest_path, seed=42):
    with open(manifest_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    labels = [r["label"] for r in rows]
    groups = [r["group_key"] for r in rows]

    sgkf = StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=seed)
    fold_of_index = {}
    for fold_idx, (_, test_idx) in enumerate(sgkf.split(rows, labels, groups)):
        for i in test_idx:
            fold_of_index[i] = fold_idx

    for i, row in enumerate(rows):
        fold = fold_of_index[i]
        row["split"] = FOLD_ASSIGNMENT.get(fold, "train")

    return rows


def verify_no_group_leakage(rows):
    """Hard assertion, not just a print — a leakage bug here invalidates
    every downstream metric."""
    group_to_splits = {}
    for row in rows:
        group_to_splits.setdefault(row["group_key"], set()).add(row["split"])
    leaked = {g: s for g, s in group_to_splits.items() if len(s) > 1}
    if leaked:
        raise AssertionError(f"{len(leaked)} group_keys span multiple splits — leakage bug. Example: {next(iter(leaked.items()))}")


def summarize(rows):
    from collections import Counter

    counts = Counter((r["split"], r["label"]) for r in rows)
    splits = ["train", "val", "calibration", "test"]
    print(f"{'split':<12}{'genuine':>10}{'fraudulent':>12}{'total':>9}")
    for s in splits:
        g = counts.get((s, "genuine"), 0)
        f = counts.get((s, "fraudulent"), 0)
        print(f"{s:<12}{g:>10}{f:>12}{g+f:>9}")
    print(f"{'TOTAL':<12}{sum(1 for r in rows if r['label']=='genuine'):>10}"
          f"{sum(1 for r in rows if r['label']=='fraudulent'):>12}{len(rows):>9}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    rows = split_manifest(args.manifest, seed=args.seed)
    verify_no_group_leakage(rows)
    summarize(rows)

    fieldnames = list(rows[0].keys())
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {out_path} (leakage check passed: 0 group_keys span multiple splits)")


if __name__ == "__main__":
    main()
