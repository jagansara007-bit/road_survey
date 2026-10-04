# Project Brief: Multi-Stage Road Damage Detection & Repair-Decision System

## Overview
An end-to-end operational intelligence system transforming cheap smartphone dashcam footage into an auditable, ranked, GPS-mapped road repair queue for municipal and public works engineers.

## Key Capabilities
1. **Multi-Stage AI Pipeline**:
   - Stage 1 & 2: YOLOv8 defect detection and ByteTrack object tracking for spatial deduplication.
   - Stage 3: Closest-approach severity estimation calibrated with engineering thresholds.
   - Stage 4: Union-area segment-level condition evaluation (50m blocks: Good / Fair / Poor).
   - Priority Scoring: Multi-factor ranking incorporating road classification (OSM), facility proximity, and recurring defect history.
2. **Authority Dashboard**:
   - JavaFX desktop application with map view, work-order repair queue, and contractor repair verification view.
   - SQLite persistent storage for surveys, defects, and segments.
3. **Robust AI Microservice**:
   - FastAPI microservice exposing structured endpoints for video ingestion, frame evaluation, and defect tracking.
