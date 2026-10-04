#!/usr/bin/env python3
"""
Evaluate survey throughput (km/hour) for automated pipeline vs manual survey from timing logs.
If timing log CSV is missing, prints NOT MEASURED and exits 0.
"""
import argparse
import csv
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Evaluate survey throughput (km/h vs manual).")
    parser.add_argument("--timing-log", default="data/timing/timing_log.csv", help="Path to timing log CSV")
    args = parser.parse_args()

    log_path = Path(args.timing_log)
    if not log_path.exists():
        print(f"NOT MEASURED: Timing log '{log_path}' absent.")
        sys.exit(0)

    rows = []
    with log_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if "route_distance_km" in r and ("automated_time_s" in r or "automated_duration_s" in r):
                rows.append(r)

    if not rows:
        print("NOT MEASURED: No valid survey timing rows found in log.")
        sys.exit(0)

    auto_speeds = []
    manual_speeds = []

    for r in rows:
        dist_km = float(r["route_distance_km"])
        auto_sec = float(r.get("automated_time_s", r.get("automated_duration_s", 0)))
        if auto_sec > 0:
            auto_speeds.append(dist_km / (auto_sec / 3600.0))

        manual_sec = float(r.get("manual_time_s", r.get("manual_duration_s", 0)))
        if manual_sec > 0:
            manual_speeds.append(dist_km / (manual_sec / 3600.0))

    avg_auto = sum(auto_speeds) / len(auto_speeds) if auto_speeds else 0.0
    avg_manual = sum(manual_speeds) / len(manual_speeds) if manual_speeds else 0.0
    speedup = (avg_auto / avg_manual) if avg_manual > 0 else 0.0

    print("=" * 60)
    print("SURVEY THROUGHPUT COMPARISON")
    print("=" * 60)
    print(f"Surveys Analyzed        : {len(rows)}")
    print(f"Automated Pipeline Speed: {avg_auto:.2f} km/h")
    print(f"Manual Survey Speed     : {avg_manual:.2f} km/h" if avg_manual > 0 else "Manual Survey Speed     : NOT RECORDED")
    if speedup > 0:
        print(f"Speedup Factor          : {speedup:.1f}x faster than manual walking survey")
    print("=" * 60)


if __name__ == "__main__":
    main()
