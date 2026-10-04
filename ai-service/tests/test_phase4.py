import os

import pytest
from app.dedup import dedup_tracks
from app.gps import interpolate, parse_csv, parse_gpx, shift_position
from app.schemas import BoundingBox, GPSPoint, TrackObservation


@pytest.fixture
def test_cfg():
    return {
        "gps": {
            "max_accuracy_m": 10.0,
            "max_time_gap_s": 5.0,
            "video_start_offset_s": 0.0
        },
        "tracking": {
            "min_track_frames": 1
        },
        "dedup": {
            "merge_radius_m": 5.0
        },
        "severity": {
            "low_max_ratio": 0.02,
            "medium_max_ratio": 0.08,
            "near_zone_top_fraction": 0.5
        }
    }


def test_gps_parsing():
    # We assume tests are run from the repository root
    csv_path = os.path.join("data", "fixtures", "test.csv")
    if os.path.exists(csv_path):
        points, malformed = parse_csv(csv_path)
        assert len(points) == 3
        assert malformed == 1
        assert points[0].timestamp_s == 1700000000.0
        assert points[1].lat == 13.0001
        
    gpx_path = os.path.join("data", "fixtures", "test.gpx")
    if os.path.exists(gpx_path):
        points, malformed = parse_gpx(gpx_path)
        assert len(points) == 2
        assert malformed == 1


def test_interpolate(test_cfg):
    points = [
        GPSPoint(timestamp_s=10.0, lat=10.0, lon=20.0),
        GPSPoint(timestamp_s=12.0, lat=10.0, lon=20.2), # Gap of 2s
        GPSPoint(timestamp_s=20.0, lat=10.1, lon=20.5)  # Gap of 8s
    ]
    
    cfg = test_cfg["gps"]
    # Exact match
    p = interpolate(points, 10.0, 0.0, cfg)
    assert p is not None and p.timestamp_s == 10.0 and p.lat == 10.0
    
    # Midpoint
    p = interpolate(points, 11.0, 0.0, cfg)
    assert p is not None and p.lat == 10.0 and p.lon == 20.1
    
    # Gap larger than max_time_gap_s (5.0s)
    p = interpolate(points, 15.0, 0.0, cfg)
    assert p is None
    
    # Out of bounds
    assert interpolate(points, 9.0, 0.0, cfg) is None
    assert interpolate(points, 21.0, 0.0, cfg) is None
    
    # Offset applied correctly
    p = interpolate(points, 0.0, 11.0, cfg) # video=0 + offset=11 -> ts=11
    assert p is not None and p.lon == 20.1


def test_dedup_30_frames_stationary(test_cfg):
    # One track, 30 frames
    track = []
    for i in range(30):
        track.append(TrackObservation(
            track_id=1, class_name="pothole", frame_idx=i,
            bbox=BoundingBox(x1=10, y1=10, x2=20, y2=20),
            confidence=0.9, frame_w=100, frame_h=100
        ))
        
    gps_points = [
        GPSPoint(timestamp_s=0.0, lat=13.0, lon=80.0),
        GPSPoint(timestamp_s=2.0, lat=13.0, lon=80.0)
    ]
    
    # fps=30 means 30 frames is 1 second
    defects, unlocated = dedup_tracks([track], gps_points, 30.0, 0.0, test_cfg)
    assert len(unlocated) == 0
    assert len(defects) == 1
    assert defects[0].class_name == "pothole"
    assert defects[0].track_ids == [1]


