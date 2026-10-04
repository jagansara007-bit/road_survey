# Legacy Inventory

## Inventory Status

No pre-existing legacy files existed in the root directory prior to Phase 0 bootstrapping. All baseline modules have been initialized cleanly in accordance with the target architecture defined in `docs/MAIN_DOCUMENT.md`.

| Original Path | Purpose / Description | Language | Destination Path | Status |
| :--- | :--- | :--- | :--- | :--- |
| `ai-service/app/detector.py` | Object detection & tracker wrapper | Python | `ai-service/app/detector.py` | Initialized |
| `ai-service/app/severity.py` | Bounding box area ratio & severity rating | Python | `ai-service/app/severity.py` | Initialized |
| `ai-service/app/condition.py` | Union area damage index & road condition | Python | `ai-service/app/condition.py` | Initialized |
| `ai-service/app/schemas.py` | Pydantic data models & contracts | Python | `ai-service/app/schemas.py` | Initialized |
| `ai-service/app/main.py` | FastAPI application service & health probe | Python | `ai-service/app/main.py` | Initialized |
| `training/03_convert_split.py` | Sequence-grouped dataset split & format converter | Python | `training/03_convert_split.py` | Initialized |
| `java-app/pom.xml` | Maven build definition for JavaFX application | XML | `java-app/pom.xml` | Initialized |
| `java-app/src/main/java/com/roaddamage/App.java` | JavaFX Desktop Application entry point | Java | `java-app/src/main/java/com/roaddamage/App.java` | Initialized |

All target destinations exist and are verified.
