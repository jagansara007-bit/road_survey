#!/usr/bin/env python3
"""
Evaluate expert rating agreement using quadratic-weighted Cohen's kappa.
Computes:
  - System vs. each expert
  - System vs. median consensus
  - Expert-expert pairwise agreement
  - 3x3 confusion matrix
Handles degenerate cases explicitly without crashing.
If data is missing, prints NOT MEASURED and exits 0.
"""
import argparse
import csv
import sys
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ai-service"))
from app.evaluation import SEVERITY_ORDER, compute_quadratic_weighted_cohen_kappa


def severity_to_num(sev: str) -> int:
    mapping = {"Low": 0, "Medium": 1, "High": 2}
    return mapping.get(sev.strip().capitalize(), 0)


def num_to_severity(num: float) -> str:
    rounded = round(num)
    rounded = max(0, min(2, rounded))
    return SEVERITY_ORDER[rounded]


def main():
    parser = argparse.ArgumentParser(description="Compute quadratic-weighted Cohen's kappa for severity ratings.")
    parser.add_argument("--ratings", default="reports/expert_rating/completed_ratings.csv", help="Path to filled rating sheet CSV")
    args = parser.parse_args()

    ratings_path = Path(args.ratings)
    if not ratings_path.exists():
        print(f"NOT MEASURED: Expert rating CSV '{ratings_path}' absent.")
        sys.exit(0)

    rows = []
    with ratings_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if "system_severity" in r:
                rows.append(r)

    if not rows:
        print("NOT MEASURED: Rating CSV contains 0 rows.")
        sys.exit(0)

    # Detect available raters
    first = rows[0]
    rater_cols = [k for k in first if k.startswith("rater_") and any(r[k].strip() for r in rows)]

    if not rater_cols:
        print("NOT MEASURED: No filled rater columns found in CSV.")
        sys.exit(0)

    system_ratings = [r["system_severity"].strip().capitalize() for r in rows]

    print("=" * 65)
    print("EXPERT SEVERITY AGREEMENT (QUADRATIC-WEIGHTED COHEN'S KAPPA)")
    print("=" * 65)
    print(f"Number of Rated Crops : {len(rows)}")
    print(f"Identified Experts     : {', '.join(rater_cols)}")
    print()

    # System vs each expert
    expert_ratings = {}
    for r_col in rater_cols:
        vals = [r[r_col].strip().capitalize() for r in rows]
        expert_ratings[r_col] = vals
        k_val, note, _ = compute_quadratic_weighted_cohen_kappa(system_ratings, vals)
        if k_val is not None:
            print(f"  System vs {r_col:<10} : kappa = {k_val:+.4f}")
        else:
            print(f"  System vs {r_col:<10} : kappa = UNDEFINED ({note})")

    # System vs Median Consensus
    consensus_ratings = []
    for i in range(len(rows)):
        scores = [severity_to_num(expert_ratings[r_col][i]) for r_col in rater_cols]
        consensus_ratings.append(num_to_severity(median(scores)))

    k_cons, cons_note, matrix = compute_quadratic_weighted_cohen_kappa(system_ratings, consensus_ratings)
    print()
    if k_cons is not None:
        print(f"  System vs Consensus    : kappa = {k_cons:+.4f}")
    else:
        print(f"  System vs Consensus    : kappa = UNDEFINED ({cons_note})")

    # Expert-Expert Pairwise
    if len(rater_cols) > 1:
        print("\nInter-Expert Agreement:")
        for i in range(len(rater_cols)):
            for j in range(i + 1, len(rater_cols)):
                r1, r2 = rater_cols[i], rater_cols[j]
                k_pair, pair_note, _ = compute_quadratic_weighted_cohen_kappa(expert_ratings[r1], expert_ratings[r2])
                if k_pair is not None:
                    print(f"  {r1} vs {r2:<10} : kappa = {k_pair:+.4f}")
                else:
                    print(f"  {r1} vs {r2:<10} : kappa = UNDEFINED ({pair_note})")

    # 3x3 Confusion Matrix (System vs Consensus)
    print("\nConfusion Matrix (System vs Consensus):")
    print(f"{'':>12} | {'Cons Low':>10} | {'Cons Med':>10} | {'Cons High':>10} |")
    print("-" * 52)
    labels = ["Low", "Medium", "High"]
    for row_idx, label in enumerate(labels):
        print(f"  Sys {label:<6} | {matrix[row_idx][0]:>10} | {matrix[row_idx][1]:>10} | {matrix[row_idx][2]:>10} |")
    print("=" * 65)


if __name__ == "__main__":
    main()
