# AGENTS.md - rules for every AI agent working in this repo

Project: **Road Damage Detection and Repair-Decision System**
Architecture: Multi-stage vision pipeline (YOLO detect/track -> Severity -> Road Condition -> Priority scoring) + FastAPI + JavaFX Dashboard + SQLite.

## Golden Rules
1. **Never commit sensitive or binary artifacts**: No `*.pt`, `*.onnx`, `*.mp4`, `*.sqlite*`, `.env`, or `data/` files in git.
2. **Deterministic & calibrated thresholds**: Hardcoded numbers (e.g. 2% / 8% severity area ratios, class definitions) must NEVER be inline in Python code; always load from `ai-service/config/thresholds.yaml`.
3. **Module boundaries**:
   - `ai-service/app/`: Core detection, severity, condition, priority, tracking, and FastAPI endpoints.
   - `training/`: Conversion, sequence-grouped split, and training pipeline scripts.
   - `java-app/`: JavaFX desktop client and SQLite DAO layer.
   - `docs/`: System documentation, specifications, and architecture records.
4. **Build and Quality Standards**:
   - All code must pass `make check` (`ruff check` + `pytest`).
   - FastAPI `/health` endpoint must return `{"status": "ok"}`.
5. **No invented facts**:
   - Disclose assumptions explicitly.
   - Every metric or formula must align with the main specification (`docs/MAIN_DOCUMENT.md`).
