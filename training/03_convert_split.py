"""training/03_convert_split.py  (shim – delegates to make_split.py)

This file is kept for backward compatibility.
All logic has moved to training/make_split.py which supports configurable
group strategies (prefix / index_window / phash), leakage checking, and
a deterministic manifest CSV.

Usage (new):
    python training/make_split.py --dataset_root data/raw --output data/processed/split_manifest.csv

Usage (legacy – this file):
    python training/03_convert_split.py --image_dir data/raw/images
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="[SHIM] Sequence-grouped split – delegates to make_split.py"
    )
    parser.add_argument("--image_dir", type=str, default="data/raw/images")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    # Import and call make_split directly
    sys.path.insert(0, str(Path(__file__).parent))
    from make_split import group_by_prefix, make_split

    image_dir = Path(args.image_dir)
    if not image_dir.exists():
        print(f"Directory {image_dir} not found; run with valid dataset path.")
        return

    exts = {".jpg", ".jpeg", ".png"}
    images = sorted(p for p in image_dir.iterdir() if p.suffix.lower() in exts)
    rows = make_split(images, group_by_prefix, {}, 0.70, 0.15, args.seed)

    counts = {"train": 0, "val": 0, "test": 0}
    for _, _, split in rows:
        counts[split] += 1

    total_groups = len({g for _, g, _ in rows})
    print(f"Sequence split complete across {total_groups} groups:")
    print(f"Train: {counts['train']} frames")
    print(f"Val:   {counts['val']} frames")
    print(f"Test:  {counts['test']} frames")
    print("Tip: use training/make_split.py for full options and manifest CSV output.")


if __name__ == "__main__":
    main()
