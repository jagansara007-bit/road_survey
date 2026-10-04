"""training/audit_dataset.py

Excluded-class audit for CRDDC/RDD dataset.

Counts, per split: total images, boxes per class, images whose ONLY labels
are excluded classes, images with empty label files, and images with no label
file at all.  Reports the filenames affected by the chosen policy.

Usage
-----
    python training/audit_dataset.py \\
        --dataset_root data/raw \\
        --classes_config training/configs/classes.yaml \\
        --excluded_only_policy drop \\
        --output_dir reports

Outputs
-------
    reports/dataset_audit.json  – machine-readable counts
    reports/dataset_audit.md    – human-readable markdown table
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

# ── helpers ──────────────────────────────────────────────────────────────────


def load_classes_config(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def class_id_to_name(cfg: dict[str, Any]) -> dict[int, str]:
    """Build int-id → name from active_classes + excluded_classes in order."""
    # CRDDC stores class IDs as sequential integers; we need to know the full
    # ordered list.  If the config doesn't have an ordered list we fall back to
    # returning the raw integer.
    # Build a sorted name list: active keys first (D00, D10, D20, D40),
    # then excluded.  The actual integer IDs used in a dataset may differ;
    # the audit reports raw IDs alongside names where known.
    known: dict[int, str] = {}
    # If the config has an explicit id_map, use it.
    id_map = cfg.get("id_map", {})
    for idx, name in id_map.items():
        known[int(idx)] = name
    return known


def get_excluded_set(cfg: dict[str, Any]) -> set[str]:
    return set(cfg.get("excluded_classes", []))


def read_label_file(label_path: Path) -> list[list[str]]:
    """Return list of rows (split by whitespace); empty list if file is empty."""
    text = label_path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    return [line.split() for line in text.splitlines() if line.strip()]


def audit_split(
    split_dir: Path,
    excluded_set: set[str],
    id_to_name: dict[int, str],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    """Audit a single split directory (expects images/ and labels/ subdirs)."""
    images_dir = split_dir / "images"
    labels_dir = split_dir / "labels"

    if not images_dir.exists():
        return {"error": f"images dir not found: {images_dir}"}

    image_files = sorted(
        p for p in images_dir.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    )

    total_images = len(image_files)
    boxes_per_raw_id: dict[str, int] = {}
    excluded_only_images: list[str] = []
    empty_label_images: list[str] = []
    no_label_images: list[str] = []

    # Build a name→excluded lookup; exclude by class name string (D44, etc.)
    # The label files store integer class IDs.  We use the config's id_map to
    # translate; where absent we keep the integer and compare to excluded names.
    excluded_ids: set[str] = set()
    id_map_inv = cfg.get("id_map", {})  # int → name; may be empty
    for idx, name in id_map_inv.items():
        if name in excluded_set:
            excluded_ids.add(str(idx))

    for img_path in image_files:
        label_path = labels_dir / (img_path.stem + ".txt")

        if not label_path.exists():
            no_label_images.append(img_path.name)
            continue

        rows = read_label_file(label_path)

        if not rows:
            empty_label_images.append(img_path.name)
            continue

        raw_ids_in_image: list[str] = []
        for row in rows:
            if not row:
                continue
            raw_id = row[0]
            raw_ids_in_image.append(raw_id)
            boxes_per_raw_id[raw_id] = boxes_per_raw_id.get(raw_id, 0) + 1

        # "Excluded-only" = every box is an excluded class
        all_excluded = all(
            (rid in excluded_ids) or (id_to_name.get(int(rid) if rid.isdigit() else -1, rid) in excluded_set)
            for rid in raw_ids_in_image
        )
        if raw_ids_in_image and all_excluded:
            excluded_only_images.append(img_path.name)

    return {
        "total_images": total_images,
        "boxes_per_class_id": boxes_per_raw_id,
        "excluded_only_count": len(excluded_only_images),
        "excluded_only_images": excluded_only_images,
        "empty_label_count": len(empty_label_images),
        "empty_label_images": empty_label_images,
        "no_label_count": len(no_label_images),
        "no_label_images": no_label_images,
    }


# ── markdown formatter ────────────────────────────────────────────────────────


def to_markdown(report: dict[str, Any], policy: str) -> str:
    lines = [
        "# Dataset Audit Report",
        "",
        f"**Policy:** `--excluded-only-policy {policy}`  ",
        (
            "**Note:** Real-data numbers are NOT MEASURED "
            "(no dataset present at run time). This report reflects "
            "synthetic / provided dataset only."
        ),
        "",
    ]

    splits = [k for k in report if k not in {"policy", "excluded_classes"}]
    for split in splits:
        data = report[split]
        if "error" in data:
            lines += [f"## {split}", f"*{data['error']}*", ""]
            continue
        lines += [
            f"## Split: `{split}`",
            "",
            "| Metric | Count |",
            "|:-------|------:|",
            f"| Total images | {data['total_images']} |",
            f"| Images with no label file | {data['no_label_count']} |",
            f"| Images with empty label file | {data['empty_label_count']} |",
            f"| Excluded-only images | {data['excluded_only_count']} |",
            "",
        ]

        if data["boxes_per_class_id"]:
            lines += ["### Boxes per class ID", "", "| Class ID | Count |", "|:---------|------:|"]
            for cid, cnt in sorted(data["boxes_per_class_id"].items(), key=lambda x: x[0]):
                lines.append(f"| {cid} | {cnt} |")
            lines.append("")

        if data["excluded_only_images"]:
            lines += [
                f"### Excluded-only images (policy=`{policy}`)",
                "",
                "| Filename |",
                "|:---------|",
            ]
            for fn in data["excluded_only_images"][:50]:
                lines.append(f"| `{fn}` |")
            if len(data["excluded_only_images"]) > 50:
                lines.append(f"| … and {len(data['excluded_only_images']) - 50} more |")
            lines.append("")

    return "\n".join(lines)


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit a CRDDC-format dataset for excluded classes and empty labels."
    )
    parser.add_argument("--dataset_root", required=True, help="Root dir containing train/, val/, test/ subdirs")
    parser.add_argument(
        "--classes_config",
        default="training/configs/classes.yaml",
        help="Path to classes.yaml",
    )
    parser.add_argument(
        "--excluded_only_policy",
        choices=["drop", "keep_as_background"],
        default="drop",
        help="What to do with excluded-only images (reported, not mutated here)",
    )
    parser.add_argument("--output_dir", default="reports", help="Where to write audit outputs")
    args = parser.parse_args()

    cfg = load_classes_config(args.classes_config)
    excluded_set = get_excluded_set(cfg)
    id_to_name = class_id_to_name(cfg)

    root = Path(args.dataset_root)
    splits = ["train", "val", "test"]

    report: dict[str, Any] = {
        "policy": args.excluded_only_policy,
        "excluded_classes": list(excluded_set),
    }

    for split in splits:
        split_dir = root / split
        if split_dir.exists():
            report[split] = audit_split(split_dir, excluded_set, id_to_name, cfg)
        else:
            report[split] = {"error": f"Split directory not found: {split_dir}"}

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "dataset_audit.json"
    md_path = out_dir / "dataset_audit.md"

    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(to_markdown(report, args.excluded_only_policy), encoding="utf-8")

    print("Audit complete. Results written to:")
    print(f"  {json_path}")
    print(f"  {md_path}")


if __name__ == "__main__":
    main()
