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
    return load_thresholds().get("severity", {"ratio_low": 0.02, "ratio_high": 0.08})


def get_condition_thresholds() -> dict[str, float]:
    return load_thresholds().get("condition", {"fair_threshold": 0.05, "poor_threshold": 0.15})
