import os
import sqlite3

import pytest
from app.db.migration_runner import run_migrations
from app.main import app
from app.schemas import Defect
from app.verify import verify_survey
from fastapi.testclient import TestClient


def test_verify_survey_logic():
    old_defects = [
        Defect(defect_id=1, class_name="D40", lat=10.0, lon=20.0, severity="High", area_px=100, confidence=0.9, track_ids=[], status="Repaired"),
        Defect(defect_id=2, class_name="D00", lat=10.0, lon=20.0001, severity="Medium", area_px=50, confidence=0.8, track_ids=[], status="Open"),
        Defect(defect_id=3, class_name="D10", lat=50.0, lon=60.0, severity="Low", area_px=10, confidence=0.7, track_ids=[], status="Open"),
    ]
    
    new_defects = [
        Defect(defect_id=4, class_name="D40", lat=10.0, lon=20.0, severity="High", area_px=100, confidence=0.9, track_ids=[]), # Matches 1 -> Failed
        Defect(defect_id=5, class_name="D00", lat=10.0, lon=20.0001, severity="Medium", area_px=50, confidence=0.8, track_ids=[]), # Matches 2 -> Open
        Defect(defect_id=6, class_name="D20", lat=30.0, lon=40.0, severity="High", area_px=150, confidence=0.95, track_ids=[]), # New
    ]
    
    from app.gps import GPSPoint
    # Path covers defect 3
    path = [GPSPoint(timestamp_s=0, lat=50.0, lon=60.00001)]
    
    cfg = {"verification": {"match_radius_m": 10.0, "coverage_radius_m": 15.0}}
    
    old_out, new_out = verify_survey(old_defects, new_defects, path, cfg)
    
    # Check old
    assert old_out[0].status == "Failed"
    assert old_out[0].recurrence is True
    
    assert old_out[1].status == "Open"
    
    assert old_out[2].status == "Repaired"
    
    # Check new
    assert new_out[0].status == "Failed"
    assert new_out[0].matched_prev_id == 1
    assert new_out[0].recurrence is True
    
    assert new_out[1].status == "Open"
    assert new_out[1].matched_prev_id == 2
    
    assert new_out[2].status == "New"
    
    
def test_migrations_idempotency_and_fk(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=ON")
    
    migrations_dir = os.path.join(os.path.dirname(__file__), "..", "app", "db", "migrations")
    
    # Run first time
    count = run_migrations(conn, migrations_dir)
    assert count > 0
    
    # Run second time
    count2 = run_migrations(conn, migrations_dir)
    assert count2 == 0
    
    # Test FK enforcement
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO defects (survey_id, class, lat, lon, severity) VALUES (999, 'D40', 0, 0, 'Low')")


client = TestClient(app)

def test_api_security():
    res = client.get("/api/v1/surveys")
    assert res.status_code == 401
    
    res = client.get("/health")
    assert res.status_code == 200

def test_api_upload_validation():
    # Bad extension
    res = client.post(
        "/api/v1/surveys",
        headers={"X-API-Key": "dev-secret-key"},
        data={"route_name": "Test", "surveyed_on": "2024-01-01"},
        files={
            "video": ("test.txt", b"dummy content"),
            "gps": ("test.csv", b"lat,lon\n0,0")
        }
    )
    assert res.status_code == 400
    
    # Oversize
    res = client.post(
        "/api/v1/surveys",
        headers={"X-API-Key": "dev-secret-key", "Content-Length": str(100 * 1024 * 1024)},  # 100MB
        data={"route_name": "Test", "surveyed_on": "2024-01-01"},
        files={
            "video": ("test.mp4", b"dummy content"),
            "gps": ("test.csv", b"lat,lon\n0,0")
        }
    )
    assert res.status_code == 413

    # Disguised .exe
    res = client.post(
        "/api/v1/surveys",
        headers={"X-API-Key": "dev-secret-key"},
        data={"route_name": "Test", "surveyed_on": "2024-01-01"},
        files={
            "video": ("malicious.mp4", b"MZ\x90\x00\x03\x00executable content"),
            "gps": ("test.csv", b"lat,lon\n0,0")
        }
    )
    assert res.status_code == 400
    assert "Executable file disguised as video" in res.json()["detail"]
