"""
Repository classes for surveys, defects, and segments.
All SQL is parameterised. No SQL outside app/db/ (ADR-0002).
"""
import sqlite3
from typing import Any


class SurveyRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, surveyed_on: str, route_name: str, source: str | None = None) -> int:
        cur = self.conn.execute(
            "INSERT INTO surveys (surveyed_on, route_name, source) VALUES (?, ?, ?)",
            (surveyed_on, route_name, source),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def update_status(self, survey_id: int, status: str) -> None:
        self.conn.execute(
            "UPDATE surveys SET status = ? WHERE survey_id = ?",
            (status, survey_id),
        )
        self.conn.commit()

    def get(self, survey_id: int) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM surveys WHERE survey_id = ?", (survey_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_all(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM surveys ORDER BY survey_id DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def defect_count(self, survey_id: int) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) FROM defects WHERE survey_id = ?", (survey_id,)
        ).fetchone()
        return row[0] if row else 0

    def segment_count(self, survey_id: int) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) FROM segments WHERE survey_id = ?", (survey_id,)
        ).fetchone()
        return row[0] if row else 0


class DefectRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def insert(self, survey_id: int, defect: dict[str, Any]) -> int:
        cur = self.conn.execute(
            """INSERT INTO defects
            (survey_id, class, lat, lon, severity, area_px, confidence,
             priority, estimated_cost, status, recurrence, unverified,
             matched_prev_id, crop_path, bbox_x1, bbox_y1, bbox_x2, bbox_y2)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                survey_id,
                defect["class_name"],
                defect["lat"],
                defect["lon"],
                defect["severity"],
                defect.get("area_px"),
                defect.get("confidence"),
                defect.get("priority"),
                defect.get("estimated_cost"),
                defect.get("status", "New"),
                defect.get("recurrence", False),
                defect.get("unverified", False),
                defect.get("matched_prev_id"),
                defect.get("crop_path"),
                defect.get("bbox_x1"),
                defect.get("bbox_y1"),
                defect.get("bbox_x2"),
                defect.get("bbox_y2"),
            ),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def insert_many(self, survey_id: int, defects: list[dict[str, Any]]) -> list[int]:
        ids = []
        for d in defects:
            ids.append(self.insert(survey_id, d))
        return ids

    def get(self, defect_id: int) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM defects WHERE defect_id = ?", (defect_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_survey(self, survey_id: int) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM defects WHERE survey_id = ? ORDER BY defect_id",
            (survey_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def update_status(
        self,
        defect_id: int,
        status: str,
        matched_prev_id: int | None = None,
        recurrence: bool = False,
        unverified: bool = False,
    ) -> None:
        self.conn.execute(
            """UPDATE defects
            SET status = ?, matched_prev_id = ?, recurrence = ?, unverified = ?
            WHERE defect_id = ?""",
            (status, matched_prev_id, recurrence, unverified, defect_id),
        )
        self.conn.commit()


class SegmentRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def insert(self, survey_id: int, segment: dict[str, Any]) -> int:
        cur = self.conn.execute(
            """INSERT INTO segments
            (survey_id, start_m, end_m, damage_index, condition)
            VALUES (?, ?, ?, ?, ?)""",
            (
                survey_id,
                segment["start_m"],
                segment["end_m"],
                segment["damage_index"],
                segment["condition"],
            ),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def insert_many(self, survey_id: int, segments: list[dict[str, Any]]) -> list[int]:
        ids = []
        for s in segments:
            ids.append(self.insert(survey_id, s))
        return ids

    def list_by_survey(self, survey_id: int) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM segments WHERE survey_id = ? ORDER BY start_m",
            (survey_id,),
        ).fetchall()
        return [dict(r) for r in rows]
