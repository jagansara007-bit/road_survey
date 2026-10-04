#!/usr/bin/env python3
"""
Evaluate detection-to-ticket time (stopwatch from upload to ranked queue) from timing logs.
If timing log CSV is missing, prints NOT MEASURED and exits 0.
"""
import argparse
import csv
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Evaluate detection-to-ticket latency.")
    parser.add_argument("--timing-log", default="data/timing/timing_log.csv", help="Path to timing log CSV")
    args = parser.parse_args()

    log_path = Path(args.timing_log)
    if not log_path.exists():
        print(f"NOT MEASURED: Timing log '{log_path}' absent.")
        sys.exit(0)

    latencies = []
    with log_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            lat = r.get("detection_to_ticket_s", r.get("latency_s"))
            if lat is not None and lat != "":
                latencies.append(float(lat))

    if not latencies:
        print("NOT MEASURED: No latency entries recorded in timing log.")
        sys.exit(0)

    avg_lat = sum(latencies) / len(latencies)
    min_lat = min(latencies)
    max_lat = max(latencies)

    print("=" * 60)
    print("DETECTION-TO-TICKET LATENCY")
    print("=" * 60)
    print(f"Runs Recorded : {len(latencies)}")
    print(f"Mean Latency  : {avg_lat:.2f} s")
    print(f"Min Latency   : {min_lat:.2f} s")
    print(f"Max Latency   : {max_lat:.2f} s")
    print("=" * 60)


if __name__ == "__main__":
    main()
