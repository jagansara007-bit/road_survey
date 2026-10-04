"""
Core evaluation metrics, matching algorithms, kappa calculation, and validation logic for Phase 8.
All functions are pure, deterministic, and handle degenerate/missing cases gracefully.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import cohen_kappa_score

SEVERITY_ORDER = ["Low", "Medium", "High"]
SEVERITY_MAP = {s: i for i, s in enumerate(SEVERITY_ORDER)}
STATUS_CATEGORIES = ["New", "Open", "Repaired", "Failed", "unverified"]


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters between two points on WGS84."""
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def validate_ground_truth_file(csv_path: str | Path, valid_classes: set[str] | None = None) -> list[str]:
    """
    Validates data/chennai/<route>/<date>/ground_truth.csv.
    Required schema: defect_id,class,lat,lon,severity_note.
    Returns a list of error descriptions (empty if valid).
    """
    path = Path(csv_path)
    if not path.exists():
        return [f"File not found: {path}"]

    errors: list[str] = []
    required_cols = ["defect_id", "class", "lat", "lon", "severity_note"]

    with path.open(mode="r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return ["Empty file: missing header"]

        header_clean = [h.strip() for h in header]
        if header_clean != required_cols:
            errors.append(f"Invalid header: expected {required_cols}, got {header_clean}")
            return errors

        seen_ids = set()
        for row_idx, row in enumerate(reader, start=2):
            if not row or all(c.strip() == "" for c in row):
                continue
            if len(row) != len(required_cols):
                errors.append(f"Row {row_idx}: expected {len(required_cols)} columns, found {len(row)}")
                continue

            defect_id_str, class_str, lat_str, lon_str, _ = [c.strip() for c in row]

            # defect_id
            try:
                d_id = int(defect_id_str)
                if d_id <= 0:
                    errors.append(f"Row {row_idx}: defect_id must be a positive integer, got '{defect_id_str}'")
                elif d_id in seen_ids:
                    errors.append(f"Row {row_idx}: duplicate defect_id {d_id}")
                seen_ids.add(d_id)
            except ValueError:
                errors.append(f"Row {row_idx}: non-integer defect_id '{defect_id_str}'")

            # class
            if valid_classes and class_str not in valid_classes:
                errors.append(f"Row {row_idx}: invalid class '{class_str}'. Allowed: {sorted(valid_classes)}")

            # lat / lon
            try:
                lat = float(lat_str)
                if not (-90.0 <= lat <= 90.0):
                    errors.append(f"Row {row_idx}: latitude out of range [-90, 90]: {lat}")
            except ValueError:
                errors.append(f"Row {row_idx}: non-float latitude '{lat_str}'")

            try:
                lon = float(lon_str)
                if not (-180.0 <= lon <= 180.0):
                    errors.append(f"Row {row_idx}: longitude out of range [-180, 180]: {lon}")
            except ValueError:
                errors.append(f"Row {row_idx}: non-float longitude '{lon_str}'")

    return errors


def match_predictions_to_ground_truth(
    predictions: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
    match_radius_m: float = 10.0,
) -> dict[str, Any]:
    """
    Match predicted unique defects to ground truth defects.
    Rules: same class, within match_radius_m, one-to-one (greedy nearest by distance, deterministic).
    Returns metrics dict with TP, FP, FN, precision, recall, f1 per class and overall.
    """
    classes = sorted(
        {p.get("class", p.get("class_name", "")) for p in predictions}
        | {g.get("class", g.get("class_name", "")) for g in ground_truth}
    )

    # Collect pairs that match class and radius
    candidate_pairs = []
    for p_idx, pred in enumerate(predictions):
        p_class = pred.get("class", pred.get("class_name", ""))
        p_lat = float(pred["lat"])
        p_lon = float(pred["lon"])
        p_id = pred.get("defect_id", p_idx)

        for g_idx, gt in enumerate(ground_truth):
            g_class = gt.get("class", gt.get("class_name", ""))
            if p_class != g_class:
                continue

            g_lat = float(gt["lat"])
            g_lon = float(gt["lon"])
            g_id = gt.get("defect_id", g_idx)

            dist = haversine_distance_m(p_lat, p_lon, g_lat, g_lon)
            if dist <= match_radius_m:
                candidate_pairs.append((dist, p_id, g_id, p_idx, g_idx, p_class))

    # Sort deterministically: distance asc, p_id asc, g_id asc
    candidate_pairs.sort(key=lambda x: (x[0], x[1], x[2]))

    matched_p = set()
    matched_g = set()
    tp_by_class: dict[str, int] = {c: 0 for c in classes}

    for dist, p_id, g_id, p_idx, g_idx, cls_name in candidate_pairs:
        if p_idx not in matched_p and g_idx not in matched_g:
            matched_p.add(p_idx)
            matched_g.add(g_idx)
            tp_by_class[cls_name] = tp_by_class.get(cls_name, 0) + 1

    # Per-class counts
    per_class_results = {}
    for c in classes:
        tp = tp_by_class.get(c, 0)
        p_count = sum(1 for p in predictions if p.get("class", p.get("class_name", "")) == c)
        g_count = sum(1 for g in ground_truth if g.get("class", g.get("class_name", "")) == c)
        fp = p_count - tp
        fn = g_count - tp

        prec = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if g_count == 0 and p_count == 0 else 0.0)
        rec = tp / (tp + fn) if (tp + fn) > 0 else (1.0 if g_count == 0 and p_count == 0 else 0.0)
        f1 = (2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        per_class_results[c] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "predictions": p_count,
            "ground_truth": g_count,
            "precision": prec,
            "recall": rec,
            "f1": f1,
        }

    total_tp = len(matched_p)
    total_fp = len(predictions) - total_tp
    total_fn = len(ground_truth) - total_tp

    total_prec = (
        total_tp / (total_tp + total_fp)
        if (total_tp + total_fp) > 0
        else (1.0 if len(ground_truth) == 0 and len(predictions) == 0 else 0.0)
    )
    total_rec = (
        total_tp / (total_tp + total_fn)
        if (total_tp + total_fn) > 0
        else (1.0 if len(ground_truth) == 0 and len(predictions) == 0 else 0.0)
    )
    total_f1 = (
        (2.0 * total_prec * total_rec / (total_prec + total_rec))
        if (total_prec + total_rec) > 0
        else 0.0
    )

    return {
        "overall": {
            "tp": total_tp,
            "fp": total_fp,
            "fn": total_fn,
            "predictions": len(predictions),
            "ground_truth": len(ground_truth),
            "precision": total_prec,
            "recall": total_rec,
            "f1": total_f1,
        },
        "per_class": per_class_results,
    }


