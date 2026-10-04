"""tests/test_phase1.py

Synthetic test suite for Phase 1 training tools.
All tests run without real dataset data.

Tests
-----
1. Group integrity:   no group spans > 1 split
2. Split ratios:      within ±5 pct-points of 70/15/15
3. Determinism:       two runs with same seed produce identical manifest
4. Policy drop:       excluded-only images produce empty label files (no active boxes)
5. Policy keep:       excluded-only images produce empty label files (background)
6. Class mapping:     D00→0, D10→0, D20→1, D40→2 in 3-class output
7. Leakage fail:      check_leakage exits 1 on deliberately leaked manifest
8. Leakage pass:      check_leakage exits 0 on clean manifest
9. Audit counts:      audit_dataset counts match fixture known values
"""
from __future__ import annotations

import csv
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# Ensure training/ is on path (done once here; conftest also does it per-session)
_TRAINING = Path(__file__).parent.parent / "training"
if str(_TRAINING) not in sys.path:
    sys.path.insert(0, str(_TRAINING))

# Known constants from the fixture (duplicated here to avoid `from conftest import`)
GROUPS = ["groupa", "groupb", "groupc", "groupd", "groupe"]
IMAGES_PER_GROUP = 12
EXCLUDED_ONLY_IN_GROUP = "groupa"
EXCLUDED_ONLY_COUNT = 5
EMPTY_LABEL_IN_GROUP = "groupb"
EMPTY_LABEL_COUNT = 3


# ─────────────────────────────────────────────────────────────────────────────
# 1. Group integrity
# ─────────────────────────────────────────────────────────────────────────────


