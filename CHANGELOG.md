# Changelog

All notable changes to this project will be documented in this file.

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
