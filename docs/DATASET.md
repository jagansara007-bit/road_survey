# Dataset Preparation Pipeline

This document explains how to process raw CRDDC/RDD datasets into the 3-class, sequence-grouped, and audited format required for YOLO training in this system.

All scripts should be executed from the repository root via `uv run`.

## Prerequisites

Your raw dataset must be in standard YOLO format under `data/raw/` (or similar), with images and labels inside:
```
data/raw/
├── images/
│   ├── seq_a_0001.jpg
│   └── ...
└── labels/
    ├── seq_a_0001.txt
    └── ...
```

## Pipeline Steps

### 1. Grouped Split Generation
Instead of a random split, we group near-duplicate video frames to prevent train/test leakage.
```bash
uv run python training/make_split.py \
    --dataset_root data/raw \
    --group_strategy prefix \
    --output data/processed/split_manifest.csv
```
*Note: If your dataset filenames don't use prefixes (like `seq_a_`), use `--group_strategy index_window` or `--group_strategy phash`.*

### 2. Verify No Leakage
Ensure that the generated split manifest is mathematically sound and that no sequence groups straddle splits.
```bash
uv run python training/check_leakage.py \
    --manifest data/processed/split_manifest.csv
```

### 3. Excluded-Class Audit (Optional but recommended)
Discover how many images contain *only* excluded classes (like Japan-specific lane markings D44), and see how many empty label files exist.
```bash
uv run python training/audit_dataset.py \
    --dataset_root data/raw \
    --classes_config training/configs/classes.yaml \
    --excluded_only_policy drop \
    --output_dir reports
```
*Check `reports/dataset_audit.md` for the results.*

### 4. Convert to 3-Class YOLO Format
This step applies the mapping defined in `training/configs/classes.yaml`:
- `D00`, `D10` -> `crack` (class 0)
- `D20` -> `alligator` (class 1)
- `D40` -> `pothole` (class 2)
Excluded classes are dropped.

```bash
uv run python training/convert_to_3class.py \
    --manifest data/processed/split_manifest.csv \
    --dataset_root data/raw \
    --classes_config training/configs/classes.yaml \
    --excluded_only_policy drop \
    --output_dir data/processed/yolo3
```
*This produces a ready-to-train YOLO directory at `data/processed/yolo3` along with `dataset.yaml` and a `crack_origins.csv` file for the next step.*

### 5. Extract Crack Orientation Crops
To classify longitudinal (D00) vs transverse (D10) cracks, we extract image crops of the crack bounding boxes from the `train` and `val` splits.
```bash
uv run python training/make_orientation_crops.py \
    --manifest data/processed/split_manifest.csv \
    --dataset_root data/raw \
    --crack_origins data/processed/yolo3/crack_origins.csv \
    --output_dir data/processed/orientation
```

### 6. Train Orientation Baseline
Evaluate the baseline logistic regression classifier on the orientation crops.
```bash
uv run python training/orientation_baseline.py \
    --orientation_dir data/processed/orientation \
    --output_dir reports
```
*Check `reports/orientation_baseline.md` for accuracy and per-class precision/recall.*

## Final Output Structure
After running the pipeline, your `data/processed/` directory will look like this:
```
data/processed/
├── split_manifest.csv
├── yolo3/
│   ├── dataset.yaml
│   ├── crack_origins.csv
│   ├── train/
│   ├── val/
│   └── test/
└── orientation/
    ├── train/
    │   ├── longitudinal/
    │   └── transverse/
    └── val/
```
You can now proceed to **Phase 2** (YOLO training) pointing ultralytics to `data/processed/yolo3/dataset.yaml`.
