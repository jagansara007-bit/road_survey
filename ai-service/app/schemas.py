
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class Detection(BaseModel):
    class_name: str
    confidence: float
    bbox: BoundingBox = Field(..., description="[x1, y1, x2, y2] in pixel or normalized coordinates")
    orientation: str | None = None
    track_id: int | None = None
    lat: float | None = None
    lon: float | None = None

class InferenceResult(BaseModel):
    detections: list[Detection]


class TrackObservation(BaseModel):
    track_id: int
    class_name: str
    frame_idx: int
    bbox: BoundingBox
    confidence: float
    frame_w: int
    frame_h: int


class DefectObservationSummary(BaseModel):
    track_id: int
    class_name: str
    severity: str
    closest_approach_frame: int
    max_area_ratio: float

class DefectAssessment(BaseModel):
    defect_id: int | None = None
    class_name: str
    severity: str
    area_ratio: float
    confidence: float
    priority: float | None = None
    lat: float | None = None
    lon: float | None = None


class GPSPoint(BaseModel):
    timestamp_s: float
    lat: float
    lon: float
    accuracy_m: float | None = None
    speed_mps: float | None = None


class Defect(BaseModel):
    defect_id: int
    class_name: str
    lat: float
    lon: float
    severity: str
    area_px: float
    confidence: float
    track_ids: list[int]
    bbox: BoundingBox | None = None
    priority: float | None = None
    estimated_cost: float | None = None
    survey_id: int | None = None
    status: str = "New"
    recurrence: bool = False
    unverified: bool = False
    matched_prev_id: int | None = None
    crop_path: str | None = None

class QueueItem(BaseModel):
    defect: Defect
    selected: bool


class QueueResult(BaseModel):
    selected: list[Defect]
    skipped: list[Defect]
    remaining_budget: float


class SegmentCondition(BaseModel):
    segment_id: int | None = None
    start_m: float
    end_m: float
    damage_index: float
    condition: str


class SurveyResponse(BaseModel):
    survey_id: int | None = None
    defects: list[Defect]
    segments: list[SegmentCondition]
