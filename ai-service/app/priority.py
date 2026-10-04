from typing import Any

from app.config_loader import get_cost_config
from app.osm import RoadContext
from app.schemas import Defect, QueueItem, QueueResult


def compute_priority(
    defect: Defect,
    road_ctx: RoadContext,
    is_recurrent: bool,
    cfg: dict[str, Any]
) -> float:
    priority_cfg = cfg.get("priority", {})
    
    # 1. Severity Score (support both severity_weights from YAML and legacy severity_score)
    severity_weights = priority_cfg.get("severity_weights") or priority_cfg.get(
        "severity_score", {"Low": 1.0, "Medium": 2.0, "High": 3.0}
    )
    severity_score = severity_weights.get(defect.severity, 1.0)
    
    # 2. Road Weight (support both road_weights from YAML and legacy road_weight)
    road_class = road_ctx.road_class(defect.lat, defect.lon)
    road_weights = priority_cfg.get("road_weights") or priority_cfg.get(
        "road_weight", {"primary": 1.5, "secondary": 1.25, "residential": 1.0, "default": 1.0}
    )
    road_weight = road_weights.get(road_class, road_weights.get("default", 1.0))
    
    # 3. Exposure Factor (support exposure_factors dict and legacy nested exposure)
    exposure_factors = priority_cfg.get("exposure_factors", {})
    exposure_radius = (
        cfg.get("priority_exposure", {}).get("radius_m")
        or priority_cfg.get("exposure_radius_m")
        or priority_cfg.get("exposure", {}).get("radius_m", 200.0)
    )
    is_exposed = road_ctx.near_sensitive(defect.lat, defect.lon, exposure_radius)
    if is_exposed:
        exposure_factor = exposure_factors.get(
            "near_sensitive_facility",
            priority_cfg.get("exposure", {}).get("factor", 1.5)
        )
    else:
        exposure_factor = exposure_factors.get("standard", 1.0)
    
    # 4. Recurrence Factor (support recurrence_factors dict and legacy recurrence_factor float)
    recurrence_factors = priority_cfg.get("recurrence_factors", {})
    if is_recurrent:
        recurrence_factor = recurrence_factors.get(
            "previously_failed",
            priority_cfg.get("recurrence_factor", 1.5)
        )
    else:
        recurrence_factor = recurrence_factors.get("first_occurrence", 1.0)
    
    return severity_score * road_weight * exposure_factor * recurrence_factor


def estimate_cost(defect: Defect, cfg: dict[str, Any]) -> float:
    """
    Computes an estimated cost for repairing the defect.
    WARNING: Pixel area cannot be reliably converted to m^2 without camera calibration.
    This is an explicit assumption/estimate for prioritization only.
    """
    cost_cfg = cfg.get("cost") or get_cost_config()
    nominal_area_m2 = cost_cfg.get("nominal_area_m2", {"Low": 0.5, "Medium": 1.5, "High": 3.0})
    unit_rate = cost_cfg.get("unit_rate_inr_per_m2", 1500.0)
    
    area = nominal_area_m2.get(defect.severity, 0.5)
    return area * unit_rate


def build_queue(defects: list[Defect], road_ctx: RoadContext, cfg: dict[str, Any]) -> list[QueueItem]:
    for d in defects:
        d.priority = compute_priority(d, road_ctx, is_recurrent=False, cfg=cfg)
        d.estimated_cost = estimate_cost(d, cfg)
        
    severity_rank = {"High": 3, "Medium": 2, "Low": 1}
    
    # Sort by priority desc, then severity desc, then defect_id asc (for determinism)
    defects.sort(
        key=lambda d: (
            d.priority or 0.0,
            severity_rank.get(d.severity, 0),
            -(d.defect_id or 0)
        ),
        reverse=True
    )
    
    return [QueueItem(defect=d, selected=False) for d in defects]


def select_within_budget(queue: list[QueueItem], budget_inr: float) -> QueueResult:
    """
    Walk the queue in priority order. Include if fits remaining budget, else skip and continue.
    """
    selected = []
    skipped = []
    remaining = budget_inr
    
    for item in queue:
        cost = item.defect.estimated_cost or 0.0
        if cost <= remaining:
            item.selected = True
            selected.append(item.defect)
            remaining -= cost
        else:
            item.selected = False
            skipped.append(item.defect)
            
    return QueueResult(selected=selected, skipped=skipped, remaining_budget=remaining)
