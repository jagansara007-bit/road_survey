
from app.config_loader import get_condition_thresholds
from app.schemas import Detection, SegmentCondition


def evaluate_segment_condition(damage_index: float) -> str:
    """
    Evaluates condition rating using externalized thresholds from thresholds.yaml.
    """
    thresholds = get_condition_thresholds()
    fair_thresh = thresholds["fair_threshold"]
    poor_thresh = thresholds["poor_threshold"]

    if damage_index < fair_thresh:
        return "Good"
    elif damage_index < poor_thresh:
        return "Fair"
    else:
        return "Poor"


def compute_segment_condition(
    detections: list[Detection],
    segment_length_m: float = 50.0,
    start_m: float = 0.0
) -> SegmentCondition:
    """
    Computes road condition index for a given segment.
    """
    total_area_ratio = 0.0
    for det in detections:
        x1, y1, x2, y2 = det.bbox
        box_w = max(0.0, x2 - x1)
        box_h = max(0.0, y2 - y1)
        total_area_ratio += (box_w * box_h)

    damage_index = min(1.0, total_area_ratio)
    condition_rating = evaluate_segment_condition(damage_index)

    return SegmentCondition(
        start_m=start_m,
        end_m=start_m + segment_length_m,
        damage_index=damage_index,
        condition=condition_rating
    )
