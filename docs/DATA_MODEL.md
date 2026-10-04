# Data Model

This document defines the authoritative SQLite schema for the Road Damage Detection system. See also [ADR-0002](decisions/ADR-0002-single-sqlite-writer.md) for the database access policy.

## Tables

### surveys

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| survey_id | INTEGER | PRIMARY KEY | Auto-incremented survey identifier |
| surveyed_on | DATE | NOT NULL | Date the survey was conducted |
| route_name | TEXT | NOT NULL | Human-readable route label |
| source | TEXT | | Original video filename (server-side random name) |
| status | TEXT | NOT NULL DEFAULT 'processing' | processing / completed / failed |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation time |

### defects

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| defect_id | INTEGER | PRIMARY KEY | Auto-incremented defect identifier |
| survey_id | INTEGER | FK → surveys, NOT NULL | Parent survey |
| class | TEXT | NOT NULL | Defect class (e.g., D40, crack, alligator_crack) |
| lat | REAL | NOT NULL | WGS84 latitude |
| lon | REAL | NOT NULL | WGS84 longitude |
| severity | TEXT | NOT NULL | Low / Medium / High |
| area_px | INTEGER | | Bounding box area in pixels |
| confidence | REAL | | Detection confidence score |
| priority | REAL | | Computed priority score |
| estimated_cost | REAL | | Estimated repair cost (assumption) |
| status | TEXT | NOT NULL DEFAULT 'New' | New / Open / Repaired / Failed |
| recurrence | BOOLEAN | NOT NULL DEFAULT 0 | True if previously repaired and re-appeared |
| unverified | BOOLEAN | NOT NULL DEFAULT 0 | True if not covered by verification survey |
| matched_prev_id | INTEGER | | Links to the previous defect this was matched against |
| crop_path | TEXT | | Relative path to closest-approach crop image |
| bbox_x1 | REAL | | Bounding box x1 |
| bbox_y1 | REAL | | Bounding box y1 |
| bbox_x2 | REAL | | Bounding box x2 |
| bbox_y2 | REAL | | Bounding box y2 |
| review_status | TEXT | | For future F6 human-in-the-loop review |

### segments

| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| segment_id | INTEGER | PRIMARY KEY | Auto-incremented |
| survey_id | INTEGER | FK → surveys, NOT NULL | Parent survey |
| start_m | REAL | NOT NULL | Start distance along route (meters) |
| end_m | REAL | NOT NULL | End distance along route (meters) |
| damage_index | REAL | NOT NULL | Union-area damage index (provisional) |
| condition | TEXT | NOT NULL | Good / Fair / Poor / NoData |

## Status Enum Rules

| Status | Meaning |
| --- | --- |
| **New** | First-time detection; no matching prior defect |
| **Open** | Previously known defect still detected in a new survey |
| **Repaired** | Previously known defect NOT detected AND the new survey path covered it |
| **Failed** | A defect previously marked Repaired that re-appears; sets `recurrence=True` |

> **Critical rule:** A defect is NEVER marked Repaired unless the new survey path demonstrably passed within `verification.coverage_radius_m` of the old defect's location. If coverage is absent, the old status is unchanged and `unverified=True`.

## Indexes

- `idx_defects_survey_id` on `defects(survey_id)`
- `idx_defects_status` on `defects(status)`
- `idx_defects_location` on `defects(lat, lon)`
- `idx_segments_survey_id` on `segments(survey_id)`
