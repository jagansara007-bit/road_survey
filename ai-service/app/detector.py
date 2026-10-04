from typing import Any

from app.config_loader import get_classes
from app.schemas import Detection


class RoadDamageDetector:
    """
    Detector abstraction wrapper. Supports mock inference during bootstrap/CI
    and Ultralytics YOLOv8 / ByteTrack tracking when model weights are provided.
    """

    def __init__(self, model_path: str = ""):
        self.model_path = model_path
        self.classes = get_classes()
        self.model: Any = None
        if model_path:
            try:
                from ultralytics import YOLO
                self.model = YOLO(model_path)
            except (ImportError, RuntimeError, Exception):  # noqa: BLE001
                self.model = None

    def detect(self, image_data: Any) -> list[Detection]:
        if self.model is not None:
            results = self.model.predict(image_data)
            detections: list[Detection] = []
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0].item())
                    cls_name = list(self.classes.keys())[cls_id] if cls_id < len(self.classes) else f"cls_{cls_id}"
                    conf = float(box.conf[0].item())
                    xyxy = [float(x) for x in box.xyxy[0].tolist()]
                    detections.append(Detection(class_name=cls_name, confidence=conf, bbox=xyxy))
            return detections
        # Return empty list in mock/bootstrap mode
        return []

    def track(self, source: Any) -> list[Detection]:
        if self.model is not None:
            results = self.model.track(source, persist=True)
            detections: list[Detection] = []
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0].item())
                    cls_name = list(self.classes.keys())[cls_id] if cls_id < len(self.classes) else f"cls_{cls_id}"
                    conf = float(box.conf[0].item())
                    xyxy = [float(x) for x in box.xyxy[0].tolist()]
                    track_id = int(box.id[0].item()) if box.id is not None else None
                    detections.append(Detection(class_name=cls_name, confidence=conf, bbox=xyxy, track_id=track_id))
            return detections
        return []
