#!/usr/bin/env python3
"""
Sample ~100 closest-approach crops stratified by system severity (seeded).
Exports a CSV (crop_id, filename, system_severity, rater_1, rater_2, rater_3)
and copies sampled crops to an export directory.
If crops source is absent, prints NOT MEASURED and exits 0.
"""
import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser(description="Create expert rating sheet from closest-approach crops.")
    parser.add_argument("--crops-dir", default="data/crops", help="Directory containing crop images")
    parser.add_argument("--metadata", default="data/crops/metadata.json", help="Path to crops metadata JSON")
    parser.add_argument("--output-dir", default="reports/expert_rating", help="Output directory for rating sheet")
    parser.add_argument("--sample-size", type=int, default=100, help="Number of crops to sample")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic sampling")
    args = parser.parse_args()

    crops_dir = Path(args.crops_dir)
    meta_path = Path(args.metadata)
    out_dir = Path(args.output_dir)

    if not crops_dir.exists() or not meta_path.exists():
        print(f"NOT MEASURED: Crops data absent (crops_exists={crops_dir.exists()}, meta_exists={meta_path.exists()})")
        sys.exit(0)

    with meta_path.open("r", encoding="utf-8") as f:
        items = json.load(f)

    if not items:
        print("NOT MEASURED: Metadata JSON contains 0 crop records.")
        sys.exit(0)

    # Group by system_severity
    by_sev = {"Low": [], "Medium": [], "High": []}
    for item in items:
        sev = item.get("system_severity", item.get("severity", "Low"))
        if sev in by_sev:
            by_sev[sev].append(item)
        else:
            by_sev["Low"].append(item)

    rng = np.random.RandomState(args.seed)
    sampled = []
    target_per_class = max(1, args.sample_size // 3)

    for sev, group in by_sev.items():
        if not group:
            continue
        n_take = min(len(group), target_per_class)
        chosen_indices = rng.choice(len(group), size=n_take, replace=False)
        for idx in chosen_indices:
            sampled.append(group[idx])

    # If shortfall, sample from remainder
    remaining = [item for item in items if item not in sampled]
    if len(sampled) < args.sample_size and remaining:
        extra_needed = min(len(remaining), args.sample_size - len(sampled))
        chosen_extras = rng.choice(len(remaining), size=extra_needed, replace=False)
        for idx in chosen_extras:
            sampled.append(remaining[idx])

    out_dir.mkdir(parents=True, exist_ok=True)
    out_crops = out_dir / "crops"
    out_crops.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "rating_sheet.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["crop_id", "filename", "system_severity", "rater_1", "rater_2", "rater_3"])
        for idx, item in enumerate(sampled, start=1):
            fname = Path(item["filename"]).name
            src_file = crops_dir / fname
            if src_file.exists():
                shutil.copy2(src_file, out_crops / fname)
            writer.writerow([idx, fname, item.get("system_severity", item.get("severity", "Low")), "", "", ""])

    print("=" * 60)
    print("EXPERT RATING SHEET GENERATED")
    print("=" * 60)
    print(f"Total Sampled Crops : {len(sampled)}")
    print(f"Random Seed         : {args.seed}")
    print(f"Rating Sheet CSV    : {csv_path}")
    print(f"Copied Crops Dir    : {out_crops}")
    print("=" * 60)


if __name__ == "__main__":
    main()
