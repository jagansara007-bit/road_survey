---
trigger: "ai-service"
description: "Rules and conventions for Python AI service development"
---

# AI Service Guidelines

1. **Thresholds & Classes**:
   - Always load constants, class names, and bounding area thresholds from `ai-service/config/thresholds.yaml`.
   - Never hardcode `0.02`, `0.08`, or defect class lists in application logic.
2. **Type Safety & Schemas**:
   - All API inputs and outputs must be strongly typed using Pydantic in `app/schemas.py`.
3. **Linting & Testing**:
   - Ensure `ruff check .` and `pytest` pass cleanly with zero warnings or errors.