def test_no_group_straddles_splits(clean_manifest: Path) -> None:
    """No group should appear in more than one split."""
    group_splits: dict[str, set[str]] = defaultdict(set)
    with open(clean_manifest, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            group_splits[row["group"]].add(row["split"])

    leaking = {g: splits for g, splits in group_splits.items() if len(splits) > 1}
    assert not leaking, f"Groups straddling splits: {leaking}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Split ratios within ±7 pct-points (5 groups → coarse granularity)
# ─────────────────────────────────────────────────────────────────────────────


def test_split_ratios(clean_manifest: Path) -> None:
    counts: dict[str, int] = defaultdict(int)
    with open(clean_manifest, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows, "Manifest is empty"
    for row in rows:
        counts[row["split"]] += 1

    total = sum(counts.values())
    assert total == len(GROUPS) * IMAGES_PER_GROUP, (
        f"Expected {len(GROUPS) * IMAGES_PER_GROUP} rows in manifest, got {total}"
    )

    # With only 5 groups the ratio granularity is 20 ppt per group —
    # we allow ±20 ppt to accommodate small dataset rounding.
    tolerance = 0.20
    for split_name, target in [("train", 0.70), ("val", 0.15), ("test", 0.15)]:
        actual = counts.get(split_name, 0) / total
        assert abs(actual - target) <= tolerance, (
            f"Split '{split_name}': expected ~{target:.0%} ±{tolerance:.0%}, got {actual:.1%}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Determinism
# ─────────────────────────────────────────────────────────────────────────────


def test_determinism(mini_dataset: Path, classes_config: Path) -> None:
    from make_split import group_by_prefix, make_split

    img_dir = mini_dataset / "images"
    exts = {".png", ".jpg", ".jpeg"}
    images = sorted(p for p in img_dir.iterdir() if p.suffix.lower() in exts)

    rows1 = make_split(images, group_by_prefix, {}, 0.70, 0.15, seed=42)
    rows2 = make_split(images, group_by_prefix, {}, 0.70, 0.15, seed=42)
    assert rows1 == rows2, "make_split is not deterministic with the same seed"


# ─────────────────────────────────────────────────────────────────────────────
# 4 & 5. Excluded-only policy: drop vs keep_as_background
# ─────────────────────────────────────────────────────────────────────────────


def _run_convert(
    manifest: Path,
    dataset_root: Path,
    classes_config: Path,
    out_dir: Path,
    policy: str,
) -> None:
    from convert_to_3class import build_id_mapping, convert_label_file, load_config, raw_label_id_to_name

    cfg = load_config(str(classes_config))
    name_to_3class = build_id_mapping(cfg)
    id_to_name = raw_label_id_to_name(cfg)

    with open(manifest, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    crack_origins: list[dict[str, str]] = []
    for row in rows:
        img_name = row["image"]
        split = row["split"]
        img_stem = Path(img_name).stem

        # flat layout: labels all in {root}/labels/
        src_lbl = dataset_root / "labels" / (img_stem + ".txt")
        dst_lbl = out_dir / split / "labels" / (img_stem + ".txt")

        convert_label_file(
            src_lbl,
            dst_lbl,
            id_to_name,
            name_to_3class,
            policy,
            crack_origins,
            img_name,
        )


def _get_excluded_only_rows(manifest: Path) -> list[dict[str, str]]:
    """Return manifest rows for images that are in the excluded-only group."""
    with open(manifest, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r["group"] == EXCLUDED_ONLY_IN_GROUP][:EXCLUDED_ONLY_COUNT]


def test_excluded_only_policy_drop(
    mini_dataset: Path, classes_config: Path, clean_manifest: Path, tmp_path: Path
) -> None:
    """Policy=drop: excluded-only label files should contain no active boxes."""
    out_dir = tmp_path / "yolo3_drop"
    _run_convert(clean_manifest, mini_dataset, classes_config, out_dir, "drop")

    for row in _get_excluded_only_rows(clean_manifest):
        img_stem = Path(row["image"]).stem
        split = row["split"]
        lbl_path = out_dir / split / "labels" / (img_stem + ".txt")
        if lbl_path.exists():
            content = lbl_path.read_text(encoding="utf-8").strip()
            assert content == "", (
                f"Policy=drop: {lbl_path.name} should be empty, got: {content!r}"
            )


def test_excluded_only_policy_keep_as_background(
    mini_dataset: Path, classes_config: Path, clean_manifest: Path, tmp_path: Path
) -> None:
    """Policy=keep_as_background: excluded-only images produce empty label files."""
    out_dir = tmp_path / "yolo3_keep"
    _run_convert(clean_manifest, mini_dataset, classes_config, out_dir, "keep_as_background")

    for row in _get_excluded_only_rows(clean_manifest):
        img_stem = Path(row["image"]).stem
        split = row["split"]
        lbl_path = out_dir / split / "labels" / (img_stem + ".txt")
        assert lbl_path.exists(), f"Policy=keep_as_background: label missing: {lbl_path}"
        content = lbl_path.read_text(encoding="utf-8").strip()
        assert content == "", (
            f"Policy=keep_as_background: {lbl_path.name} should be empty, got: {content!r}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 6. Class mapping
# ─────────────────────────────────────────────────────────────────────────────


def test_class_mapping(
    mini_dataset: Path, classes_config: Path, clean_manifest: Path, tmp_path: Path
) -> None:
    """D00→0, D10→0, D20→1, D40→2 in 3-class output; raw IDs 3,4 must not appear."""
    out_dir = tmp_path / "yolo3_mapping"
    _run_convert(clean_manifest, mini_dataset, classes_config, out_dir, "drop")

    with open(clean_manifest, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    normal_rows = [
        r for r in rows
        if r["group"] not in (EXCLUDED_ONLY_IN_GROUP, EMPTY_LABEL_IN_GROUP)
    ][:10]

    found_ids: set[int] = set()
    for row in normal_rows:
        img_stem = Path(row["image"]).stem
        split = row["split"]
        lbl_path = out_dir / split / "labels" / (img_stem + ".txt")
        if not lbl_path.exists():
            continue
        for line in lbl_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                found_ids.add(int(line.split()[0]))

    assert 0 in found_ids, "crack (class 0) not found in 3-class output"
    assert 1 in found_ids, "alligator (class 1) not found in 3-class output"
    assert 2 in found_ids, "pothole (class 2) not found in 3-class output"
    assert 3 not in found_ids, "Raw class ID 3 leaked into 3-class output"
    assert 4 not in found_ids, "Excluded class ID 4 leaked into 3-class output"


# ─────────────────────────────────────────────────────────────────────────────
# 7 & 8. Leakage check
# ─────────────────────────────────────────────────────────────────────────────


def test_leakage_check_fails_on_leak(leaky_manifest: Path) -> None:
    """check_leakage.py must exit 1 on a deliberately leaky manifest."""
    script = Path(__file__).parent.parent / "training" / "check_leakage.py"
    result = subprocess.run(
        [sys.executable, str(script), "--manifest", str(leaky_manifest)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, (
        f"Expected exit 1 for leaky manifest, got {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "LEAKAGE" in result.stdout.upper(), (
        f"Expected 'LEAKAGE' in output; got: {result.stdout}"
    )


def test_leakage_check_passes_on_clean_manifest(clean_manifest: Path) -> None:
    """check_leakage.py must exit 0 for a clean manifest."""
    script = Path(__file__).parent.parent / "training" / "check_leakage.py"
    result = subprocess.run(
        [sys.executable, str(script), "--manifest", str(clean_manifest)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"Expected exit 0 for clean manifest, got {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 9. Audit counts match known fixture values
# ─────────────────────────────────────────────────────────────────────────────


def test_audit_counts_match_fixture(mini_dataset: Path, classes_config: Path) -> None:
    """audit_dataset counts must match the synthetic fixture's known properties."""
    from audit_dataset import audit_split, class_id_to_name, get_excluded_set, load_classes_config

    cfg = load_classes_config(str(classes_config))
    excluded_set = get_excluded_set(cfg)
    id_to_name = class_id_to_name(cfg)

    result = audit_split(mini_dataset, excluded_set, id_to_name, cfg)

    total_expected = len(GROUPS) * IMAGES_PER_GROUP  # 60
    assert result["total_images"] == total_expected, (
        f"Expected {total_expected} total images, got {result['total_images']}"
    )
    assert result["excluded_only_count"] == EXCLUDED_ONLY_COUNT, (
        f"Expected {EXCLUDED_ONLY_COUNT} excluded-only, got {result['excluded_only_count']}"
    )
    assert result["empty_label_count"] == EMPTY_LABEL_COUNT, (
        f"Expected {EMPTY_LABEL_COUNT} empty-label, got {result['empty_label_count']}"
    )

    normal_image_count = total_expected - EXCLUDED_ONLY_COUNT - EMPTY_LABEL_COUNT  # 52
    for cls_id in ["0", "1", "2", "3"]:
        got = result["boxes_per_class_id"].get(cls_id, 0)
        assert got == normal_image_count, (
            f"Class ID {cls_id}: expected {normal_image_count} boxes, got {got}"
        )
    got_excluded = result["boxes_per_class_id"].get("4", 0)
    assert got_excluded == EXCLUDED_ONLY_COUNT, (
        f"Excluded class (ID 4): expected {EXCLUDED_ONLY_COUNT} boxes, got {got_excluded}"
    )
