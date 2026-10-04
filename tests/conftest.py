"""tests/conftest.py

Synthetic mini-dataset fixture for Phase 1 tests.

Generates ~60 tiny (32x32) PNG images with YOLO-format .txt label files.
Structure mirrors a CRDDC dataset with known properties:
    - 5 sequence groups (seq_a ... seq_e), 12 images each
    - Groups seq_a...seq_c -> train,  seq_d -> val,  seq_e -> test  (via make_split)
    - 5 images in seq_a that contain ONLY excluded-class boxes (D44)
    - 3 images in seq_b with EMPTY label files
    - Remaining images have boxes from D00, D10, D20, D40

Class IDs used in label files (integer format expected by YOLO):
    0 = D00   1 = D10   2 = D20   3 = D40   4 = D44  (excluded)

All images are 32x32 black PNGs - enough for PIL operations.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest
import yaml
from PIL import Image

# Make training/ importable from any pytest invocation path
_TRAINING_DIR = str(Path(__file__).parent.parent / "training")
if _TRAINING_DIR not in sys.path:
    sys.path.insert(0, _TRAINING_DIR)


# ── constants ─────────────────────────────────────────────────────────────────
GROUPS = ["groupa", "groupb", "groupc", "groupd", "groupe"]
IMAGES_PER_GROUP = 12
EXCLUDED_ONLY_IN_GROUP = "groupa"
EXCLUDED_ONLY_COUNT = 5          # first 5 images of groupa are excluded-only
EMPTY_LABEL_IN_GROUP = "groupb"
EMPTY_LABEL_COUNT = 3            # first 3 images of groupb have empty labels

# Normal label template: one box per active class per image
NORMAL_BOXES = [
    "0 0.5 0.5 0.3 0.2",   # D00 longitudinal crack
    "1 0.3 0.4 0.2 0.4",   # D10 transverse crack
    "2 0.7 0.6 0.25 0.3",  # D20 alligator
    "3 0.2 0.8 0.3 0.15",  # D40 pothole
]

EXCLUDED_BOX = "4 0.5 0.5 0.4 0.4"  # D44 – excluded


# ── fixture ───────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def mini_dataset(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a synthetic mini-dataset under a temp directory.

    Returns the dataset root path.  The dataset has a flat images/ and
    labels/ structure (all images together, no pre-assigned splits).
    """
    root = tmp_path_factory.mktemp("mini_dataset")
    img_dir = root / "images"
    lbl_dir = root / "labels"
    img_dir.mkdir()
    lbl_dir.mkdir()

    for group in GROUPS:
        for i in range(IMAGES_PER_GROUP):
            img_name = f"{group}_{i:04d}.png"
            img_path = img_dir / img_name
            lbl_path = lbl_dir / (Path(img_name).stem + ".txt")

            # Create tiny black image
            Image.new("RGB", (32, 32), color=(0, 0, 0)).save(img_path)

            # Determine label content
            if group == EXCLUDED_ONLY_IN_GROUP and i < EXCLUDED_ONLY_COUNT:
                lbl_path.write_text(EXCLUDED_BOX + "\n", encoding="utf-8")
            elif group == EMPTY_LABEL_IN_GROUP and i < EMPTY_LABEL_COUNT:
                lbl_path.write_text("", encoding="utf-8")
            else:
                lbl_path.write_text("\n".join(NORMAL_BOXES) + "\n", encoding="utf-8")

    return root


@pytest.fixture(scope="session")
def classes_config(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Write a minimal classes.yaml and return its path."""
    cfg = {
        "active_classes": {"D00": "Longitudinal Crack", "D10": "Transverse Crack",
                           "D20": "Alligator Crack", "D40": "Pothole"},
        "excluded_classes": ["D44", "D01", "D43", "D11", "D50", "D0w0"],
        "three_class_mapping": {"D00": 0, "D10": 0, "D20": 1, "D40": 2},
        "three_class_names": {0: "crack", 1: "alligator", 2: "pothole"},
        "nc": 3,
        "names": ["crack", "alligator", "pothole"],
        # id_map: integer label id -> class name (as stored in .txt files)
        "id_map": {0: "D00", 1: "D10", 2: "D20", 3: "D40", 4: "D44"},
    }
    cfg_dir = tmp_path_factory.mktemp("cfg")
    cfg_path = cfg_dir / "classes.yaml"
    cfg_path.write_text(yaml.dump(cfg), encoding="utf-8")
    return cfg_path


@pytest.fixture(scope="session")
def clean_manifest(mini_dataset: Path, classes_config: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Run make_split on the mini dataset and return the manifest path."""
    from make_split import group_by_prefix, make_split

    img_dir = mini_dataset / "images"
    exts = {".png", ".jpg", ".jpeg"}
    images = sorted(p for p in img_dir.iterdir() if p.suffix.lower() in exts)

    rows = make_split(images, group_by_prefix, {}, 0.70, 0.15, seed=42)

    out_dir = tmp_path_factory.mktemp("manifests")
    manifest_path = out_dir / "split_manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["image", "group", "split"])
        writer.writerows(rows)

    return manifest_path


@pytest.fixture(scope="session")
def leaky_manifest(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Deliberately leaky manifest: group 'groupa' appears in both train and val."""
    out_dir = tmp_path_factory.mktemp("leaky")
    manifest_path = out_dir / "leaky_manifest.csv"
    rows = [
        ["image", "group", "split"],
        ["groupa_0000.png", "groupa", "train"],
        ["groupa_0001.png", "groupa", "val"],   # same group, different split -> leak
        ["groupb_0000.png", "groupb", "train"],
        ["groupc_0000.png", "groupc", "test"],
    ]
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return manifest_path
