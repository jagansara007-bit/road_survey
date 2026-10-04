"""training/check_leakage.py

Leakage verifier for split manifests.

Exits with code 1 (FAIL) if any group appears in more than one split.
Also reports the nearest cross-split pair by filename Levenshtein distance
(or by phash Hamming distance when imagehash is installed and --images_root
is provided).

Usage
-----
    python training/check_leakage.py \\
        --manifest data/processed/split_manifest.csv

    # with phash nearest-pair:
    python training/check_leakage.py \\
        --manifest data/processed/split_manifest.csv \\
        --images_root data/raw/images
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

# ── string distance fallback ──────────────────────────────────────────────────


def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            curr.append(min(prev[j] + 1, curr[-1] + 1, prev[j - 1] + (ca != cb)))
        prev = curr
    return prev[-1]


# ── phash nearest pair ────────────────────────────────────────────────────────


def nearest_cross_split_phash(
    cross_pairs: list[tuple[str, str, str, str]],
    images_root: Path,
) -> tuple[str, str, int] | None:
    """Return (img_a, img_b, distance) for the nearest cross-split pair by phash."""
    try:
        import imagehash
        from PIL import Image
    except ImportError:
        return None

    best: tuple[str, str, int] | None = None
    for img_a, split_a, img_b, split_b in cross_pairs[:200]:  # limit for speed
        pa = images_root / img_a
        pb = images_root / img_b
        if not (pa.exists() and pb.exists()):
            continue
        try:
            ha = imagehash.phash(Image.open(pa))
            hb = imagehash.phash(Image.open(pb))
            dist = ha - hb
            if best is None or dist < best[2]:
                best = (img_a, img_b, dist)
        except Exception:  # noqa: BLE001, S112
            continue
    return best


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify no group straddles train/val/test splits")
    parser.add_argument("--manifest", required=True, help="Path to split_manifest.csv")
    parser.add_argument(
        "--images_root",
        default=None,
        help="Optional: image directory for phash nearest-pair report",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        sys.exit(f"ERROR: manifest not found: {manifest_path}")

    # Load manifest
    group_to_splits: dict[str, set[str]] = defaultdict(set)
    image_to_split: dict[str, str] = {}
    image_to_group: dict[str, str] = {}

    with open(manifest_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            img = row["image"]
            group = row["group"]
            split = row["split"]
            group_to_splits[group].add(split)
            image_to_split[img] = split
            image_to_group[img] = group

    # Check for leaking groups
    leaking = {g: splits for g, splits in group_to_splits.items() if len(splits) > 1}

    if leaking:
        print(f"LEAKAGE DETECTED: {len(leaking)} group(s) span multiple splits.")
        for g, splits in sorted(leaking.items()):
            print(f"  group={g!r}  splits={sorted(splits)}")

        # Find nearest cross-split image pairs within leaking groups
        print("\nNearest cross-split pair (by filename distance):")
        best_str: tuple[str, str, int] | None = None
        for g in leaking:
            imgs_in_group = [img for img, grp in image_to_group.items() if grp == g]
            for i in range(len(imgs_in_group)):
                for j in range(i + 1, len(imgs_in_group)):
                    ia, ib = imgs_in_group[i], imgs_in_group[j]
                    if image_to_split[ia] != image_to_split[ib]:
                        dist = levenshtein(ia, ib)
                        if best_str is None or dist < best_str[2]:
                            best_str = (ia, ib, dist)

        if best_str:
            print(f"  {best_str[0]} ({image_to_split[best_str[0]]}) <-> "
                  f"{best_str[1]} ({image_to_split[best_str[1]]})  "
                  f"edit-distance={best_str[2]}")

        if args.images_root:
            print("\nNearest cross-split pair (by phash):")
            # Build cross pairs from all images in different splits of same group
            cross_pairs: list[tuple[str, str, str, str]] = []
            for g in leaking:
                imgs = [(img, image_to_split[img]) for img, grp in image_to_group.items() if grp == g]
                for i in range(len(imgs)):
                    for j in range(i + 1, len(imgs)):
                        if imgs[i][1] != imgs[j][1]:
                            cross_pairs.append((imgs[i][0], imgs[i][1], imgs[j][0], imgs[j][1]))

            result = nearest_cross_split_phash(cross_pairs, Path(args.images_root))
            if result:
                a, b, dist = result
                print(f"  {a} ({image_to_split[a]}) <-> {b} ({image_to_split[b]})  phash-dist={dist}")
            else:
                print("  (imagehash not installed or images not found)")

        sys.exit(1)
    else:
        n_groups = len(group_to_splits)
        n_images = len(image_to_split)
        print(f"OK: no leakage detected.  {n_groups} groups, {n_images} images, all clean.")
        sys.exit(0)


if __name__ == "__main__":
    main()
