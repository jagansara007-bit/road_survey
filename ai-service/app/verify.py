import math
from typing import Any

from app.gps import GPSPoint
from app.schemas import Defect


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _is_covered(defect: Defect, path: list[GPSPoint], coverage_radius_m: float) -> bool:
    if not path:
        return False
        
    for p in path:
        d = haversine_m(defect.lat, defect.lon, p.lat, p.lon)
        if d <= coverage_radius_m:
            return True
            
    # For a precise check we could do point-to-line projection, but point distance to raw GPS points
    # is sufficient if GPS points are dense (e.g. 1Hz). We'll assume dense points.
    return False


def verify_survey(
    old_defects: list[Defect],
    new_defects: list[Defect],
    covered_path: list[GPSPoint],
    cfg: dict[str, Any]
) -> tuple[list[Defect], list[Defect]]:
    """
    Matches new defects against old defects.
    Returns (updated_old_defects, updated_new_defects).
    """
    v_cfg = cfg.get("verification", {})
    match_radius_m = v_cfg.get("match_radius_m", 10.0)
    coverage_radius_m = v_cfg.get("coverage_radius_m", 15.0)
    
    # Pre-calculate distances for same-class pairs
    candidates = []
    for old_idx, old_d in enumerate(old_defects):
        for new_idx, new_d in enumerate(new_defects):
            if old_d.class_name == new_d.class_name:
                dist = haversine_m(old_d.lat, old_d.lon, new_d.lat, new_d.lon)
                if dist <= match_radius_m:
                    candidates.append((dist, old_d.defect_id, old_idx, new_d.defect_id, new_idx))
                    
    # Greedy nearest matching
    # Sort by dist (asc), then old_defect_id (asc), new_defect_id (asc) for determinism
    candidates.sort(key=lambda x: (x[0], x[1] or 0, x[3] or 0))
    
    matched_old_indices = set()
    matched_new_indices = set()
    
    for dist, old_id, old_idx, new_id, new_idx in candidates:
        if old_idx not in matched_old_indices and new_idx not in matched_new_indices:
            matched_old_indices.add(old_idx)
            matched_new_indices.add(new_idx)
            
            # Apply matches
            old_d = old_defects[old_idx]
            new_d = new_defects[new_idx]
            
            new_d.matched_prev_id = old_d.defect_id
            
            if old_d.status == "Repaired":
                new_d.status = "Failed"
                new_d.recurrence = True
                
                old_d.status = "Failed"
                old_d.recurrence = True
            else:
                new_d.status = "Open"
                
                old_d.status = "Open"
                old_d.unverified = False
                
    # Process unmatched new defects
    for i, new_d in enumerate(new_defects):
        if i not in matched_new_indices:
            new_d.status = "New"
            
    # Process unmatched old defects
    for i, old_d in enumerate(old_defects):
        if i not in matched_old_indices:
            if _is_covered(old_d, covered_path, coverage_radius_m):
                old_d.status = "Repaired"
                old_d.unverified = False
            else:
                old_d.unverified = True
                # Status unchanged
                
    return old_defects, new_defects
