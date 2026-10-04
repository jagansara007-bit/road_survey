from typing import Any, Protocol

import numpy as np
import onnxruntime as ort
from app.config_loader import get_classes, get_detector_config
from app.schemas import BoundingBox, Detection


class Detector(Protocol):
    def detect(self, image_data: Any) -> list[Detection]:
        ...

def _xywh2xyxy(x: np.ndarray) -> np.ndarray:
    # Convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2]
    # where xy1=top-left, xy2=bottom-right
    y = np.copy(x)
    y[..., 0] = x[..., 0] - x[..., 2] / 2  # top left x
    y[..., 1] = x[..., 1] - x[..., 3] / 2  # top left y
    y[..., 2] = x[..., 0] + x[..., 2] / 2  # bottom right x
    y[..., 3] = x[..., 1] + x[..., 3] / 2  # bottom right y
    return y

def _nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float = 0.45) -> list[int]:
    """Non-Maximum Suppression."""
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h

        iou = inter / (areas[i] + areas[order[1:]] - inter)

        inds = np.where(iou <= iou_threshold)[0]
        order = order[inds + 1]

    return keep

class RoadDamageDetector:
    """
    Detector abstraction wrapper. Supports mock inference during bootstrap/CI
    and ONNX YOLOv8 when model weights are provided.
    """

    def __init__(self, model_path: str = "", cfg: dict[str, Any] | None = None):
        self.model_path = model_path
        self.classes = get_classes()
        self.session = None
        self.input_name = None
        
        det_cfg = (cfg or {}).get("detector", get_detector_config())
        self.conf_thres = det_cfg.get("conf_thres", 0.25)
        self.iou_threshold = det_cfg.get("iou_threshold", 0.45)
        self.input_size = det_cfg.get("input_size", 640)
        
        if model_path:
            try:
                self.session = ort.InferenceSession(model_path)
                self.input_name = self.session.get_inputs()[0].name
            except Exception:  # noqa: BLE001
                self.session = None

    def detect(self, image_data: Any) -> list[Detection]:
        if self.session is not None:
            # Assuming image_data is an un-normalized, RGB HxWxC np.ndarray or PIL Image
            if not isinstance(image_data, np.ndarray):
                image_data = np.array(image_data)
            
            # Simple pre-processing for YOLOv8
            import cv2
            img = cv2.resize(image_data, (self.input_size, self.input_size))
            img = img.transpose((2, 0, 1)) # HWC to CHW
            img = np.expand_dims(img, axis=0) # 1CHW
            img = img.astype(np.float32) / 255.0
            
            outputs = self.session.run(None, {self.input_name: img})[0]
            # YOLOv8 ONNX output shape: [1, 4 + num_classes, 8400]
            outputs = np.transpose(np.squeeze(outputs, 0)) # [8400, 4 + num_classes]
            
            boxes = outputs[:, :4]
            scores = outputs[:, 4:]
            class_ids = np.argmax(scores, axis=1)
            class_scores = np.max(scores, axis=1)
            
            # Filter by conf threshold
            mask = class_scores > self.conf_thres
            boxes = boxes[mask]
            class_scores = class_scores[mask]
            class_ids = class_ids[mask]
            
            boxes = _xywh2xyxy(boxes)
            
            keep = _nms(boxes, class_scores, iou_threshold=self.iou_threshold)
            
            detections: list[Detection] = []
            class_names = list(self.classes.keys())
            for i in keep:
                cls_id = int(class_ids[i])
                cls_name = class_names[cls_id] if cls_id < len(class_names) else f"cls_{cls_id}"
                conf = float(class_scores[i])
                box = boxes[i].tolist()
                detections.append(Detection(
                    class_name=cls_name,
                    confidence=conf,
                    bbox=BoundingBox(x1=box[0], y1=box[1], x2=box[2], y2=box[3])
                ))
            return detections
        # Return empty list in mock/bootstrap mode
        return []
