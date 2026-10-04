from app.condition import condition_from_index
from app.config_loader import get_classes, get_condition_thresholds, get_severity_thresholds, load_thresholds
from app.schemas import BoundingBox, Detection
from app.severity import severity_label


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
    low_bound = thresholds["low_max_ratio"]
    medium_bound = thresholds["medium_max_ratio"]

    assert severity_label(low_bound / 2, thresholds) == "Low"
    assert severity_label((low_bound + medium_bound) / 2, thresholds) == "Medium"
    assert severity_label(medium_bound + 0.05, thresholds) == "High"


def test_condition_evaluation():
    thresholds = get_condition_thresholds()
    assert condition_from_index(0.01, thresholds) == "Good"
    assert condition_from_index(0.08, thresholds) == "Fair"
    assert condition_from_index(0.20, thresholds) == "Poor"


def test_schemas_validation():
    bbox = BoundingBox(x1=100.0, y1=200.0, x2=300.0, y2=400.0)
    det = Detection(class_name="D40", confidence=0.88, bbox=bbox)
    assert det.class_name == "D40"
    assert det.track_id is None
