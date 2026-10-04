import os

import pytest
from app.gps import shift_position
from app.osm import CachedOsmProvider
from app.priority import build_queue, compute_priority, select_within_budget
from app.schemas import BoundingBox, Defect, GPSPoint
from app.segments import build_segments


@pytest.fixture
def test_cfg():
    return {
        "gps": {
            "max_accuracy_m": 10.0,
            "max_time_gap_s": 5.0,
            "video_start_offset_s": 0.0
        },
        "segments": {
            "length_m": 50.0
        },
        "condition": {
            "fair_min_index": 0.05,
            "poor_min_index": 0.15
        },
        "priority": {
            "severity_score": {"Low": 1.0, "Medium": 2.0, "High": 3.0},
            "road_weight": {"primary": 1.5, "secondary": 1.25, "residential": 1.0, "default": 1.0},
            "exposure": {"radius_m": 200.0, "factor": 1.5},
            "recurrence_factor": 1.5
        },
        "cost": {
            "nominal_area_m2": {"Low": 0.5, "Medium": 1.5, "High": 3.0},
            "unit_rate_inr_per_m2": 1500.0
        }
    }


@pytest.fixture
def test_osm():
    fixture_path = os.path.join("data", "fixtures", "osm_cache_fixture.json")
    return CachedOsmProvider(fixture_path, default_class="residential")


def test_segments_bucketing(test_cfg):
    # Path of known length, e.g., 237 meters
    # 5 segments: 0-50, 50-100, 100-150, 150-200, 200-237
    lat_base = 13.0
    lon_base = 80.0
    
    gps_points = [GPSPoint(timestamp_s=0.0, lat=lat_base, lon=lon_base)]
    
    # 237 meters total, in 1 meter increments per second
    for i in range(1, 238):
        lat, lon = shift_position(lat_base, lon_base, 90, i)
        gps_points.append(GPSPoint(timestamp_s=float(i), lat=lat, lon=lon))
        
    lat_49_9, lon_49_9 = shift_position(lat_base, lon_base, 90, 49.9)
    defect1 = Defect(defect_id=1, class_name="pothole", lat=lat_49_9, lon=lon_49_9, severity="High", area_px=100.0, confidence=0.9, track_ids=[1], bbox=BoundingBox(x1=0, y1=0, x2=10, y2=10))
    
    lat_50_1, lon_50_1 = shift_position(lat_base, lon_base, 90, 50.1)
    defect2 = Defect(defect_id=2, class_name="pothole", lat=lat_50_1, lon=lon_50_1, severity="High", area_px=100.0, confidence=0.9, track_ids=[2], bbox=BoundingBox(x1=0, y1=0, x2=10, y2=10))
    
    segments = build_segments(gps_points, [defect1, defect2], frame_w=100, frame_h=100, cfg=test_cfg)
    
    assert len(segments) == 5
    # Last segment ends at ~237m
    assert abs(segments[-1].end_m - 237.0) < 1.0
    
    # Check snapping
    # Defect at 49.9m should be in segment 1 (idx 0)
    # Defect at 50.1m should be in segment 2 (idx 1)
    # We can verify this implicitly by checking their damage indices or just logic.
    assert segments[0].damage_index > 0
    assert segments[1].damage_index > 0
    assert segments[2].damage_index == 0


def test_gps_gap_nodata(test_cfg):
    lat_base = 13.0
    lon_base = 80.0
    lat_100, lon_100 = shift_position(lat_base, lon_base, 90, 100.0)
    
    # Gap > 5s between points -> Gap
    gps_points = [
        GPSPoint(timestamp_s=0.0, lat=lat_base, lon=lon_base),
        GPSPoint(timestamp_s=10.0, lat=lat_100, lon=lon_100)
    ]
    
    segments = build_segments(gps_points, [], frame_w=100, frame_h=100, cfg=test_cfg)
    assert len(segments) == 2
    
    assert segments[0].condition == "NoData"
    assert segments[1].condition == "NoData"


