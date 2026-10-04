"""training/convert_to_3class.py

Maps CRDDC/RDD raw class IDs to the 3-class scheme used for YOLO training:

    D00, D10  →  crack     (class 0)
    D20       →  alligator (class 1)
    D40       →  pothole   (class 2)

Excluded-class boxes are dropped per the chosen policy.
Original sub-labels of crack boxes are preserved in a side CSV for the
orientation classifier.

Usage
-----
    python training/convert_to_3class.py \\
        --manifest data/processed/split_manifest.csv \\
        --dataset_root data/raw \\
        --classes_config training/configs/classes.yaml \\
        --excluded_only_policy drop \\
        --output_dir data/processed/yolo3
"""
from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

# ── helpers ──────────────────────────────────────────────────────────────────


def load_config(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_id_mapping(cfg: dict[str, Any]) -> dict[str, int | None]:
    """Return raw_class_name → 3class_id (or None for excluded)."""
    mapping: dict[str, int | None] = {}
    three_class = cfg.get("three_class_mapping", {})
    for cls_name, idx in three_class.items():
        mapping[str(cls_name)] = int(idx)
    for cls_name in cfg.get("excluded_classes", []):
        if str(cls_name) not in mapping:
            mapping[str(cls_name)] = None  # explicitly excluded
    return mapping


def raw_label_id_to_name(cfg: dict[str, Any]) -> dict[int, str]:
    """Build integer label id → class name from the dataset's class list.

    The CRDDC dataset uses integer IDs in .txt files.  Without an explicit
    id_map in classes.yaml this function returns an empty dict and callers
    fall back to treating the raw ID as the class name string directly.
    """
    return {int(k): str(v) for k, v in cfg.get("id_map", {}).items()}


# ── per-file conversion ───────────────────────────────────────────────────────


def convert_label_file(
    src: Path,
    dst: Path,
    id_to_name: dict[int, str],
    name_to_3class: dict[str, int | None],
    excluded_only_policy: str,
    crack_origins: list[dict[str, str]],
    image_name: str,
) -> None:
    """Read a YOLO label file, remap classes, write converted file."""
    if not src.exists():
        # No label → background image; write empty file
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text("", encoding="utf-8")
        return

    text = src.read_text(encoding="utf-8").strip()
    rows = [line.split() for line in text.splitlines() if line.strip()] if text else []

    out_rows: list[str] = []
    all_excluded = True

    for box_idx, row in enumerate(rows):
        raw_id_str = row[0]
        coords = row[1:]

        # Resolve class name
        if raw_id_str.isdigit():
            cls_name = id_to_name.get(int(raw_id_str), raw_id_str)
        else:
            cls_name = raw_id_str

        new_id = name_to_3class.get(cls_name)

        if new_id is None:
            # Excluded class box – drop it
            continue

        all_excluded = False
        out_rows.append(f"{new_id} {' '.join(coords)}")

        # Record crack origin for orientation task
        if new_id == 0:  # crack super-class
            crack_origins.append({
                "image": image_name,
                "box_id": str(box_idx),
                "original_class": cls_name,
            })

    dst.parent.mkdir(parents=True, exist_ok=True)

    if all_excluded and rows and excluded_only_policy == "keep_as_background":
        # Keep image but write empty label (background)
        dst.write_text("", encoding="utf-8")
    else:
        dst.write_text("\n".join(out_rows) + ("\n" if out_rows else ""), encoding="utf-8")


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert CRDDC labels to 3-class YOLO format")
    parser.add_argument("--manifest", required=True, help="split_manifest.csv from make_split.py")
    parser.add_argument("--dataset_root", required=True, help="Root of raw dataset (with train/val/test or images/)")
    parser.add_argument("--classes_config", default="training/configs/classes.yaml")
    parser.add_argument(
        "--excluded_only_policy",
        choices=["drop", "keep_as_background"],
        default="drop",
    )
    parser.add_argument("--output_dir", default="data/processed/yolo3")
    args = parser.parse_args()

    cfg = load_config(args.classes_config)
    name_to_3class = build_id_mapping(cfg)
    id_to_name = raw_label_id_to_name(cfg)

    root = Path(args.dataset_root)
    out_root = Path(args.output_dir)

    # Read manifest
    manifest: list[dict[str, str]] = []
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        sys.exit(f"ERROR: manifest not found: {manifest_path}")

    with open(manifest_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        manifest = list(reader)

    if not manifest:
        sys.exit("ERROR: manifest is empty")

    crack_origins: list[dict[str, str]] = []
    images_processed = 0

    for row in manifest:
        img_name = row["image"]
        split = row["split"]
        img_stem = Path(img_name).stem

        # Locate source image (may live in split subdir or flat images dir)
        src_img: Path | None = None
        for candidate in [
            root / split / "images" / img_name,
            root / "images" / img_name,
            root / img_name,
        ]:
            if candidate.exists():
                src_img = candidate
                break

        if src_img is None:
            continue  # image not present (gitignored dataset)

        # Copy image
        dst_img = out_root / split / "images" / img_name
        dst_img.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_img, dst_img)

        # Convert label
        src_label: Path | None = None
        for candidate in [
            root / split / "labels" / (img_stem + ".txt"),
            root / "labels" / (img_stem + ".txt"),
        ]:
            if candidate.exists():
                src_label = candidate
                break

        dst_label = out_root / split / "labels" / (img_stem + ".txt")
        convert_label_file(
            src_label or Path("/nonexistent"),
            dst_label,
            id_to_name,
            name_to_3class,
            args.excluded_only_policy,
            crack_origins,
            img_name,
        )
        images_processed += 1

    # Write dataset.yaml
    nc = cfg.get("nc", 3)
    names = cfg.get("names", ["crack", "alligator", "pothole"])
    dataset_yaml = {
        "path": str(out_root.resolve()),
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "nc": nc,
        "names": names,
    }
    out_root.mkdir(parents=True, exist_ok=True)
    with open(out_root / "dataset.yaml", "w", encoding="utf-8") as f:
        yaml.dump(dataset_yaml, f, default_flow_style=False, allow_unicode=True)

    # Write crack origins CSV
    origins_path = out_root / "crack_origins.csv"
    with open(origins_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image", "box_id", "original_class"])
        writer.writeheader()
        writer.writerows(crack_origins)

    print(f"Converted {images_processed} images -> {out_root}")
    print(f"Crack origins: {len(crack_origins)} boxes -> {origins_path}")
    print(f"YOLO dataset.yaml: {out_root / 'dataset.yaml'}")


if __name__ == "__main__":
    main()
