#!/usr/bin/env python3
"""
Evaluate repair verification accuracy against ground-truth repair manifests.
Outputs overall status accuracy and confusion matrix over Open/Repaired/Failed/New/unverified.
If data is missing, prints NOT MEASURED and exits 0.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ai-service"))
from app.evaluation import evaluate_repair_verification


def load_manifest(path: Path) -> list[dict]:
    items = []
    with path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            items.append({
                "defect_id": int(r.get("defect_id", len(items) + 1)),
                "actual_status": r.get("actual_status", r.get("status", "Open")).strip(),
                "class": r.get("class", ""),
                "lat": float(r.get("lat", 0.0)),
                "lon": float(r.get("lon", 0.0)),
            })
    return items


def main():
    parser = argparse.ArgumentParser(description="Evaluate repair verification accuracy.")
    parser.add_argument("--resurvey-predictions", default="data/chennai/resurvey/predictions.json", help="Resurvey predictions with verified statuses")
    parser.add_argument("--repair-manifest", default="data/chennai/resurvey/repaired_spots.csv", help="Known ground-truth repair manifest CSV")
    args = parser.parse_args()

    pred_path = Path(args.resurvey_predictions)
    manifest_path = Path(args.repair_manifest)

    if not pred_path.exists() or not manifest_path.exists():
        print(f"NOT MEASURED: Verification evaluation inputs absent (pred_exists={pred_path.exists()}, manifest_exists={manifest_path.exists()})")
        sys.exit(0)

    # Load predictions
    with pred_path.open("r", encoding="utf-8") as f:
        pred_data = json.load(f)
    predictions = pred_data.get("defects", pred_data) if isinstance(pred_data, dict) else pred_data

    # Load manifest
    manifest = load_manifest(manifest_path)

    results = evaluate_repair_verification(predictions, manifest)

    cats = results["categories"]
    matrix = results["confusion_matrix"]

    print("=" * 65)
    print("REPAIR VERIFICATION EVALUATION REPORT")
    print("=" * 65)
    print(f"Evaluated Defects   : {results['total']}")
    print(f"Correctly Classified: {results['correct']}")
    print(f"Status Accuracy     : {results['accuracy'] * 100.0:.2f}%")
    print("\nConfusion Matrix (Rows = Actual GT, Cols = Predicted Status):")
    actual_pred_label = "Actual \\ Pred"
    header = f"{actual_pred_label:>14} | " + " | ".join(f"{c:>10}" for c in cats) + " |"
    print(header)
    print("-" * len(header))
    for r_idx, cat in enumerate(cats):
        row_str = f"{cat:>14} | " + " | ".join(f"{matrix[r_idx][c_idx]:>10}" for c_idx in range(len(cats))) + " |"
        print(row_str)
    print("=" * 65)


if __name__ == "__main__":
    main()
