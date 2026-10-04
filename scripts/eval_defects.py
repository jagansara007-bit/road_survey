#!/usr/bin/env python3
"""
Evaluate defect detection and deduplication against ground truth.
Reports unique-defect precision, recall, F1 (per-class & overall), raw TP/FP/FN,
and pre-dedup vs post-dedup counts.
If data is missing, prints NOT MEASURED and exits 0.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ai-service"))
from app.config_loader import load_thresholds
from app.evaluation import match_predictions_to_ground_truth


def load_defects_from_csv(path: Path) -> list[dict]:
    defects = []
    with path.open(mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            defects.append({
                "defect_id": int(row.get("defect_id", len(defects) + 1)),
                "class": row.get("class", row.get("class_name", "")),
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "severity": row.get("severity", row.get("severity_note", "Low")),
            })
    return defects


def main():
    parser = argparse.ArgumentParser(description="Evaluate predicted defects against ground truth.")
    parser.add_argument("--predictions", default="data/chennai/route1/2026-10-05/predictions.json", help="Path to predictions JSON or CSV")
    parser.add_argument("--ground-truth", default="data/chennai/route1/2026-10-05/ground_truth.csv", help="Path to ground_truth.csv")
    parser.add_argument("--match-radius", type=float, default=None, help="Match radius in meters")
    args = parser.parse_args()

    pred_path = Path(args.predictions)
    gt_path = Path(args.ground_truth)

    if not pred_path.exists() or not gt_path.exists():
        print(f"NOT MEASURED: Input files absent (pred_exists={pred_path.exists()}, gt_exists={gt_path.exists()})")
        sys.exit(0)

    try:
        cfg = load_thresholds()
        match_radius = args.match_radius or float(cfg.get("verification", {}).get("match_radius_m", 10.0))
    except (FileNotFoundError, KeyError, ValueError):
        match_radius = args.match_radius or 10.0

    # Load ground truth
    ground_truth = load_defects_from_csv(gt_path)

    # Load predictions
    pre_dedup_count = 0
    predictions = []
    if pred_path.suffix.lower() == ".json":
        with pred_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            predictions = data.get("defects", [])
            pre_dedup_count = data.get("pre_dedup_detections", len(predictions))
        else:
            predictions = data
            pre_dedup_count = len(predictions)
    else:
        predictions = load_defects_from_csv(pred_path)
        pre_dedup_count = len(predictions)

    results = match_predictions_to_ground_truth(predictions, ground_truth, match_radius_m=match_radius)

    overall = results["overall"]
    print("=" * 60)
    print("UNIQUE-DEFECT EVALUATION REPORT")
    print("=" * 60)
    print(f"Match Radius          : {match_radius:.1f} m")
    print(f"Pre-dedup Detections  : {pre_dedup_count}")
    print(f"Post-dedup Unique Def : {len(predictions)} (Dedup reduction: {((pre_dedup_count - len(predictions)) / pre_dedup_count * 100.0) if pre_dedup_count else 0.0:.1f}%)")
    print(f"Ground Truth Defects  : {len(ground_truth)}")
    print(f"True Positives (TP)   : {overall['tp']}")
    print(f"False Positives (FP)  : {overall['fp']}")
    print(f"False Negatives (FN)  : {overall['fn']}")
    print(f"Precision             : {overall['precision']:.4f}")
    print(f"Recall                : {overall['recall']:.4f}")
    print(f"F1 Score              : {overall['f1']:.4f}")
    print("\nPer-Class Breakdown:")
    for cls_name, c_res in sorted(results["per_class"].items()):
        print(f"  [{cls_name}]:")
        print(f"    GT: {c_res['ground_truth']} | Pred: {c_res['predictions']} | TP: {c_res['tp']} | FP: {c_res['fp']} | FN: {c_res['fn']}")
        print(f"    Precision: {c_res['precision']:.4f} | Recall: {c_res['recall']:.4f} | F1: {c_res['f1']:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