def test_priority_calculations(test_osm, test_cfg):
    # High x primary x school x recurrence = 3.0 * 1.5 * 1.5 * 1.5 = 10.125
    # primary is at 13.0000, 80.0000; school is at 13.0005, 80.0002
    defect1 = Defect(defect_id=1, class_name="pothole", lat=13.0000, lon=80.0000, severity="High", area_px=100, confidence=0.9, track_ids=[1])
    p1 = compute_priority(defect1, test_osm, is_recurrent=True, cfg=test_cfg)
    assert abs(p1 - 10.125) < 0.001
    
    # Low x residential x no school x no recurrence = 1.0 * 1.0 * 1.0 * 1.0 = 1.0
    defect2 = Defect(defect_id=2, class_name="crack", lat=14.0, lon=81.0, severity="Low", area_px=100, confidence=0.9, track_ids=[2])
    p2 = compute_priority(defect2, test_osm, is_recurrent=False, cfg=test_cfg)
    assert abs(p2 - 1.0) < 0.001


def test_queue_determinism(test_osm, test_cfg):
    # Two identical defects
    d1 = Defect(defect_id=1, class_name="pothole", lat=14.0, lon=81.0, severity="Low", area_px=100, confidence=0.9, track_ids=[1])
    d2 = Defect(defect_id=2, class_name="pothole", lat=14.0, lon=81.0, severity="Low", area_px=100, confidence=0.9, track_ids=[2])
    
    q = build_queue([d1, d2], test_osm, test_cfg)
    # Same severity, same priority, defect_id asc -> 1 then 2? No, sort key is -(d.defect_id or 0) reverse=True -> smaller negative -> bigger positive?
    # Let's check the logic: priority desc, severity desc, -defect_id desc => -defect_id desc is defect_id asc.
    assert q[0].defect.defect_id == 1
    assert q[1].defect.defect_id == 2


def test_budget_selection():
    # Defects with estimated cost: 100, 200, 300, 50, sorted by priority (A, B, C, D)
    d_A = Defect(defect_id=1, class_name="pothole", lat=0, lon=0, severity="High", area_px=0, confidence=0.9, track_ids=[])
    d_A.estimated_cost = 200.0
    d_B = Defect(defect_id=2, class_name="pothole", lat=0, lon=0, severity="High", area_px=0, confidence=0.9, track_ids=[])
    d_B.estimated_cost = 300.0
    d_C = Defect(defect_id=3, class_name="pothole", lat=0, lon=0, severity="High", area_px=0, confidence=0.9, track_ids=[])
    d_C.estimated_cost = 50.0
    d_D = Defect(defect_id=4, class_name="pothole", lat=0, lon=0, severity="High", area_px=0, confidence=0.9, track_ids=[])
    d_D.estimated_cost = 100.0
    
    from app.schemas import QueueItem
    queue = [QueueItem(defect=d_A, selected=False), QueueItem(defect=d_B, selected=False), 
             QueueItem(defect=d_C, selected=False), QueueItem(defect=d_D, selected=False)]
    
    # Exact fit (Budget = 200) -> selects A, leaves 0, skips B, C, D
    res1 = select_within_budget(queue, 200.0)
    assert len(res1.selected) == 1
    assert res1.selected[0].defect_id == 1
    
    # Skip-and-continue (Budget = 250) -> selects A (200), remaining 50. Skips B (300). Selects C (50). Remaining 0. Skips D (100)
    res2 = select_within_budget(queue, 250.0)
    assert len(res2.selected) == 2
    assert [d.defect_id for d in res2.selected] == [1, 3]
    assert res2.remaining_budget == 0.0
    
    # Zero budget -> none selected
    res3 = select_within_budget(queue, 0.0)
    assert len(res3.selected) == 0
    assert len(res3.skipped) == 4
    
    # Huge budget -> all selected
    res4 = select_within_budget(queue, 10000.0)
    assert len(res4.selected) == 4
    assert len(res4.skipped) == 0


def test_osm_missing_data():
    # Invalid path
    provider = CachedOsmProvider("data/does_not_exist.json", default_class="residential")
    assert provider.road_class(13.0, 80.0) == "residential"
    assert not provider.near_sensitive(13.0, 80.0, 200.0)
