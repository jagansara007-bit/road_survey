"""training/make_orientation_crops.py

Extracts crack bounding-box crops from TRAIN and VAL splits only.
(Test split is never cropped to prevent data leakage into the orientation
classifier evaluation.)

Labels:
    longitudinal  ← D00 original class
    transverse    ← D10 original class

Output directory:
    data/processed/orientation/
        train/
            longitudinal/  …PNG crops
            transverse/    …PNG crops
        val/
            longitudinal/
            transverse/

Usage
-----
    python training/make_orientation_crops.py \\
        --manifest data/processed/split_manifest.csv \\
        --dataset_root data/raw \\
        --crack_origins data/processed/yolo3/crack_origins.csv \\
        --output_dir data/processed/orientation
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from PIL import Image

# ── constants ─────────────────────────────────────────────────────────────────

LONGITUDINAL_CLASSES = {"D00"}
TRANSVERSE_CLASSES = {"D10"}
ORIENTATION_LABEL = {**{c: "longitudinal" for c in LONGITUDINAL_CLASSES},
                      **{c: "transverse" for c in TRANSVERSE_CLASSES}}


# ── helpers ───────────────────────────────────────────────────────────────────


def yolo_box_to_pixel(
    cx: float, cy: float, w: float, h: float, img_w: int, img_h: int
) -> tuple[int, int, int, int]:
    """Convert YOLO normalised (cx,cy,w,h) → pixel (x1,y1,x2,y2), clamped."""
    x1 = int((cx - w / 2) * img_w)
    y1 = int((cy - h / 2) * img_h)
    x2 = int((cx + w / 2) * img_w)
    y2 = int((cy + h / 2) * img_h)
    x1, x2 = max(0, x1), min(img_w, x2)
    y1, y2 = max(0, y1), min(img_h, y2)
    return x1, y1, x2, y2


def locate_image(root: Path, split: str, img_name: str) -> Path | None:
    for candidate in [
        root / split / "images" / img_name,
        root / "images" / img_name,
        root / img_name,
    ]:
        if candidate.exists():
            return candidate
    return None


def locate_label(root: Path, split: str, img_stem: str) -> Path | None:
    for candidate in [
        root / split / "labels" / (img_stem + ".txt"),
        root / "labels" / (img_stem + ".txt"),
    ]:
        if candidate.exists():
            return candidate
    return None


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract crack orientation crops from TRAIN and VAL splits")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--dataset_root", required=True)
    parser.add_argument("--crack_origins", required=True, help="crack_origins.csv from convert_to_3class.py")
    parser.add_argument("--output_dir", default="data/processed/orientation")
    parser.add_argument("--min_size", type=int, default=10, help="Skip crops smaller than this in pixels")
    args = parser.parse_args()

    # Load manifest
    manifest: dict[str, str] = {}  # img_name → split
    with open(args.manifest, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            manifest[row["image"]] = row["split"]

    # Load crack origins (box_id × original_class for each image)
    origins: dict[str, dict[str, str]] = {}  # image → {box_id → orig_class}
    with open(args.crack_origins, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            origins.setdefault(row["image"], {})[row["box_id"]] = row["original_class"]

    root = Path(args.dataset_root)
    out_root = Path(args.output_dir)
    stats: dict[str, dict[str, int]] = {"train": {}, "val": {}}

    for img_name, split in manifest.items():
        if split not in ("train", "val"):
            continue  # never crop test

        img_stem = Path(img_name).stem
        img_path = locate_image(root, split, img_name)
        lbl_path = locate_label(root, split, img_stem)

        if img_path is None or lbl_path is None:
            continue  # dataset not present locally

        try:
            img = Image.open(img_path).convert("RGB")
        except Exception:  # noqa: BLE001, S112
            continue

        img_w, img_h = img.size
        origin_map = origins.get(img_name, {})

        lbl_rows = [ln.split() for ln in lbl_path.read_text(encoding="utf-8").splitlines() if ln.strip()]

        for box_idx, row in enumerate(lbl_rows):
            cls_name = row[0]  # may be int string or class name
            coords = row[1:]
            if len(coords) < 4:
                continue

            orig_class = origin_map.get(str(box_idx), cls_name)
            label = ORIENTATION_LABEL.get(orig_class)
            if label is None:
                continue  # not a crack box

            cx, cy, bw, bh = (float(v) for v in coords[:4])
            x1, y1, x2, y2 = yolo_box_to_pixel(cx, cy, bw, bh, img_w, img_h)
            if (x2 - x1) < args.min_size or (y2 - y1) < args.min_size:
                continue

            crop = img.crop((x1, y1, x2, y2))
            dst_dir = out_root / split / label
            dst_dir.mkdir(parents=True, exist_ok=True)
            crop_name = f"{img_stem}_box{box_idx}.png"
            crop.save(dst_dir / crop_name)

            stats[split][label] = stats[split].get(label, 0) + 1

    print(f"Orientation crops written to {out_root}")
    for sp, counts in stats.items():
        print(f"  {sp}: " + "  ".join(f"{lbl}={n}" for lbl, n in sorted(counts.items())))


if __name__ == "__main__":
    main()
