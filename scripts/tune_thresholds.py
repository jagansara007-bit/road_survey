#!/usr/bin/env python3
"""
Grid-search severity.low_max_ratio and medium_max_ratio against expert consensus.
Maximizes quadratic-weighted Cohen's kappa.
Proposes new values; NEVER overwrites thresholds.yaml automatically.
Uses a seeded held-out split; flags small sample size (N < 30) and train/report overlap.
If input data is missing, prints NOT MEASURED and exits 0.
"""
import argparse
import csv
import sys
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ai-service"))
from app.config_loader import load_thresholds
from app.evaluation import SEVERITY_ORDER, tune_severity_thresholds


def severity_to_num(sev: str) -> int:
    mapping = {"Low": 0, "Medium": 1, "High": 2}
    return mapping.get(sev.strip().capitalize(), 0)


def num_to_severity(num: float) -> str:
    rounded = round(num)
    rounded = max(0, min(2, rounded))
    return SEVERITY_ORDER[rounded]


def main():
    parser = argparse.ArgumentParser(description="Tune severity thresholds using expert ratings.")
    parser.add_argument("--ratings", default="reports/expert_rating/completed_ratings.csv", help="Path to filled rating CSV")
    parser.add_argument("--crops-metadata", default="data/crops/metadata.json", help="Path to crop metadata with area_ratio")
    parser.add_argument("--seed", type=int, default=42, help="Seed for train/test split")
    parser.add_argument("--train-ratio", type=float, default=0.7, help="Fraction for tuning split")
    args = parser.parse_args()

    ratings_path = Path(args.ratings)
    meta_path = Path(args.crops_metadata)

    if not ratings_path.exists():
        print(f"NOT MEASURED: Rating CSV '{ratings_path}' absent.")
        sys.exit(0)

    try:
        cfg = load_thresholds()
        current_low = float(cfg.get("severity", {}).get("low_max_ratio", 0.02))
        current_med = float(cfg.get("severity", {}).get("medium_max_ratio", 0.08))
    except (FileNotFoundError, KeyError, ValueError):
        current_low = 0.02
        current_med = 0.08

    # Read ratings
    rows = []
    with ratings_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if "filename" in r:
                rows.append(r)

    if not rows:
        print("NOT MEASURED: Rating CSV has 0 rows.")
        sys.exit(0)

    rater_cols = [k for k in rows[0] if k.startswith("rater_") and any(r[k].strip() for r in rows)]
    if not rater_cols:
        print("NOT MEASURED: No filled rater columns in rating CSV.")
        sys.exit(0)

    # We need area_ratio for each crop. If crops metadata exists, use it; otherwise check if 'area_ratio' is in rating CSV.
    area_ratios = {}
    if meta_path.exists():
        import json
        with meta_path.open("r", encoding="utf-8") as f:
            meta_items = json.load(f)
            for m in meta_items:
                area_ratios[Path(m["filename"]).name] = float(m.get("area_ratio", m.get("max_area_ratio", 0.0)))

    crops_data = []
    for r in rows:
        fname = Path(r["filename"]).name
        ratio = None
        if "area_ratio" in r and r["area_ratio"].strip():
            ratio = float(r["area_ratio"])
        elif fname in area_ratios:
            ratio = area_ratios[fname]

        if ratio is None:
            continue

        scores = [severity_to_num(r[k]) for k in rater_cols if r[k].strip()]
        if not scores:
            continue
        consensus = num_to_severity(median(scores))

        crops_data.append({
            "filename": fname,
            "area_ratio": ratio,
            "consensus_severity": consensus,
        })

    if not crops_data:
        print("NOT MEASURED: No valid crop samples with both area_ratio and expert ratings found.")
        sys.exit(0)

    res = tune_severity_thresholds(
        crops_data,
        current_low=current_low,
        current_medium=current_med,
        seed=args.seed,
        train_ratio=args.train_ratio,
    )

    print("=" * 65)
    print("THRESHOLD OPTIMIZATION RESULTS (SEVERITY AREA RATIO)")
    print("=" * 65)
    print(f"Total Evaluated Crops  : {res['n_samples']}")
    print(f"Tuning Split (Train)   : {res['train_size']} crops")
    print(f"Held-out Split (Test)  : {res['test_size']} crops")
    print(f"Split Random Seed      : {args.seed}")
    print()
    print("Current Baseline Thresholds:")
    print(f"  low_max_ratio        : {res['initial_thresholds']['low_max_ratio']:.4f}")
    print(f"  medium_max_ratio     : {res['initial_thresholds']['medium_max_ratio']:.4f}")
    print(f"  Baseline Kappa (Train): {res['initial_train_kappa']:+.4f}")
    print(f"  Baseline Kappa (Test) : {res['initial_test_kappa']:+.4f}")
    print()
    print("Proposed Tuned Thresholds (DO NOT OVERWRITE thresholds.yaml AUTOMATICALLY):")
    print(f"  low_max_ratio        : {res['proposed_thresholds']['low_max_ratio']:.4f}")
    print(f"  medium_max_ratio     : {res['proposed_thresholds']['medium_max_ratio']:.4f}")
    print(f"  Tuned Kappa (Train)  : {res['tuned_train_kappa']:+.4f}")
    print(f"  Tuned Kappa (Test)   : {res['tuned_test_kappa']:+.4f}")
    print()
    if res["warnings"]:
        print("WARNINGS / LIMITATIONS:")
        for w in res["warnings"]:
            print(f"  * {w}")
    else:
        print("Validation: Sample size sufficient and evaluation performed on held-out test split.")
    print("=" * 65)


if __name__ == "__main__":
    main()
