#!/usr/bin/env python3
"""
Validates ground truth CSV files (defect_id, class, lat, lon, severity_note).
Reports bad rows. Exits 0 if valid (or absent -> NOT MEASURED), non-zero if invalid rows are found.
"""
import argparse
import sys
from pathlib import Path

# Add ai-service to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ai-service"))
from app.config_loader import load_thresholds
from app.evaluation import validate_ground_truth_file


def main():
    parser = argparse.ArgumentParser(description="Validate ground_truth.csv")
    parser.add_argument("path", nargs="?", default="data/chennai/route1/2026-10-05/ground_truth.csv", help="Path to ground_truth.csv")
    args = parser.parse_args()

    gt_path = Path(args.path)
    if not gt_path.exists():
        print(f"NOT MEASURED: Ground truth file '{gt_path}' does not exist.")
        sys.exit(0)

    try:
        cfg = load_thresholds()
        valid_classes = set(cfg.get("detector", {}).get("classes", ["crack", "alligator_crack", "pothole"]))
    except (FileNotFoundError, KeyError, ValueError):
        valid_classes = {"crack", "alligator_crack", "pothole", "D00", "D10", "D20", "D40"}

    errors = validate_ground_truth_file(gt_path, valid_classes=valid_classes)
    if errors:
        print(f"FAILED: Found {len(errors)} validation errors in '{gt_path}':")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print(f"VALID: '{gt_path}' adheres to the ground truth schema.")
        sys.exit(0)


if __name__ == "__main__":
    main()
