from typing import Any

from app.config_loader import get_dedup_config
from app.gps import GPSPoint, haversine_m, interpolate
from app.schemas import Defect, TrackObservation
from app.severity import closest_approach, near_zone_area_ratio, severity_label


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        
    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]
        
    def union(self, i: int, j: int):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            self.parent[root_i] = root_j


def dedup_tracks(
    tracks: list[list[TrackObservation]],
    gps_points: list[GPSPoint],
    fps: float,
    video_start_offset_s: float,
    cfg: dict[str, Any]
) -> tuple[list[Defect], list[list[TrackObservation]]]:
    """
    Merges overlapping tracks of the same class.
    Returns (located_defects, unlocated_tracks).
    """
    located_representatives = []
    unlocated_tracks = []
    
    # 1. Pick closest approach for each track and interpolate GPS
    for track in tracks:
        rep_obs = closest_approach(track, cfg.get("tracking", {}).get("min_track_frames", 3))
        if rep_obs is None:
            continue
            
        video_time_s = rep_obs.frame_idx / fps
        gps_point = interpolate(gps_points, video_time_s, video_start_offset_s, cfg.get("gps", {}))
        
        if gps_point is None:
            unlocated_tracks.append(track)
            continue
            
        located_representatives.append({
            "track": track,
            "rep_obs": rep_obs,
            "gps": gps_point
        })
        
    n = len(located_representatives)
    uf = UnionFind(n)
    merge_radius_m = cfg.get("dedup", {}).get("merge_radius_m", get_dedup_config().get("merge_radius_m", 5.0))
    
    # 2. Single-linkage clustering: O(N^2) distance matrix for N <= ~1000
    for i in range(n):
        for j in range(i + 1, n):
            c1 = located_representatives[i]
            c2 = located_representatives[j]
            
            # Must be same class to merge
            if c1["rep_obs"].class_name != c2["rep_obs"].class_name:
                continue
                
            dist = haversine_m(c1["gps"].lat, c1["gps"].lon, c2["gps"].lat, c2["gps"].lon)
            if dist <= merge_radius_m:
                uf.union(i, j)
                
    # 3. Group by clusters and build Defect objects
    clusters: dict[int, list[dict[str, Any]]] = {}
    for i in range(n):
        root = uf.find(i)
        if root not in clusters:
            clusters[root] = []
        clusters[root].append(located_representatives[i])
        
    defects = []
    for root, cluster_members in clusters.items():
        # Representative observation of the cluster is the one with largest box area
        # from all the closest-approach candidates in the cluster.
        # Alternatively, we could re-run closest_approach over all track points in the cluster.
        # Let's just pick the member rep_obs that has the max area to match single-track logic.
        
        best_member = max(
            cluster_members,
            key=lambda m: (m["rep_obs"].bbox.x2 - m["rep_obs"].bbox.x1) * (m["rep_obs"].bbox.y2 - m["rep_obs"].bbox.y1)
        )
        rep_obs = best_member["rep_obs"]
        gps_point = best_member["gps"]
        
        class_name = rep_obs.class_name
        lat = gps_point.lat
        lon = gps_point.lon
        
        # Max confidence in the cluster
        conf = max(obs.confidence for member in cluster_members for obs in member["track"])
        
        # All track IDs
        track_ids = sorted({member["rep_obs"].track_id for member in cluster_members})
        
        # Calculate severity and area_px
        box_w = max(0.0, rep_obs.bbox.x2 - rep_obs.bbox.x1)
        box_h = max(0.0, rep_obs.bbox.y2 - rep_obs.bbox.y1)
        area_px = box_w * box_h
        
        ratio = near_zone_area_ratio(rep_obs.bbox, rep_obs.frame_w, rep_obs.frame_h, cfg.get("severity", {}))
        severity = severity_label(ratio, cfg.get("severity", {}))
        
        defects.append(Defect(
            defect_id=0, # Will assign later
            class_name=class_name,
            lat=lat,
            lon=lon,
            severity=severity,
            area_px=area_px,
            confidence=conf,
            track_ids=track_ids,
            bbox=rep_obs.bbox
        ))
        
    # 4. Deterministic defect_id assignment
    defects.sort(key=lambda d: min(d.track_ids)) # sort by first occurrence track ID
    for idx, d in enumerate(defects, start=1):
        d.defect_id = idx
        
    return defects, unlocated_tracks
