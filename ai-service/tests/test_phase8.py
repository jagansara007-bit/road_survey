"""
Comprehensive unit tests for Phase 8 metrics, evaluation algorithms, and edge cases.
"""
from __future__ import annotations

import csv
import tempfile
from pathlib import Path

import pytest
from app.evaluation import (
    compute_fp_per_km,
    compute_quadratic_weighted_cohen_kappa,
    evaluate_repair_verification,
    haversine_distance_m,
    match_predictions_to_ground_truth,
    tune_severity_thresholds,
    validate_ground_truth_file,
)
from sklearn.metrics import cohen_kappa_score


def test_haversine_distance():
    # Distance between same points is 0
    assert haversine_distance_m(13.0827, 80.2707, 13.0827, 80.2707) == 0.0
    # Approx 111 km per degree latitude
    d = haversine_distance_m(13.0, 80.0, 14.0, 80.0)
    assert 110000.0 < d < 112000.0


def test_validate_ground_truth_valid():
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", newline="") as tmp:
        writer = csv.writer(tmp)
        writer.writerow(["defect_id", "class", "lat", "lon", "severity_note"])
        writer.writerow([1, "pothole", 13.0827, 80.2707, "Deep pothole"])
        writer.writerow([2, "crack", 13.0828, 80.2708, "Longitudinal"])
        tmp_path = Path(tmp.name)

    try:
        errors = validate_ground_truth_file(tmp_path, valid_classes={"pothole", "crack"})
        assert errors == []
    finally:
        tmp_path.unlink()


def test_validate_ground_truth_corrupt():
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", newline="") as tmp:
        writer = csv.writer(tmp)
        writer.writerow(["wrong", "header", "lat", "lon", "note"])
        writer.writerow(["bad_id", "unknown_class", 999.0, "not_lon", ""])
        tmp_path = Path(tmp.name)

    try:
        errors = validate_ground_truth_file(tmp_path, valid_classes={"pothole", "crack"})
        assert len(errors) > 0
        assert any("Invalid header" in e for e in errors)
    finally:
        tmp_path.unlink()


def test_defect_matching_hand_computable():
    """
    Hand-computable case:
    10 Ground Truth defects (at base coordinates).
    8 Predicted defects:
      - 7 land within 5m of GT defects with matching class (TP=7).
      - 1 prediction lands > 50m away (FP=1).
      - 3 GT defects have no predictions nearby (FN=3).
    Expected:
      TP = 7
      FP = 1
      FN = 3
      Precision = 7 / (7 + 1) = 7/8 = 0.875
      Recall = 7 / (7 + 3) = 7/10 = 0.700
      F1 = 2 * 0.875 * 0.7 / (0.875 + 0.7) = 1.225 / 1.575 = 0.777777...
    """
    gt = [
        {"defect_id": i, "class": "pothole", "lat": 13.0800 + i * 0.001, "lon": 80.2700}
        for i in range(1, 11)
    ]

    preds = [
        # 7 close predictions (~1m offset)
        {"defect_id": i, "class": "pothole", "lat": 13.0800 + i * 0.001 + 0.00001, "lon": 80.2700}
        for i in range(1, 8)
    ] + [
        # 1 false positive far away
        {"defect_id": 99, "class": "pothole", "lat": 13.0700, "lon": 80.2700}
    ]

    res = match_predictions_to_ground_truth(preds, gt, match_radius_m=10.0)
    overall = res["overall"]

    assert overall["tp"] == 7
    assert overall["fp"] == 1
    assert overall["fn"] == 3
    assert abs(overall["precision"] - 0.875) < 1e-6
    assert abs(overall["recall"] - 0.700) < 1e-6
    assert abs(overall["f1"] - (1.225 / 1.575)) < 1e-6


def test_defect_matching_degenerate_cases():
    # 0 predictions, 5 GT
    gt = [{"defect_id": 1, "class": "pothole", "lat": 13.0, "lon": 80.0}] * 5
    res = match_predictions_to_ground_truth([], gt)
    assert res["overall"]["tp"] == 0
    assert res["overall"]["fp"] == 0
    assert res["overall"]["fn"] == 5
    assert res["overall"]["precision"] == 0.0
    assert res["overall"]["recall"] == 0.0

    # 5 predictions, 0 GT
    preds = [{"defect_id": 1, "class": "pothole", "lat": 13.0, "lon": 80.0}] * 5
    res2 = match_predictions_to_ground_truth(preds, [])
    assert res2["overall"]["tp"] == 0
    assert res2["overall"]["fp"] == 5
    assert res2["overall"]["fn"] == 0
    assert res2["overall"]["precision"] == 0.0
    assert res2["overall"]["recall"] == 0.0

    # Class mismatch at exact same coordinates
    p = [{"defect_id": 1, "class": "crack", "lat": 13.0, "lon": 80.0}]
    g = [{"defect_id": 1, "class": "pothole", "lat": 13.0, "lon": 80.0}]
    res3 = match_predictions_to_ground_truth(p, g, match_radius_m=10.0)
    assert res3["overall"]["tp"] == 0
    assert res3["overall"]["fp"] == 1
    assert res3["overall"]["fn"] == 1


