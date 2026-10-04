import math
from typing import Any

import numpy as np
from app.condition import condition_from_index
from app.config_loader import get_segments_config
from app.gps import GPSPoint, haversine_m
from app.schemas import Defect, SegmentCondition


def _point_to_line_dist(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> tuple[float, float]:
    """
    Finds the shortest distance from point p to line segment ab, 
    and returns the fractional projection t along ab.
    We approximate locally using euclidean distance for this small scale snapping.
    """
    l2 = (bx - ax)**2 + (by - ay)**2
    if l2 == 0.0:
        return math.hypot(px - ax, py - ay), 0.0
        
    t = max(0, min(1, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / l2))
    proj_x = ax + t * (bx - ax)
    proj_y = ay + t * (by - ay)
    return math.hypot(px - proj_x, py - proj_y), t


def compute_union_area(defects: list[Defect], frame_w: int, frame_h: int) -> int:
    """
    Computes the Union-Area of the bounding boxes using a 2D boolean numpy array.
    This guarantees overlapping boxes are not double-counted.
    """
    if not defects:
        return 0
        
    canvas = np.zeros((frame_h, frame_w), dtype=bool)
    for d in defects:
        if d.bbox is None:
            continue
        x1 = max(0, int(d.bbox.x1))
        y1 = max(0, int(d.bbox.y1))
        x2 = min(frame_w, int(d.bbox.x2))
        y2 = min(frame_h, int(d.bbox.y2))
        if x1 < x2 and y1 < y2:
            canvas[y1:y2, x1:x2] = True
            
    return int(np.sum(canvas))


def build_segments(
    gps_points: list[GPSPoint],
    defects: list[Defect],
    frame_w: int,
    frame_h: int,
    cfg: dict[str, Any]
) -> list[SegmentCondition]:
    if not gps_points:
        return []
        
    seg_length_m = cfg.get("segments", {}).get("length_m", get_segments_config().get("length_m", 50.0))
    max_time_gap_s = cfg.get("gps", {}).get("max_time_gap_s", 5.0)
    
    # 1. Build polyline and cumulative distances
    cumulative_dist = [0.0]
    is_gap = [False] # is_gap[i] means gap between point i-1 and i
    total_dist = 0.0
    
    for i in range(1, len(gps_points)):
        p1 = gps_points[i-1]
        p2 = gps_points[i]
        
        dist = haversine_m(p1.lat, p1.lon, p2.lat, p2.lon)
        total_dist += dist
        cumulative_dist.append(total_dist)
        
        gap = p2.timestamp_s - p1.timestamp_s > max_time_gap_s
        is_gap.append(gap)
        
    # 2. Bucket segments
    num_segments = math.ceil(total_dist / seg_length_m) if total_dist > 0 else 1
    segment_defects = [[] for _ in range(num_segments)]
    segment_covered = [False for _ in range(num_segments)]
    
    # Evaluate segment coverage based on gaps
    # A segment is covered if ANY part of the polyline traversing it is NOT a gap.
    # Actually, simpler: mark segment as covered if a valid polyline segment falls inside it.
    for i in range(1, len(gps_points)):
        if not is_gap[i]:
            start_dist = cumulative_dist[i-1]
            end_dist = cumulative_dist[i]
            
            start_seg = int(start_dist / seg_length_m)
            end_seg = int(end_dist / seg_length_m)
            
            # Bound end_seg
            start_seg = min(start_seg, num_segments - 1)
            end_seg = min(end_seg, num_segments - 1)
            
            for s in range(start_seg, end_seg + 1):
                segment_covered[s] = True
                
    # 3. Snap defects to polyline
    for d in defects:
        best_dist = float("inf")
        best_cum_dist = 0.0
        
        for i in range(1, len(gps_points)):
            p1 = gps_points[i-1]
            p2 = gps_points[i]
            
            # Local equirectangular approximation for fast snapping
            # R = 6371000, 1 deg lat = 111139 m, 1 deg lon = 111139 * cos(lat)
            lat_m = 111139.0
            lon_m = 111139.0 * math.cos(math.radians(p1.lat))
            
            ax, ay = p1.lon * lon_m, p1.lat * lat_m
            bx, by = p2.lon * lon_m, p2.lat * lat_m
            px, py = d.lon * lon_m, d.lat * lat_m
            
            dist, t = _point_to_line_dist(px, py, ax, ay, bx, by)
            
            if dist < best_dist:
                best_dist = dist
                segment_dist = haversine_m(p1.lat, p1.lon, p2.lat, p2.lon)
                best_cum_dist = cumulative_dist[i-1] + t * segment_dist
                
        seg_idx = int(best_cum_dist / seg_length_m)
        seg_idx = min(seg_idx, num_segments - 1)
        segment_defects[seg_idx].append(d)
        
    # 4. Compute Stage 4 Condition per segment
    results = []
    condition_cfg = cfg.get("condition", {})
    
    for i in range(num_segments):
        start_m = i * seg_length_m
        end_m = min((i + 1) * seg_length_m, total_dist)
        
        if not segment_covered[i]:
            results.append(SegmentCondition(
                segment_id=i+1,
                start_m=start_m,
                end_m=end_m,
                damage_index=0.0,
                condition="NoData"
            ))
            continue
            
        union_area_px = compute_union_area(segment_defects[i], frame_w, frame_h)
        total_area_px = frame_w * frame_h
        
        damage_index = union_area_px / total_area_px if total_area_px > 0 else 0.0
        condition_str = condition_from_index(damage_index, condition_cfg)
        
        results.append(SegmentCondition(
            segment_id=i+1,
            start_m=start_m,
            end_m=end_m,
            damage_index=damage_index,
            condition=condition_str
        ))
        
    return results
