
from app.condition import compute_segment_condition
from app.config_loader import load_thresholds
from app.schemas import DefectAssessment, Detection, SurveyResponse
from app.severity import assess_defect_severity
from fastapi import FastAPI

app = FastAPI(title="Road Damage AI Microservice", version="0.1.0")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config")
def get_config() -> dict:
    return load_thresholds()


@app.post("/analyze/frame", response_model=SurveyResponse)
def analyze_frame(detections: list[Detection]) -> SurveyResponse:
    defects = []
    # Assume default 1080p frame dimensions if not provided
    img_h, img_w = 1080, 1920
    for idx, det in enumerate(detections):
        sev, ratio = assess_defect_severity(det.bbox, (img_h, img_w))
        defects.append(
            DefectAssessment(
                defect_id=idx + 1,
                class_name=det.class_name,
                severity=sev,
                area_ratio=ratio,
                confidence=det.confidence,
                lat=det.lat,
                lon=det.lon,
            )
        )

    segment = compute_segment_condition(detections, segment_length_m=50.0, start_m=0.0)
    return SurveyResponse(survey_id=1, defects=defects, segments=[segment])
