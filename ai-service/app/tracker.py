from typing import Any, Protocol

from app.schemas import BoundingBox, Detection, TrackObservation

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None


class Tracker(Protocol):
    def track(self, image_data: Any, frame_idx: int) -> list[Detection]:
        ...


class RoadDamageTracker:
    def __init__(self, model_path: str, tracker_config: str = "bytetrack.yaml", conf_thres: float = 0.25):
        if YOLO is None:
            raise ImportError("ultralytics is required for RoadDamageTracker")
        self.model = YOLO(model_path)
        self.tracker_config = tracker_config
        self.conf_thres = conf_thres

    def track(self, image_data: Any, frame_idx: int) -> list[Detection]:
        # Ultralytics track returns a list of Results (one per image if batch=1)
        results = self.model.track(image_data, persist=True, tracker=self.tracker_config, conf=self.conf_thres, verbose=False)
        detections = []
        for r in results:
            if r.boxes is None:
                continue
            
            names = self.model.names
            for box in r.boxes:
                cls_id = int(box.cls[0].item())
                cls_name = names.get(cls_id, f"cls_{cls_id}")
                conf = float(box.conf[0].item())
                
                # xyxy is [x1, y1, x2, y2]
                xyxy = box.xyxy[0].tolist()
                
                track_id = None
                if box.id is not None:
                    track_id = int(box.id[0].item())
                    
                detections.append(Detection(
                    class_name=cls_name,
                    confidence=conf,
                    bbox=BoundingBox(x1=xyxy[0], y1=xyxy[1], x2=xyxy[2], y2=xyxy[3]),
                    track_id=track_id
                ))
        return detections


class FakeTracker:
    def __init__(self, scripted_detections: dict[int, list[Detection]]):
        self.scripted = scripted_detections

    def track(self, image_data: Any, frame_idx: int) -> list[Detection]:
        return self.scripted.get(frame_idx, [])


def group_into_tracks(detections_stream: list[tuple[int, list[Detection]]], frame_w: int, frame_h: int, min_track_frames: int) -> list[list[TrackObservation]]:
    """
    Takes a stream of (frame_idx, detections) and groups them by track_id.
    Drops tracks shorter than min_track_frames.
    """
    track_dict: dict[int, list[TrackObservation]] = {}
    for frame_idx, detections in detections_stream:
        for det in detections:
            if det.track_id is None:
                continue
                
            obs = TrackObservation(
                track_id=det.track_id,
                class_name=det.class_name,
                frame_idx=frame_idx,
                bbox=det.bbox,
                confidence=det.confidence,
                frame_w=frame_w,
                frame_h=frame_h
            )
            
            if det.track_id not in track_dict:
                track_dict[det.track_id] = []
            track_dict[det.track_id].append(obs)
            
    # Filter by min_track_frames
    return [obs_list for obs_list in track_dict.values() if len(obs_list) >= min_track_frames]
