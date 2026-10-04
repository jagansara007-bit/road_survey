import pytest
from app.condition import condition_from_index, sum_of_areas, union_area_px
from app.schemas import BoundingBox, TrackObservation
from app.severity import closest_approach, near_zone_area_ratio, severity_label


@pytest.fixture
def mock_config():
    return {
        "tracking": {"min_track_frames": 3},
        "severity": {
            "low_max_ratio": 0.02,
            "medium_max_ratio": 0.08,
            "near_zone_top_fraction": 0.5
        },
        "condition": {
            "fair_min_index": 0.05,
            "poor_min_index": 0.15
        }
    }

def test_union_area_vs_sum_of_areas():
    """Two identical overlapping boxes: union area == single box area; sum_of_areas is double."""
    boxes = [
        BoundingBox(x1=10, y1=10, x2=50, y2=50),
        BoundingBox(x1=10, y1=10, x2=50, y2=50)
    ]
    frame_w, frame_h = 100, 100
    
    union_area = union_area_px(boxes, frame_w, frame_h)
    sum_area = sum_of_areas(boxes)
    
    single_area = 40 * 40 # 1600
    assert union_area == single_area
    assert sum_area == single_area * 2

def test_partially_overlapping_boxes():
    """Partially overlapping boxes: union equals hand-computed value."""
    # Box 1: 10x10, area 100
    # Box 2: 10x10 starting at (5, 5), overlap is 5x5 = 25
    # Union should be 100 + 100 - 25 = 175
    boxes = [
        BoundingBox(x1=0, y1=0, x2=10, y2=10),
        BoundingBox(x1=5, y1=5, x2=15, y2=15)
    ]
    union_area = union_area_px(boxes, 100, 100)
    assert union_area == 175

def test_union_area_edge_cases():
    """Boxes outside/partly outside the frame; zero-area boxes; empty list -> 0."""
    boxes = [
        BoundingBox(x1=-10, y1=-10, x2=-5, y2=-5), # Completely outside
        BoundingBox(x1=95, y1=95, x2=105, y2=105), # Partly outside (5x5 inside)
        BoundingBox(x1=20, y1=20, x2=20, y2=20), # Zero area
        BoundingBox(x1=30, y1=30, x2=25, y2=25) # Degenerate (x1 > x2)
    ]
    assert union_area_px([], 100, 100) == 0
    
    union_area = union_area_px(boxes, 100, 100)
    # Only the partly outside box contributes inside the canvas (95 to 100 is 5, 95 to 100 is 5 => 25)
    assert union_area == 25

def test_closest_approach_stability(mock_config):
    """
    Same physical pothole at different distances: closest-approach severity is stable 
    while per-frame severity varies.
    """
    # Simulate a pothole moving closer (y increases, box area increases)
    obs = [
        TrackObservation(track_id=1, class_name="pothole", frame_idx=1, bbox=BoundingBox(x1=40, y1=40, x2=60, y2=60), confidence=0.8, frame_w=100, frame_h=100),
        TrackObservation(track_id=1, class_name="pothole", frame_idx=2, bbox=BoundingBox(x1=30, y1=50, x2=70, y2=90), confidence=0.9, frame_w=100, frame_h=100),
        TrackObservation(track_id=1, class_name="pothole", frame_idx=3, bbox=BoundingBox(x1=35, y1=45, x2=65, y2=80), confidence=0.85, frame_w=100, frame_h=100) # Receding/smaller
    ]
    
    closest = closest_approach(obs, mock_config["tracking"]["min_track_frames"])
    assert closest.frame_idx == 2 # Largest area, lowest in frame (y2=90)
    
    ratios = [near_zone_area_ratio(o.bbox, o.frame_w, o.frame_h, mock_config["severity"]) for o in obs]
    severities = [severity_label(r, mock_config["severity"]) for r in ratios]
    
    # Near zone is y=50 to 100, area is 100*50 = 5000
    # Obs 1: y1=40 to y2=60, clipped near zone y=50 to 60 -> w=20, h=10 -> area=200. Ratio = 200/5000 = 0.04 (Medium)
    # Obs 2: y1=50 to y2=90, near zone y=50 to 90 -> w=40, h=40 -> area=1600. Ratio = 1600/5000 = 0.32 (High)
    assert severities[0] == "Medium"
    assert severities[1] == "High"
    
    closest_ratio = near_zone_area_ratio(closest.bbox, closest.frame_w, closest.frame_h, mock_config["severity"])
    closest_sev = severity_label(closest_ratio, mock_config["severity"])
    assert closest_sev == "High"

def test_closest_approach_edge_cases(mock_config):
    """Handles short tracks, single observation ties."""
    obs_short = [
        TrackObservation(track_id=1, class_name="pothole", frame_idx=1, bbox=BoundingBox(x1=0,y1=0,x2=10,y2=10), confidence=0.9, frame_w=100, frame_h=100)
    ]
    # Too short -> None
    assert closest_approach(obs_short, mock_config["tracking"]["min_track_frames"]) is None
    
    # Tie breaking: same y2, pick largest area
    obs_tie = [
        TrackObservation(track_id=2, class_name="pothole", frame_idx=1, bbox=BoundingBox(x1=10,y1=80,x2=20,y2=90), confidence=0.9, frame_w=100, frame_h=100),
        TrackObservation(track_id=2, class_name="pothole", frame_idx=2, bbox=BoundingBox(x1=10,y1=70,x2=30,y2=90), confidence=0.9, frame_w=100, frame_h=100),
        TrackObservation(track_id=2, class_name="pothole", frame_idx=3, bbox=BoundingBox(x1=10,y1=75,x2=15,y2=90), confidence=0.9, frame_w=100, frame_h=100)
    ]
    closest = closest_approach(obs_tie, 1) # Override min_track_frames to 1 for this test
    assert closest.frame_idx == 2 # Area 20x20=400 vs 10x10=100 vs 5x15=75

def test_severity_boundary_values(mock_config):
    """Severity boundary values (exactly 0.02, 0.08, just below/above)."""
    cfg = mock_config["severity"]
    assert severity_label(0.019, cfg) == "Low"
    assert severity_label(0.020, cfg) == "Medium" # Exact match -> higher class
    assert severity_label(0.021, cfg) == "Medium"
    assert severity_label(0.079, cfg) == "Medium"
    assert severity_label(0.080, cfg) == "High"   # Exact match -> higher class
    assert severity_label(0.081, cfg) == "High"

def test_condition_from_index_legacy_reproduction(mock_config):
    """condition_from_index reproduces the old rules for a table of inputs."""
    cfg = mock_config["condition"]
    # Legacy: < fair_min_index is Good, < poor_min_index is Fair, >= poor_min_index is Poor
    assert condition_from_index(0.0, cfg) == "Good"
    assert condition_from_index(0.049, cfg) == "Good"
    assert condition_from_index(0.05, cfg) == "Fair"
    assert condition_from_index(0.149, cfg) == "Fair"
    assert condition_from_index(0.15, cfg) == "Poor"
    assert condition_from_index(1.0, cfg) == "Poor"
