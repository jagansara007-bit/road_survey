"""training/make_split.py

Sequence-grouped dataset split.

Groups images so near-duplicate frames never straddle train / val / test.
The split is 70 / 15 / 15 by GROUP, not by image.

Group strategies
----------------
prefix
    Group key = filename up to the first underscore, e.g.
    ``japan_000001.jpg`` → ``japan``.  Default.

index_window
    Group key = floor(numeric_id / W) where W is the window size (--window).
    Consecutive frame indices within the same window land in the same group.
    Useful when filenames carry a monotone frame counter but no prefix.

phash
    Cluster images by perceptual hash (imagehash library required).
    Two images whose Hamming distance ≤ --phash_threshold share a group.
    Requires ``pip install imagehash Pillow``.

If all groups produced by ``prefix`` are singletons (no sequence structure
detected) the script warns and recommends ``index_window`` or ``phash``.

Outputs
-------
data/processed/split_manifest.csv   columns: image, group, split
"""
from __future__ import annotations

import argparse
import csv
import random
import re
import sys
import warnings
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

# ── group-key builders ────────────────────────────────────────────────────────


def group_by_prefix(img_path: Path, **_kwargs: object) -> str:
    """Return text before the first underscore, or first 4 characters."""
    name = img_path.stem
    if "_" in name:
        return name.split("_")[0]
    return name[:4] if len(name) >= 4 else name


def group_by_index_window(img_path: Path, window: int = 10, **_kwargs: object) -> str:
    """Return str(floor(numeric_id / window)); falls back to prefix on failure."""
    name = img_path.stem
    digits = re.findall(r"\d+", name)
    if digits:
        idx = int(digits[-1])
        return str(idx // window)
    return group_by_prefix(img_path)


def group_by_phash(img_path: Path, phash_map: dict[Path, str], **_kwargs: object) -> str:
    """Return pre-computed phash cluster id."""
    return phash_map.get(img_path, img_path.stem)


# ── phash clustering ──────────────────────────────────────────────────────────


def compute_phash_clusters(image_paths: list[Path], threshold: int) -> dict[Path, str]:
    """Cluster images by perceptual hash.  Requires imagehash + Pillow."""
    try:
        import imagehash
        from PIL import Image
    except ImportError:
        sys.exit(
            "ERROR: --group_strategy phash requires 'imagehash' and 'Pillow'.\n"
            "Install: pip install imagehash Pillow   (or: uv add imagehash)"
        )

    hashes: list[tuple[Path, object]] = []
    for p in image_paths:
        try:
            h = imagehash.phash(Image.open(p))
            hashes.append((p, h))
        except Exception as exc:  # noqa: BLE001
            warnings.warn(f"Could not hash {p}: {exc}", stacklevel=2)

    # Union-find
    parent: dict[int, int] = {i: i for i in range(len(hashes))}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        parent[find(a)] = find(b)

    for i in range(len(hashes)):
        for j in range(i + 1, len(hashes)):
            if (hashes[i][1] - hashes[j][1]) <= threshold:
                union(i, j)

    cluster_map: dict[Path, str] = {}
    for i, (p, _) in enumerate(hashes):
        cluster_map[p] = str(find(i))
    return cluster_map


# ── split logic ───────────────────────────────────────────────────────────────


def make_split(
    image_paths: list[Path],
    key_fn: Callable[..., str],
    key_kwargs: dict,
    train_ratio: float,
    val_ratio: float,
    seed: int,
) -> list[tuple[str, str, str]]:  # (image_name, group, split)
    """Return sorted list of (image_name, group_key, split_name) tuples."""
    groups: dict[str, list[Path]] = defaultdict(list)
    for p in image_paths:
        g = key_fn(p, **key_kwargs)
        groups[g].append(p)

    group_keys = sorted(groups)

    # Warn if all groups are singletons
    singleton_count = sum(1 for v in groups.values() if len(v) == 1)
    if singleton_count == len(group_keys) and len(group_keys) > 1:
        warnings.warn(
            f"All {len(group_keys)} groups are singletons — filename prefix carries "
            "no sequence information.  Consider --group_strategy index_window or phash.",
            UserWarning,
            stacklevel=3,
        )

    rng = random.Random(seed)
    rng.shuffle(group_keys)

    n = len(group_keys)
    n_train = max(1, round(n * train_ratio))
    n_val = max(1, round(n * val_ratio))
    # Remainder goes to test
    n_train = min(n_train, n - 2)
    n_val = min(n_val, n - n_train - 1)

    train_set = set(group_keys[:n_train])
    val_set = set(group_keys[n_train : n_train + n_val])

    rows: list[tuple[str, str, str]] = []
    for g in sorted(groups):
        split_name = "train" if g in train_set else ("val" if g in val_set else "test")
        for p in sorted(groups[g]):
            rows.append((p.name, g, split_name))

    rows.sort(key=lambda r: r[0])
    return rows


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Sequence-grouped dataset split")
    parser.add_argument("--dataset_root", required=True, help="Root with images/ subdir (or train/val/test subdirs)")
    parser.add_argument("--config", default="training/configs/classes.yaml")
    parser.add_argument(
        "--group_strategy",
        choices=["prefix", "index_window", "phash"],
        default="prefix",
    )
    parser.add_argument("--window", type=int, default=10, help="Window size for index_window strategy")
    parser.add_argument("--phash_threshold", type=int, default=10, help="Hamming distance threshold for phash")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train", type=float, default=0.70)
    parser.add_argument("--val", type=float, default=0.15)
    parser.add_argument("--output", default="data/processed/split_manifest.csv")
    args = parser.parse_args()

    root = Path(args.dataset_root)
    # Accept either flat images/ dir or a dataset with train/val/test already present
    images_dir = root / "images" if (root / "images").exists() else root
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    image_paths = sorted(p for p in images_dir.rglob("*") if p.suffix.lower() in image_exts)

    if not image_paths:
        sys.exit(f"No images found under {images_dir}")

    print(f"Found {len(image_paths)} images in {images_dir}")

    # Build group key function and kwargs
    key_kwargs: dict = {}
    if args.group_strategy == "prefix":
        key_fn: Callable[..., str] = group_by_prefix
    elif args.group_strategy == "index_window":
        key_fn = group_by_index_window
        key_kwargs["window"] = args.window
    else:  # phash
        print("Computing perceptual hashes (this may take a moment)…")
        phash_map = compute_phash_clusters(image_paths, args.phash_threshold)
        key_fn = group_by_phash
        key_kwargs["phash_map"] = phash_map

    rows = make_split(
        image_paths,
        key_fn,
        key_kwargs,
        train_ratio=args.train,
        val_ratio=args.val,
        seed=args.seed,
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["image", "group", "split"])
        writer.writerows(rows)

    # Summary
    counts: dict[str, int] = defaultdict(int)
    for _, _, s in rows:
        counts[s] += 1
    print(f"Split manifest written to {out_path}")
    print(f"  train: {counts['train']}  val: {counts['val']}  test: {counts['test']}")


if __name__ == "__main__":
    main()