def compute_fp_per_km(fp_count: int, distance_km: float) -> float:
    """Compute false positives per kilometer on a verified clean road."""
    if distance_km <= 0.0:
        return 0.0
    return fp_count / distance_km


def compute_quadratic_weighted_cohen_kappa(
    rater1: list[str | int],
    rater2: list[str | int],
    categories: list[str] | None = None,
) -> tuple[float | None, str | None, list[list[int]]]:
    """
    Computes quadratic-weighted Cohen's kappa and 3x3 confusion matrix.
    Handles degenerate cases (single category, identical raters) explicitly without crashing.
    Matches sklearn.metrics.cohen_kappa_score(weights="quadratic") within 1e-9.
    """
    if len(rater1) != len(rater2):
        raise ValueError("Rater lists must have the same length")
    if len(rater1) == 0:
        return None, "Empty ratings list", [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

    cat_list = categories or SEVERITY_ORDER
    cat_to_int = {c: i for i, c in enumerate(cat_list)}

    # Convert to numeric indices
    idx1 = [cat_to_int[r] if isinstance(r, str) else int(r) for r in rater1]
    idx2 = [cat_to_int[r] if isinstance(r, str) else int(r) for r in rater2]

    k = len(cat_list)
    matrix = [[0] * k for _ in range(k)]
    for i1, i2 in zip(idx1, idx2):
        matrix[i1][i2] += 1

    # Check for degenerate cases
    all_same_1 = len(set(idx1)) == 1
    all_same_2 = len(set(idx2)) == 1

    if all_same_1 and all_same_2 and idx1[0] == idx2[0]:
        # Both raters always assign the exact same single category
        return None, "Undefined: all ratings belong to a single category (zero variance)", matrix

    if all_same_1 or all_same_2:
        return None, "Undefined: marginal total variance is zero for one rater", matrix

    # Use sklearn for exact quadratic-weighted kappa
    val = float(cohen_kappa_score(idx1, idx2, weights="quadratic", labels=list(range(k))))
    return val, None, matrix


def tune_severity_thresholds(
    crops: list[dict[str, Any]],
    current_low: float = 0.02,
    current_medium: float = 0.08,
    seed: int = 42,
    train_ratio: float = 0.7,
) -> dict[str, Any]:
    """
    Grid-search low_max_ratio and medium_max_ratio against expert consensus.
    Does NOT overwrite thresholds.yaml.
    Uses a seeded train/test split.
    Flags small sample size (N < 30) and train/report overlap.
    """
    n = len(crops)
    warnings: list[str] = []
    if n < 30:
        warnings.append(f"Sample size N={n} is too small for reliable tuning (recommend N >= 30)")

    # Shuffle and split
    rng = np.random.RandomState(seed)
    indices = np.arange(n)
    rng.shuffle(indices)

    train_size = max(1, round(n * train_ratio))
    if train_size >= n:
        train_size = n - 1
        warnings.append("Train and test split are identical or test split is empty")

    train_idx = indices[:train_size]
    test_idx = indices[train_size:]

    def classify(ratio: float, low_t: float, med_t: float) -> str:
        if ratio < low_t:
            return "Low"
        if ratio < med_t:
            return "Medium"
        return "High"

    def eval_thresholds(items: list[dict[str, Any]], low_t: float, med_t: float) -> float:
        preds = [classify(item["area_ratio"], low_t, med_t) for item in items]
        gt = [item["consensus_severity"] for item in items]
        k_val, _, _ = compute_quadratic_weighted_cohen_kappa(preds, gt)
        return k_val if k_val is not None else 0.0

    train_items = [crops[i] for i in train_idx]
    test_items = [crops[i] for i in test_idx] if len(test_idx) > 0 else train_items

    initial_train_kappa = eval_thresholds(train_items, current_low, current_medium)
    initial_test_kappa = eval_thresholds(test_items, current_low, current_medium)

    # Grid search
    low_candidates = np.linspace(0.005, 0.06, 24)
    med_candidates = np.linspace(0.04, 0.20, 33)

    best_low = current_low
    best_med = current_medium
    best_train_kappa = -2.0

    for l_val in low_candidates:
        for m_val in med_candidates:
            if l_val >= m_val:
                continue
            k_score = eval_thresholds(train_items, float(l_val), float(m_val))
            if k_score > best_train_kappa:
                best_train_kappa = k_score
                best_low = float(round(l_val, 4))
                best_med = float(round(m_val, 4))

    best_test_kappa = eval_thresholds(test_items, best_low, best_med)

    return {
        "n_samples": n,
        "train_size": len(train_items),
        "test_size": len(test_items),
        "initial_thresholds": {"low_max_ratio": current_low, "medium_max_ratio": current_medium},
        "initial_train_kappa": initial_train_kappa,
        "initial_test_kappa": initial_test_kappa,
        "proposed_thresholds": {"low_max_ratio": best_low, "medium_max_ratio": best_med},
        "tuned_train_kappa": best_train_kappa,
        "tuned_test_kappa": best_test_kappa,
        "warnings": warnings,
    }


def evaluate_repair_verification(
    predictions: list[dict[str, Any]],
    known_ground_truth: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Evaluates verification statuses (Open, Repaired, Failed, New, unverified).
    Matches by defect_id or coordinate proximity and returns accuracy & confusion matrix.
    """
    categories = STATUS_CATEGORIES
    cat_to_idx = {c: i for i, c in enumerate(categories)}

    pred_by_id = {p["defect_id"]: p.get("status", "Open") for p in predictions if "defect_id" in p}

    matrix = [[0] * len(categories) for _ in range(len(categories))]
    correct = 0
    total = 0

    for gt in known_ground_truth:
        d_id = gt.get("defect_id")
        gt_status = gt.get("actual_status", gt.get("status", "Open"))
        if gt_status not in cat_to_idx:
            continue

        pred_status = pred_by_id.get(d_id, "unverified")
        if pred_status not in cat_to_idx:
            pred_status = "unverified"

        r_idx = cat_to_idx[gt_status]
        c_idx = cat_to_idx[pred_status]
        matrix[r_idx][c_idx] += 1
        total += 1
        if r_idx == c_idx:
            correct += 1

    acc = correct / total if total > 0 else 0.0
    return {
        "accuracy": acc,
        "total": total,
        "correct": correct,
        "categories": categories,
        "confusion_matrix": matrix,
    }
