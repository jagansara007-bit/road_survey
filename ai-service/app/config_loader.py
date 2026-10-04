import os
from functools import lru_cache
from typing import Any

import yaml


@lru_cache
def load_thresholds() -> dict[str, Any]:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.normpath(os.path.join(current_dir, "..", "config", "thresholds.yaml"))
    if not os.path.exists(config_path):
        # Fallback to local config relative path
        config_path = os.path.join("config", "thresholds.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_classes() -> dict[str, str]:
    return load_thresholds().get("classes", {})


def get_severity_thresholds() -> dict[str, float]:
    return load_thresholds().get("severity", {"low_max_ratio": 0.02, "medium_max_ratio": 0.08, "near_zone_top_fraction": 0.5})


def get_condition_thresholds() -> dict[str, float]:
    return load_thresholds().get("condition", {"fair_min_index": 0.05, "poor_min_index": 0.15})


def get_cost_config() -> dict[str, Any]:
    return load_thresholds().get("cost", {
        "nominal_area_m2": {"Low": 0.5, "Medium": 1.5, "High": 3.0},
        "unit_rate_inr_per_m2": 1500.0,
    })


def get_dedup_config() -> dict[str, Any]:
    return load_thresholds().get("dedup", {"merge_radius_m": 5.0})


def get_segments_config() -> dict[str, Any]:
    return load_thresholds().get("segments", {"length_m": 50.0})


def get_detector_config() -> dict[str, Any]:
    return load_thresholds().get("detector", {"conf_thres": 0.25, "iou_threshold": 0.45, "input_size": 640})


def get_privacy_config() -> dict[str, Any]:
    return load_thresholds().get("privacy", {"blur_faces": True, "blur_plates": True, "retention_days": 30})

