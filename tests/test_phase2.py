import numpy as np
from app.detector import _nms, _xywh2xyxy
from app.schemas import BoundingBox, Detection


def test_xywh2xyxy():
    boxes = np.array([[10, 10, 4, 4]])
    out = _xywh2xyxy(boxes)
    # Expected: x1=10-2=8, y1=10-2=8, x2=10+2=12, y2=10+2=12
    assert np.allclose(out, [[8, 8, 12, 12]])

def test_nms():
    # Two highly overlapping boxes
    boxes = np.array([
        [0, 0, 10, 10],
        [1, 1, 11, 11]
    ])
    scores = np.array([0.9, 0.8])
    keep = _nms(boxes, scores, iou_threshold=0.5)
    assert keep == [0]

    # Two non-overlapping boxes
    boxes = np.array([
        [0, 0, 10, 10],
        [20, 20, 30, 30]
    ])
    scores = np.array([0.9, 0.8])
    keep = _nms(boxes, scores, iou_threshold=0.5)
    assert set(keep) == {0, 1}

def test_schemas():
    bbox = BoundingBox(x1=0, y1=0, x2=10, y2=10)
    det = Detection(class_name="crack", confidence=0.9, bbox=bbox)
    assert det.class_name == "crack"
    assert det.bbox.x2 == 10
