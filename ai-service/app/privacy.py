import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import cv2
import numpy as np
from app.config_loader import get_privacy_config

logger = logging.getLogger(__name__)


@runtime_checkable
class Redactor(Protocol):
    """
    Protocol for pluggable privacy redactors.
    """
    def redact(self, image: np.ndarray) -> np.ndarray:
        ...

    def detect_sensitive_regions(self, image: np.ndarray) -> list[tuple[int, int, int, int, str]]:
        ...


def blur_bounding_box(image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
    """
    Applies strong Gaussian blur to the specified bounding box within an image.
    Modifies image in-place and returns it.
    """
    h, w = image.shape[:2]
    x1_c = max(0, min(w - 1, int(x1)))
    y1_c = max(0, min(h - 1, int(y1)))
    x2_c = max(x1_c + 1, min(w, int(x2)))
    y2_c = max(y1_c + 1, min(h, int(y2)))

    roi_w = x2_c - x1_c
    roi_h = y2_c - y1_c
    if roi_w <= 0 or roi_h <= 0:
        return image

    roi = image[y1_c:y2_c, x1_c:x2_c]
    # Choose strong kernel proportional to box size
    ksize_w = max(15, (roi_w // 3) * 2 + 1)
    ksize_h = max(15, (roi_h // 3) * 2 + 1)
    ksize = max(ksize_w, ksize_h)
    if ksize % 2 == 0:
        ksize += 1

    blurred_roi = cv2.GaussianBlur(roi, (ksize, ksize), sigmaX=30.0)
    image[y1_c:y2_c, x1_c:x2_c] = blurred_roi
    return image


class DefaultOfflineRedactor:
    """
    Offline privacy redactor supporting heuristic face and license-plate detection.
    Runs entirely local with no internet connection or external API calls.
    """

    def __init__(
        self,
        blur_faces: bool = True,
        blur_plates: bool = True,
        custom_face_detector: Callable[[np.ndarray], list[tuple[int, int, int, int]]] | None = None,
        custom_plate_detector: Callable[[np.ndarray], list[tuple[int, int, int, int]]] | None = None,
    ):
        self.blur_faces = blur_faces
        self.blur_plates = blur_plates
        self.custom_face_detector = custom_face_detector
        self.custom_plate_detector = custom_plate_detector

    def _detect_faces_heuristic(self, image: np.ndarray) -> list[tuple[int, int, int, int]]:
        """
        Detects face-like regions using skin-color segmentation in YCrCb color space
        and morphological geometry filtering.
        """
        if image is None or image.size == 0 or len(image.shape) < 3:
            return []

        h, w = image.shape[:2]
        img_area = h * w
        ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
        
        # Standard human skin tone mask in YCrCb space
        # Cr: 133 to 173, Cb: 77 to 127
        lower = np.array([0, 133, 77], dtype=np.uint8)
        upper = np.array([255, 173, 127], dtype=np.uint8)
        skin_mask = cv2.inRange(ycrcb, lower, upper)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_DILATE, kernel)

        contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            area = bw * bh
            aspect_ratio = bh / max(1.0, float(bw))
            # Human faces are typically roughly oval/vertical (aspect ratio 0.8 to 2.2)
            # Area between 0.5% and 40% of the image
            if 0.005 * img_area <= area <= 0.40 * img_area and 0.8 <= aspect_ratio <= 2.2:
                boxes.append((x, y, x + bw, y + bh))

        return boxes

    def _detect_plates_heuristic(self, image: np.ndarray) -> list[tuple[int, int, int, int]]:
        """
        Detects vehicle license-plate candidates via horizontal gradient density
        and rectangular aspect-ratio filtering (Indian plates ~ 2.0 to 5.0).
        """
        if image is None or image.size == 0:
            return []

        h, w = image.shape[:2]
        img_area = h * w
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) >= 3 else image

        # Horizontal Sobel edge response
        grad_x = cv2.Sobel(gray, cv2.CV_16S, 1, 0, ksize=3)
        abs_grad_x = cv2.convertScaleAbs(grad_x)

        # Threshold and morphology
        _, thresh = cv2.threshold(abs_grad_x, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            area = bw * bh
            aspect_ratio = bw / max(1.0, float(bh))
            # Indian vehicle registration plates have aspect ratios between 2.0 and 5.5
            if 0.002 * img_area <= area <= 0.25 * img_area and 1.8 <= aspect_ratio <= 5.5:
                boxes.append((x, y, x + bw, y + bh))

        return boxes

    def detect_sensitive_regions(self, image: np.ndarray) -> list[tuple[int, int, int, int, str]]:
        regions: list[tuple[int, int, int, int, str]] = []

        if self.blur_faces:
            if self.custom_face_detector is not None:
                face_boxes = self.custom_face_detector(image)
            else:
                face_boxes = self._detect_faces_heuristic(image)
            for x1, y1, x2, y2 in face_boxes:
                regions.append((x1, y1, x2, y2, "face"))

        if self.blur_plates:
            if self.custom_plate_detector is not None:
                plate_boxes = self.custom_plate_detector(image)
            else:
                plate_boxes = self._detect_plates_heuristic(image)
            for x1, y1, x2, y2 in plate_boxes:
                regions.append((x1, y1, x2, y2, "license_plate"))

        return regions

    def redact(self, image: np.ndarray) -> np.ndarray:
        if image is None or image.size == 0:
            return image

        output = image.copy()
        regions = self.detect_sensitive_regions(output)
        for x1, y1, x2, y2, _label in regions:
            blur_bounding_box(output, x1, y1, x2, y2)

        return output


def get_default_redactor(cfg: dict[str, Any] | None = None) -> Redactor:
    privacy_cfg = (cfg or {}).get("privacy", get_privacy_config())
    blur_faces = privacy_cfg.get("blur_faces", True)
    blur_plates = privacy_cfg.get("blur_plates", True)
    return DefaultOfflineRedactor(blur_faces=blur_faces, blur_plates=blur_plates)


def blur_crop(
    image: Any,
    cfg: dict[str, Any] | None = None,
    redactor: Redactor | None = None
) -> Any:
    """
    Applies privacy blurring (faces and license plates) to the given image crop or frame.
    Must be invoked BEFORE persisting any crop or frame to disk.
    """
    if image is None:
        return image

    if not isinstance(image, np.ndarray):
        img_np = np.array(image)
    else:
        img_np = image

    active_redactor = redactor or get_default_redactor(cfg)
    return active_redactor.redact(img_np)


def measure_blur_recall(sample_dir: str | Path) -> dict[str, Any]:
    """
    Measures blur recall on hand-labelled evaluation samples if present.
    If no labelled sample directory is found, returns NOT MEASURED with exit 0 semantics.
    """
    p = Path(sample_dir)
    if not p.exists() or not (p / "labels.csv").exists():
        return {
            "status": "NOT MEASURED",
            "reason": f"No labelled sample directory found at {p}",
            "sample_size": 0,
            "face_recall": None,
            "plate_recall": None,
        }

    # If samples exist, compute IoU against detected blur regions
    import csv
    with open(p / "labels.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return {
            "status": "NOT MEASURED",
            "reason": "Empty labels.csv",
            "sample_size": 0,
            "face_recall": None,
            "plate_recall": None,
        }

    redactor = get_default_redactor()
    tp_faces = 0
    total_faces = 0
    tp_plates = 0
    total_plates = 0

    for row in rows:
        img_path = p / row["filename"]
        if not img_path.exists():
            continue
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        detected = redactor.detect_sensitive_regions(img)
        gt_class = row["class"]
        gt_box = (int(row["x1"]), int(row["y1"]), int(row["x2"]), int(row["y2"]))

        # Check overlap
        matched = False
        for dx1, dy1, dx2, dy2, dclass in detected:
            if dclass == gt_class:
                # Calculate IoU
                ix1 = max(gt_box[0], dx1)
                iy1 = max(gt_box[1], dy1)
                ix2 = min(gt_box[2], dx2)
                iy2 = min(gt_box[3], dy2)
                inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                union = (gt_box[2] - gt_box[0]) * (gt_box[3] - gt_box[1]) + (dx2 - dx1) * (dy2 - dy1) - inter
                iou = inter / max(1.0, float(union))
                if iou >= 0.3:
                    matched = True
                    break

        if gt_class == "face":
            total_faces += 1
            if matched:
                tp_faces += 1
        elif gt_class == "license_plate":
            total_plates += 1
            if matched:
                tp_plates += 1

    face_recall = (tp_faces / total_faces) if total_faces > 0 else 0.0
    plate_recall = (tp_plates / total_plates) if total_plates > 0 else 0.0

    return {
        "status": "MEASURED",
        "sample_size": len(rows),
        "total_faces": total_faces,
        "face_recall": face_recall,
        "total_plates": total_plates,
        "plate_recall": plate_recall,
    }
