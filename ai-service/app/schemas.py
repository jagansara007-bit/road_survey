
from pydantic import BaseModel, Field


class Detection(BaseModel):
    class_name: str
    confidence: float
    bbox: list[float] = Field(..., description="[x1, y1, x2, y2] in pixel or normalized coordinates")
    track_id: int | None = None
    lat: float | None = None
    lon: float | None = None


class DefectAssessment(BaseModel):
    defect_id: int | None = None
    class_name: str
    severity: str
    area_ratio: float
    confidence: float
    priority: float | None = None
    lat: float | None = None
    lon: float | None = None


class SegmentCondition(BaseModel):
    segment_id: int | None = None
    start_m: float
    end_m: float
    damage_index: float
    condition: str


class SurveyResponse(BaseModel):
    survey_id: int | None = None
    defects: list[DefectAssessment]
    segments: list[SegmentCondition]
