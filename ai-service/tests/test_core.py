from app.condition import evaluate_segment_condition
from app.config_loader import get_classes, get_severity_thresholds, load_thresholds
from app.schemas import Detection
from app.severity import calculate_severity


def test_imports_and_thresholds():
    cfg = load_thresholds()
    assert "classes" in cfg
    assert "severity" in cfg
    assert "condition" in cfg

    classes = get_classes()
    assert "D00" in classes
    assert "D40" in classes


def test_severity_calculation():
    thresholds = get_severity_thresholds()
    low_bound = thresholds["ratio_low"]
    high_bound = thresholds["ratio_high"]

    assert calculate_severity(low_bound / 2) == "Low"
    assert calculate_severity((low_bound + high_bound) / 2) == "Medium"
    assert calculate_severity(high_bound + 0.05) == "High"


def test_condition_evaluation():
    assert evaluate_segment_condition(0.01) == "Good"
    assert evaluate_segment_condition(0.08) == "Fair"
    assert evaluate_segment_condition(0.20) == "Poor"


def test_schemas_validation():
    det = Detection(class_name="D40", confidence=0.88, bbox=[100.0, 200.0, 300.0, 400.0])
    assert det.class_name == "D40"
    assert det.track_id is None
