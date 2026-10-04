#!/usr/bin/env python3
"""
Evaluate False Positives per kilometer on a verified-clean stretch.
Calculates route length from GPS log.
If data is missing, prints NOT MEASURED and exits 0.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ai-service"))
from app.evaluation import compute_fp_per_km, haversine_distance_m


def compute_route_length_km(gps_path: Path) -> float:
    points = []
    with gps_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            points.append((float(r["lat"]), float(r["lon"])))

    total_meters = 0.0
    for i in range(len(points) - 1):
        total_meters += haversine_distance_m(
            points[i][0], points[i][1], points[i + 1][0], points[i + 1][1]
        )
    return total_meters / 1000.0


def main():
    parser = argparse.ArgumentParser(description="Compute False Positives per km on a verified-clean stretch.")
    parser.add_argument("--gps", default="data/chennai/clean_stretch/gps.csv", help="Path to clean stretch GPS log")
    parser.add_argument("--detections", default="data/chennai/clean_stretch/predictions.json", help="Path to detections on clean stretch")
    args = parser.parse_args()

    gps_path = Path(args.gps)
    det_path = Path(args.detections)

    if not gps_path.exists() or not det_path.exists():
        print(f"NOT MEASURED: Clean stretch data absent (gps_exists={gps_path.exists()}, det_exists={det_path.exists()})")
        sys.exit(0)

    dist_km = compute_route_length_km(gps_path)
    if dist_km <= 0.0:
        print("NOT MEASURED: GPS track has zero or invalid distance.")
        sys.exit(0)

    with det_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    defects = data.get("defects", data) if isinstance(data, dict) else data
    fp_count = len(defects)

    fp_per_km = compute_fp_per_km(fp_count, dist_km)

    print("=" * 60)
    print("FALSE POSITIVES PER KM (CLEAN STRETCH)")
    print("=" * 60)
    print(f"Surveyed Route Distance : {dist_km:.3f} km")
    print(f"False Positive Count    : {fp_count}")
    print(f"False Positives / km    : {fp_per_km:.2f} FP/km")
    print("=" * 60)


if __name__ == "__main__":
    main()