def test_compute_fp_per_km():
    assert compute_fp_per_km(5, 2.5) == 2.0
    assert compute_fp_per_km(0, 5.0) == 0.0
    assert compute_fp_per_km(10, 0.0) == 0.0


def test_cohen_kappa_matches_sklearn_textbook():
    """
    Known dataset:
    Verify quadratic-weighted kappa matches sklearn exactly (within 1e-9).
    """
    rater1 = ["Low", "Low", "Medium", "Medium", "High", "High", "Medium", "Low", "High", "Medium"]
    rater2 = ["Low", "Medium", "Medium", "Medium", "High", "Medium", "Medium", "Low", "High", "High"]

    my_kappa, note, _matrix = compute_quadratic_weighted_cohen_kappa(rater1, rater2)
    assert note is None
    assert my_kappa is not None

    mapping = {"Low": 0, "Medium": 1, "High": 2}
    y1 = [mapping[r] for r in rater1]
    y2 = [mapping[r] for r in rater2]
    sk_kappa = cohen_kappa_score(y1, y2, weights="quadratic", labels=[0, 1, 2])

    assert abs(my_kappa - sk_kappa) < 1e-9


def test_cohen_kappa_degenerate_cases():
    # 1. Identical ratings with variation -> kappa is 1.0 (perfect agreement)
    r1 = ["Low", "Medium", "High", "Low"]
    r2 = ["Low", "Medium", "High", "Low"]
    k, _note, _ = compute_quadratic_weighted_cohen_kappa(r1, r2)
    assert abs(k - 1.0) < 1e-9

    # 2. All ratings in a single category -> undefined, handled without crashing
    all_low1 = ["Low", "Low", "Low", "Low"]
    all_low2 = ["Low", "Low", "Low", "Low"]
    k_undef, note_undef, mat = compute_quadratic_weighted_cohen_kappa(all_low1, all_low2)
    assert k_undef is None
    assert "Undefined" in note_undef
    assert mat[0][0] == 4

    # 3. Unequal length -> raises ValueError
    with pytest.raises(ValueError):
        compute_quadratic_weighted_cohen_kappa(["Low"], ["Low", "High"])


def test_tune_severity_thresholds_logic():
    # Synthetic crops with clear area_ratio cutoffs:
    # 0.01 -> Low, 0.05 -> Medium, 0.12 -> High
    crops = []
    for _ in range(12):
        crops.append({"filename": "c_low.jpg", "area_ratio": 0.01, "consensus_severity": "Low"})
    for _ in range(12):
        crops.append({"filename": "c_med.jpg", "area_ratio": 0.05, "consensus_severity": "Medium"})
    for _ in range(12):
        crops.append({"filename": "c_high.jpg", "area_ratio": 0.12, "consensus_severity": "High"})

    res = tune_severity_thresholds(crops, current_low=0.02, current_medium=0.08, seed=42)
    assert res["n_samples"] == 36
    assert res["proposed_thresholds"]["low_max_ratio"] < res["proposed_thresholds"]["medium_max_ratio"]
    assert res["tuned_train_kappa"] >= res["initial_train_kappa"]


def test_tune_severity_thresholds_small_sample_warning():
    crops = [
        {"filename": "c1.jpg", "area_ratio": 0.01, "consensus_severity": "Low"},
        {"filename": "c2.jpg", "area_ratio": 0.05, "consensus_severity": "Medium"},
    ]
    res = tune_severity_thresholds(crops, seed=42)
    assert any("too small" in w for w in res["warnings"])


def test_evaluate_repair_verification():
    gt_manifest = [
        {"defect_id": 1, "actual_status": "Repaired"},
        {"defect_id": 2, "actual_status": "Open"},
        {"defect_id": 3, "actual_status": "Failed"},
        {"defect_id": 4, "actual_status": "New"},
    ]
    preds = [
        {"defect_id": 1, "status": "Repaired"},
        {"defect_id": 2, "status": "Open"},
        {"defect_id": 3, "actual_status": "Failed", "status": "Failed"},
        {"defect_id": 4, "status": "Open"},  # Wrong (should be New)
    ]
    res = evaluate_repair_verification(preds, gt_manifest)
    assert res["total"] == 4
    assert res["correct"] == 3
    assert res["accuracy"] == 0.75
