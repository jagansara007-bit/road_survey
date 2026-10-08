import os
import sqlite3
from typing import Any

from app.config_loader import load_thresholds
from app.db.migration_runner import open_db
from app.db.repository import DefectRepo, SegmentRepo, SurveyRepo
from app.detector import RoadDamageDetector
from app.tracker import RoadDamageTracker
from fastapi import Depends

# Shared single connection for the application (ADR-0002)
_DB_CONN: sqlite3.Connection | None = None
# Shared detector and tracker
_DETECTOR: RoadDamageDetector | None = None
_TRACKER: RoadDamageTracker | None = None


def get_db_conn() -> sqlite3.Connection:
    global _DB_CONN
    if _DB_CONN is None:
        db_path = os.environ.get("DB_PATH", "road_damage.sqlite")
        _DB_CONN = open_db(db_path)
    return _DB_CONN


def get_survey_repo(conn: sqlite3.Connection = Depends(get_db_conn)) -> SurveyRepo:
    return SurveyRepo(conn)


def get_defect_repo(conn: sqlite3.Connection = Depends(get_db_conn)) -> DefectRepo:
    return DefectRepo(conn)


def get_segment_repo(conn: sqlite3.Connection = Depends(get_db_conn)) -> SegmentRepo:
    return SegmentRepo(conn)


def get_config() -> dict:
    return load_thresholds()


def get_tracker() -> Any:
    # Usually instantiated in a background task
    global _TRACKER
    if _TRACKER is None:
        model_path = os.environ.get("MODEL_PATH", "")
        if not model_path:
            candidates = [
                os.path.join(os.getcwd(), "models", "best.pt"),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "models", "best.pt"),
                os.path.join(os.path.dirname(__file__), "..", "..", "models", "best.pt"),
            ]
            for candidate in candidates:
                if os.path.exists(candidate):
                    model_path = os.path.abspath(candidate)
                    break
        from app.tracker import FakeTracker
        if not model_path:
            return FakeTracker({})
        try:
            _TRACKER = RoadDamageTracker(model_path)
        except Exception:
            return FakeTracker({})
    return _TRACKER
