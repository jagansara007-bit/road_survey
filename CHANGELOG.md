# Changelog

All notable changes to this project will be documented in this file.

## [Phase 8: Evaluation Metrics, Calibration, and Reporting] - 2026-10-05

### Added
- Core evaluation module `ai-service/app/evaluation.py` implementing unique-defect matching, false positive rate per km, quadratic-weighted Cohen's kappa, threshold grid-search tuning, and verification confusion matrix.
- Field evaluation scripts in `scripts/`:
  - `validate_ground_truth.py`: Ground-truth CSV format validator.
  - `eval_defects.py`: Unique-defect precision/recall/F1 with deduplication reduction stats.
  - `eval_fp_per_km.py`: False positives per km on clean road stretches.
  - `eval_throughput.py` & `eval_latency.py`: Processing speed (km/h) and detection-to-ticket latency.
  - `make_rating_sheet.py`: Stratified sampling of closest-approach crops for expert review.
  - `eval_severity_kappa.py`: Quadratic-weighted Cohen's kappa for multi-expert agreement and 3x3 confusion matrix.
  - `tune_thresholds.py`: Seeded grid search for near-zone area ratio cutoffs without auto-overwriting thresholds.
  - `eval_verification.py`: Status accuracy against known ground-truth repair manifests.
  - `generate_metrics_report.py`: Consolidated reporter for `reports/METRICS_REPORT.md` (emits NOT MEASURED when data is absent).
- Documentation:
  - `docs/METRICS.md`: Full mathematical specifications and formulas for the six headline metrics.
  - `docs/CHENNAI_CAPTURE_PROTOCOL.md`: Field capture procedure, hardware setup, and ground-truth schema.
  - `docs/RATING_PROTOCOL.md`: Expert civil engineer rating instructions for closest-approach crops.
- Comprehensive test suite `ai-service/tests/test_phase8.py` covering degenerate cases, textbook kappa verification against scikit-learn, and arithmetic consistency.

## [Phase 3: Pure Severity and Condition Logic] - 2026-10-05

### Added
- `TrackObservation` and `DefectObservationSummary` schemas to support temporal tracking of defects.
- `closest_approach` in `severity.py` to evaluate severity for tracked objects based on largest box area nearest to the camera.
- `near_zone_area_ratio` in `severity.py` to mitigate perspective distortion by limiting measurement to the bottom fraction of the frame.
- `union_area_px` in `condition.py` using NumPy rasterization to correctly merge overlapping bounding boxes and prevent double-counting area (e.g., for alligator cracks).
- `docs/SEVERITY_AND_CONDITION.md` documenting the math and logic for severity and condition index calculations.
- Comprehensive test suite in `ai-service/tests/test_phase3.py`.

### Changed
- Refactored `severity.py` and `condition.py` to be pure functions injected with config parameters, removing implicit I/O.
- Restructured `ai-service/config/thresholds.yaml` to explicitly rename threshold variables (e.g., `ratio_low` to `low_max_ratio`, `fair_threshold` to `fair_min_index`) and introduce `tracking.min_track_frames` and `near_zone_top_fraction`.

## [Phase 0: Bootstrap and standards] - 2026-10-05
### Added
- Standard directory layout: `ai-service/`, `training/`, `java-app/`, `docs/`, `.agents/rules/`.
- `AGENTS.md` specifying repository golden rules, boundaries, and standards.
- CI and AI-service workflow rules in `.agents/rules/`.
- Externalized configuration in `ai-service/config/thresholds.yaml` (classes, severity ratios, condition thresholds, priority weights).
- Config loader `ai-service/app/config_loader.py` caching YAML thresholds.
- Core Python modules: `app/detector.py`, `app/severity.py`, `app/condition.py`, `app/schemas.py`, and `app/main.py`.
- Training sequence-grouped dataset split script `training/03_convert_split.py`.
- JavaFX skeleton build configuration `java-app/pom.xml` and `App.java`.
- Comprehensive `.gitignore` filtering model weights, data, videos, SQLite, and secrets.
- Unit test suite `ai-service/tests/test_core.py` covering schema validation, severity calibration, and condition index.
- Root build automation `Makefile` (`make setup`, `make check`) and `pyproject.toml`.
- Legacy audit documented in `docs/LEGACY_INVENTORY.md`.
 
## [Phase 4] Tracking and GPS deduplication
- Added GPS parsing for GPX and CSV.
- Implemented single-linkage clustering deduplication on track closest approach.
- Built video pipeline orchestration in process_video.
- Added FakeTracker for testing without YOLO model.

