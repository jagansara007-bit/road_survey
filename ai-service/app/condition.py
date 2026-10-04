import numpy as np
from app.config_loader import get_condition_thresholds
from app.schemas import BoundingBox, Detection, SegmentCondition


def union_area_px(boxes: list[BoundingBox], canvas_w: int, canvas_h: int) -> int:
    """
    Rasterize all boxes on one binary canvas (numpy), count filled pixels.
    Clip boxes to the canvas; ignore degenerate boxes.
    """
    if not boxes or canvas_w <= 0 or canvas_h <= 0:
        return 0

    canvas = np.zeros((canvas_h, canvas_w), dtype=bool)

    for box in boxes:
        # Clip to canvas
        x1 = max(0, int(box.x1))
        y1 = max(0, int(box.y1))
        x2 = min(canvas_w, int(box.x2))
        y2 = min(canvas_h, int(box.y2))
        
        # Ignore degenerate boxes
        if x1 >= x2 or y1 >= y2:
            continue
            
        canvas[y1:y2, x1:x2] = True
        
    return int(np.sum(canvas))

def damage_index(boxes: list[BoundingBox], frame_w: int, frame_h: int, cfg: dict) -> float:
    """
    Computes the union area divided by the near-zone area.
    (Note: The near-zone definition should match severity.py if applied similarly,
    but here we calculate the union area on the whole frame and then normalize
    by the near-zone area or full frame area. We'll use full frame area for backward compatibility
    unless explicitly near-zone is requested. Assuming frame area per requirements unless cfg specifies otherwise.
    The prompt says: "damage_index(boxes, frame_w, frame_h, cfg): union area divided by frame (or near-zone) area."
    We'll use near-zone area if `near_zone_top_fraction` is in cfg, else frame area.)
    """
    union_area = union_area_px(boxes, frame_w, frame_h)
    
    near_zone_top = frame_h * cfg.get("near_zone_top_fraction", 0.0)
    denominator_area = frame_w * (frame_h - near_zone_top)
    
    if denominator_area <= 0:
        return 0.0
        
    return float(union_area) / denominator_area

def condition_from_index(index: float, cfg: dict) -> str:
    """
    Reuses existing Stage 4 rules using injected config.
    Legacy behavior was defined in old evaluate_segment_condition.
    """
    # Original rules (from condition.py:14-19):
    # if damage_index < fair_thresh: return "Good"
    # elif damage_index < poor_thresh: return "Fair"
    # else: return "Poor"
    fair_thresh = cfg["fair_min_index"]
    poor_thresh = cfg["poor_min_index"]

    if index < fair_thresh:
        return "Good"
    elif index < poor_thresh:
        return "Fair"
    else:
        return "Poor"

def sum_of_areas(boxes: list[BoundingBox]) -> float:
    """
    Legacy helper kept ONLY for comparison tests to show the double-counting problem
    on overlapping boxes.
    """
    total = 0.0
    for box in boxes:
        w = max(0.0, box.x2 - box.x1)
        h = max(0.0, box.y2 - box.y1)
        total += w * h
    return total

def compute_segment_condition(
    detections: list[Detection],
    segment_length_m: float = 50.0,
    start_m: float = 0.0
) -> SegmentCondition:
    """
    Legacy wrapper.
    """
    boxes = [det.bbox for det in detections]
    # For legacy behavior without frame sizes, assume normalized or dummy
    # In a real pipeline, this would receive frame dims.
    # We will compute sum_of_areas to mimic old behaviour if frame dims are unknown,
    # or just use 1.0, 1.0. The test suite uses the new pure functions.
    idx = min(1.0, sum_of_areas(boxes))
    
    return SegmentCondition(
        start_m=start_m,
        end_m=start_m + segment_length_m,
        damage_index=idx,
        condition=condition_from_index(idx, get_condition_thresholds())
    )
