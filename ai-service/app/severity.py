
from app.config_loader import get_severity_thresholds


def compute_box_area_ratio(bbox: tuple[float, float, float, float], image_shape: tuple[int, int]) -> float:
    """
    Computes ratio of bounding box area to total image area.
    bbox: (x1, y1, x2, y2)
    image_shape: (height, width)
    """
    x1, y1, x2, y2 = bbox
    height, width = image_shape
    total_area = height * width
    if total_area <= 0:
        return 0.0

    box_w = max(0.0, x2 - x1)
    box_h = max(0.0, y2 - y1)
    box_area = box_w * box_h
    return box_area / total_area


def calculate_severity(area_ratio: float) -> str:
    """
    Evaluates severity based on externalized thresholds from thresholds.yaml.
    """
    thresholds = get_severity_thresholds()
    low = thresholds["ratio_low"]
    high = thresholds["ratio_high"]

    if area_ratio < low:
        return "Low"
    elif area_ratio < high:
        return "Medium"
    else:
        return "High"


def assess_defect_severity(bbox: list[float], image_shape: tuple[int, int]) -> tuple[str, float]:
    ratio = compute_box_area_ratio((bbox[0], bbox[1], bbox[2], bbox[3]), image_shape)
    severity_level = calculate_severity(ratio)
    return severity_level, ratio