def test_dedup_merge_radius(test_cfg):
    # Two tracks, separated by distance
    track1 = [TrackObservation(track_id=1, class_name="pothole", frame_idx=0, bbox=BoundingBox(x1=10, y1=80, x2=20, y2=90), confidence=0.9, frame_w=100, frame_h=100)]
    [TrackObservation(track_id=2, class_name="pothole", frame_idx=0, bbox=BoundingBox(x1=10, y1=80, x2=20, y2=90), confidence=0.9, frame_w=100, frame_h=100)]
    
    # Let's mock GPS explicitly by putting the video timestamps exactly at the GPS timestamps
    [
        GPSPoint(timestamp_s=0.0, lat=13.0, lon=80.0),
    ]
    
    # To test distance, we can just manipulate the track's closest approach time, 
    # but here we can just create synthetic GPS logs where the time corresponds to the tracks.
    # Actually, we can use shift_position to make a point exactly 12m away.
    lat2, lon2 = shift_position(13.0, 80.0, 90, 12.0)
    gps_points_12m = [
        GPSPoint(timestamp_s=0.0, lat=13.0, lon=80.0),
        GPSPoint(timestamp_s=1.0, lat=lat2, lon=lon2)
    ]
    
    # For track2 to hit timestamp 1.0 at 30fps, frame_idx = 30
    track2_12m = [TrackObservation(track_id=2, class_name="pothole", frame_idx=30, bbox=BoundingBox(x1=10, y1=80, x2=20, y2=90), confidence=0.9, frame_w=100, frame_h=100)]
    
    defects, _ = dedup_tracks([track1, track2_12m], gps_points_12m, 30.0, 0.0, test_cfg)
    assert len(defects) == 2 # 12m > 5m radius
    
    lat3, lon3 = shift_position(13.0, 80.0, 90, 3.0)
    gps_points_3m_sep = [
        GPSPoint(timestamp_s=0.0, lat=13.0, lon=80.0),
        GPSPoint(timestamp_s=1.0, lat=lat3, lon=lon3)
    ]
    defects, _ = dedup_tracks([track1, track2_12m], gps_points_3m_sep, 30.0, 0.0, test_cfg)
    assert len(defects) == 1 # 3m <= 5m radius
    assert sorted(defects[0].track_ids) == [1, 2]


def test_dedup_tracker_id_switch_and_different_classes(test_cfg):
    track1 = [TrackObservation(track_id=1, class_name="pothole", frame_idx=0, bbox=BoundingBox(x1=10, y1=80, x2=20, y2=90), confidence=0.9, frame_w=100, frame_h=100)]
    track2 = [TrackObservation(track_id=2, class_name="pothole", frame_idx=1, bbox=BoundingBox(x1=10, y1=80, x2=20, y2=90), confidence=0.9, frame_w=100, frame_h=100)]
    track3 = [TrackObservation(track_id=3, class_name="crack", frame_idx=0, bbox=BoundingBox(x1=10, y1=80, x2=20, y2=90), confidence=0.9, frame_w=100, frame_h=100)]
    
    gps_points = [GPSPoint(timestamp_s=0.0, lat=13.0, lon=80.0), GPSPoint(timestamp_s=1.0, lat=13.0, lon=80.0)]
    
    # ID switch (track1 and track2 are same class and location) -> 1 defect
    defects, _ = dedup_tracks([track1, track2], gps_points, 30.0, 0.0, test_cfg)
    assert len(defects) == 1
    
    # Different classes same location (track1 and track3) -> 2 defects
    defects, _ = dedup_tracks([track1, track3], gps_points, 30.0, 0.0, test_cfg)
    assert len(defects) == 2


def test_gps_gap_goes_to_unlocated(test_cfg):
    track = [TrackObservation(track_id=1, class_name="pothole", frame_idx=300, bbox=BoundingBox(x1=10, y1=80, x2=20, y2=90), confidence=0.9, frame_w=100, frame_h=100)]
    # Frame 300 at 30 fps is ts=10.0
    # GPS gap between 0 and 20s
    gps_points = [GPSPoint(timestamp_s=0.0, lat=13.0, lon=80.0), GPSPoint(timestamp_s=20.0, lat=13.1, lon=80.1)]
    
    defects, unlocated = dedup_tracks([track], gps_points, 30.0, 0.0, test_cfg)
    assert len(defects) == 0
    assert len(unlocated) == 1
    assert unlocated[0][0].track_id == 1


def test_property_random_scatter(test_cfg):
    N = 10
    tracks = []
    gps_points = []
    
    base_lat = 13.0
    base_lon = 80.0
    
    for i in range(N):
        tracks.append([TrackObservation(track_id=i, class_name="pothole", frame_idx=i, bbox=BoundingBox(x1=10, y1=80, x2=20, y2=90), confidence=0.9, frame_w=100, frame_h=100)])
        # Shift each by 20 meters to ensure > 5m separation
        lat, lon = shift_position(base_lat, base_lon, 90, i * 20.0)
        # video_time = i / 30.0
        gps_points.append(GPSPoint(timestamp_s=float(i) / 30.0, lat=lat, lon=lon))
        
    defects, _ = dedup_tracks(tracks, gps_points, 30.0, 0.0, test_cfg)
    assert len(defects) == N
    # Determinism: defect IDs are 1 to N
    assert [d.defect_id for d in defects] == list(range(1, N + 1))
