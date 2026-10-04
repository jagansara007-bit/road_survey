# System Architecture

## Architecture Diagram

```
Phone Video + GPS Log (GPX/CSV)
              │
              ▼
   [Preprocessing Pipeline]
   (OpenCV frame extraction, privacy blur)
              │
              ▼
   [Stage 1 & 2: Detection + Tracking]
   (YOLOv8 + ByteTrack: track_id & GPS interpolation)
              │
              ▼
   [Stage 3: Calibrated Severity]
   (Closest approach, threshold evaluation)
              │
              ▼
   [Stage 4: Segment Aggregation]
   (50m road segment grouping, union-area damage index)
              │
              ▼
   [Priority Scoring Engine]
   (OSM highway hierarchy, school/hospital exposure factor)
              │
              ▼
   [FastAPI AI Service] ── HTTP/JSON ──> [JavaFX Dashboard (java-app)]
                                                │
                                                ▼
                                         [SQLite Database]
```

## Module Boundaries
- `ai-service/`:
  - `app/detector.py`: YOLO inference and ByteTrack persistence.
  - `app/severity.py`: Bounding-box closest-approach severity calculation.
  - `app/condition.py`: Union-area rasterization and road condition rating.
  - `app/schemas.py`: Pydantic models for surveys, defects, segments.
  - `app/main.py`: FastAPI application endpoints.
  - `config/thresholds.yaml`: Externalized configuration and thresholds.
- `training/`: Dataset conversion, sequence-grouped splitting, YOLO training scripts.
- `java-app/`: JavaFX interface, OpenStreetMap viewer, queue and SQLite DAO.
