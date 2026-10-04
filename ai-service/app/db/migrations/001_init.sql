-- 001_init.sql: Initial schema for Road Damage Detection system
-- See docs/DATA_MODEL.md for field documentation.

CREATE TABLE IF NOT EXISTS surveys (
    survey_id   INTEGER PRIMARY KEY,
    surveyed_on DATE    NOT NULL,
    route_name  TEXT    NOT NULL,
    source      TEXT,
    status      TEXT    NOT NULL DEFAULT 'processing',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS defects (
    defect_id       INTEGER PRIMARY KEY,
    survey_id       INTEGER NOT NULL REFERENCES surveys(survey_id),
    class           TEXT    NOT NULL,
    lat             REAL    NOT NULL,
    lon             REAL    NOT NULL,
    severity        TEXT    NOT NULL,
    area_px         INTEGER,
    confidence      REAL,
    priority        REAL,
    estimated_cost  REAL,
    status          TEXT    NOT NULL DEFAULT 'New',
    recurrence      BOOLEAN NOT NULL DEFAULT 0,
    unverified      BOOLEAN NOT NULL DEFAULT 0,
    matched_prev_id INTEGER,
    crop_path       TEXT,
    bbox_x1         REAL,
    bbox_y1         REAL,
    bbox_x2         REAL,
    bbox_y2         REAL,
    review_status   TEXT
);

CREATE TABLE IF NOT EXISTS segments (
    segment_id  INTEGER PRIMARY KEY,
    survey_id   INTEGER NOT NULL REFERENCES surveys(survey_id),
    start_m     REAL    NOT NULL,
    end_m       REAL    NOT NULL,
    damage_index REAL   NOT NULL,
    condition   TEXT    NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_defects_survey_id ON defects(survey_id);
CREATE INDEX IF NOT EXISTS idx_defects_status    ON defects(status);
CREATE INDEX IF NOT EXISTS idx_defects_location  ON defects(lat, lon);
CREATE INDEX IF NOT EXISTS idx_segments_survey_id ON segments(survey_id);
