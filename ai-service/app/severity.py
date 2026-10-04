from app.config_loader import get_severity_thresholds
from app.schemas import BoundingBox, TrackObservation


def closest_approach(observations: list[TrackObservation], min_track_frames: int) -> TrackObservation | None:
    """
    Chooses the observation with the largest box area among those whose bottom edge 
    is lowest in the frame (highest y2).
    Tie-break rule: Largest area, then highest confidence.
    Ignores tracks shorter than min_track_frames.
    """
    if not observations or len(observations) < min_track_frames:
        return None

    # Find the maximum y2 (lowest in the frame)
    max_y2 = max(obs.bbox.y2 for obs in observations)

    # Filter to only those with max_y2
    closest_candidates = [obs for obs in observations if obs.bbox.y2 == max_y2]

    # Sort by largest area, then by highest confidence
    closest_candidates.sort(
        key=lambda obs: (
            (obs.bbox.x2 - obs.bbox.x1) * (obs.bbox.y2 - obs.bbox.y1),
            obs.confidence
        ),
        reverse=True
    )

    return closest_candidates[0]


def near_zone_area_ratio(bbox: BoundingBox, frame_w: int, frame_h: int, cfg: dict) -> float:
    """
    Computes box area clipped to the near zone divided by near-zone area.
    """
    near_zone_top = frame_h * cfg.get("near_zone_top_fraction", 0.5)
    near_zone_area = frame_w * (frame_h - near_zone_top)

    if near_zone_area <= 0:
        return 0.0

    # Clip box to near zone
    x1 = max(0.0, bbox.x1)
    y1 = max(near_zone_top, bbox.y1)
    x2 = min(float(frame_w), bbox.x2)
    y2 = min(float(frame_h), bbox.y2)

    box_w = max(0.0, x2 - x1)
    box_h = max(0.0, y2 - y1)
    box_area = box_w * box_h

    return box_area / near_zone_area


def severity_label(ratio: float, cfg: dict) -> str:
    """
    Evaluates severity based on near-zone area ratio.
    """
    low = cfg["low_max_ratio"]
    medium = cfg["medium_max_ratio"]

    if ratio < low:
        return "Low"
    elif ratio < medium:
        return "Medium"
    else:
        return "High"

def assess_defect_severity(bbox: BoundingBox, image_shape: tuple[int, int]) -> tuple[str, float]:
    """Legacy helper for non-tracked usages."""
    ratio = near_zone_area_ratio(bbox, image_shape[1], image_shape[0], get_severity_thresholds())
    severity_level = severity_label(ratio, get_severity_thresholds())
    return severity_level, ratio
