# Road Damage Repair-Decision System: Official Demo Script

This script provides step-by-step instructions for demonstrating the **Multi-Stage Road Damage AI & Municipal Repair Decision System** to evaluators, judges, municipal engineers, and public works authorities.

---

## 1. System Overview & Core Narrative

> *"Existing tools tell you a road is bad. Ours tells a city engineer which defects to fix first within their exact budget, plots them on an offline-capable map, deduplicates multiple camera sightings into a single ticket, and proves later whether the contractor actually completed the repair."*

### Available Demonstration Modes:
1. **Scenario A: Air-Gapped Offline Presentation (`--demo`)**  
   Runs 100% offline with zero external network connectivity, zero database overhead, and pre-packaged local fixtures. Recommended for stage presentations and air-gapped environments.
2. **Scenario B: Live End-to-End Microservice**  
   Launches the FastAPI AI engine (:8000) with SQLite storage, real-time spatial deduplication, budget optimization API, and live JavaFX dashboard synchronization.

---

## 2. Prerequisites & Environment Setup

Verify required tooling before starting the presentation:
- **Java:** JDK 21+ (`java -version`)
- **Maven:** Apache Maven 3.9+ (`mvn -version`)
- **Python:** 3.10+ managed via `uv` (`uv --version`)

```bash
# Verify system integrity & test suites
make check
cd java-app && mvn test && cd ..
```

---

## 3. Scenario A: Air-Gapped Offline Demo Walkthrough

### Step 1: Launch Application in Demo Mode
Open a terminal, navigate to `java-app`, and execute:
```bash
cd java-app
mvn compile javafx:run -Djavafx.args="--demo"
```
**Expected Terminal Output:**
```text
Running in DEMO mode. API calls bypassed.
```
*The desktop window titled `Road Damage Authority Dashboard [DEMO MODE]` opens with dimensions 1024x768.*

---

### Step 2: Tab 1 — Interactive Map View
1. **Leaflet Offline Engine:**  
   Click on the **Map** tab. The view renders using bundled Leaflet resources (`map.html`, `leaflet.js`, `leaflet.css`).
2. **Air-Gapped Resiliency:**  
   Because external internet connectivity is disconnected or bypassed, the map displays a clean SVG grid canvas (`#f1f3f5`) with an `"Offline Mode (Local Grid Active)"` badge rather than broken image tiles.
3. **Defect Markers & Color-Coding:**  
   Notice the pre-loaded Bengaluru road defects:
   - **Red marker (`#e03131`):** High Severity (D40 Pothole, MG Road).
   - **Orange marker (`#f08c00`):** Medium Severity (Crack).
4. **Interactive Inspect Popup:**  
   Click on any marker. A popup displays `Defect #ID`, `Severity`, and coordinates (`Lat`, `Lon`), while dispatching defect selection to the Java backend bridge.

---

### Step 3: Tab 2 — Priority Repair Queue & Budget Allocation
1. **Mock Data Presentation:**  
   Click on the **Queue** tab. The table displays ranked defects loaded from `src/main/resources/demo/fixtures.json`:
   - Column schema: `ID`, `Class`, `Severity`, `Priority`, `Estimated Cost (₹)`, `Status`.
2. **Dynamic Budget Slider (`₹0` to `₹10,00,000`):**  
   - Drag the slider to adjust the municipal budget.
   - The label updates instantly: `Budget (INR): ₹XX,XXX`.
   - The underlying `QueueViewModel.selectWithinBudget` algorithm dynamically selects candidates that maximize priority score within the budget cap.
3. **CSV Work Order Export:**  
   - Click **Export to CSV**.
   - The status message confirms: `Exported N items to repair_queue_export.csv`.
   - Inspect the generated `repair_queue_export.csv` containing contractor work order fields.

---

### Step 4: Tab 3 — Contractor Re-Survey Verification (The "Wow" Feature)
1. **Side-by-Side Visual Audit:**  
   Click on the **Verify** tab.
   - Left side: **Previous Survey (Baseline)** showing the unaddressed pothole with red detection bounding box.
   - Right side: **Current Survey (Re-survey)** showing the asphalt repair patch and seal outline.
2. **Auditor Action Controls:**  
   Demonstrate contractor accountability decisions:
   - Click **Mark as Repaired**: Status updates to `Current Status: Repaired (Verified Closed)` (Green highlight).
   - Click **Mark as Failed**: Status updates to `Current Status: Failed (Defect Recurred / Inadequate Repair)` (Red highlight).
   - Click **Keep Open**: Status updates to `Current Status: Open (Unrepaired)`.

---

### Step 5: Tab 4 — Ingestion & Upload Form
1. Click on the **Upload** tab.
2. Review the survey ingestion form fields:
   - **Route Name** text field (e.g. `Anna Salai Corridor`).
   - **Survey Date** date picker.
   - **Video File** selector (`.mp4` dashcam stream).
   - **GPS Track** selector (`.csv` / `.gpx` interpolated vehicle telemetry).
   - **Upload Survey** trigger with active progress indicator.

---

## 4. Scenario B: Live End-to-End Microservice Walkthrough

For environments where local processes can interact over localhost:

### Step 1: Start FastAPI Microservice
In Terminal 1 (from repository root):
```bash
make run-ai
```
*Uvicorn starts on `http://127.0.0.1:8000` with SQLite storage (`ai-service/road_damage.sqlite`).*

### Step 2: Verify Service Health & Endpoints
In Terminal 2:
```bash
# Liveness probe (no auth required)
curl -s http://127.0.0.1:8000/health
# Response: {"status":"ok"}

# List surveys (requires API key header)
curl -s -H "X-API-Key: dev-secret-key" http://127.0.0.1:8000/api/v1/surveys
```

### Step 3: Launch Live Authority Dashboard
In Terminal 2:
```bash
cd java-app
mvn javafx:run
```
*The JavaFX Dashboard connects to `http://127.0.0.1:8000/api/v1/` using the configured API client.*

---

## 5. Automated Verification Checklist

To verify all system components programmatically prior to a demonstration:

| Target | Command | Expected Outcome |
|---|---|---|
| Python Code Quality | `make lint` | `All checks passed!` |
| Python Pipeline & ML Tests | `make test` | `58 passed, 0 failures` |
| Java UI & DTO Tests | `cd java-app && mvn test` | `Tests run: 8, Failures: 0, Errors: 0` |
| Privacy Redactor Audit | `uv run pytest ai-service/tests/test_phase9.py` | `7 passed` (Gaussian blurring verified) |
| Metrics Report Integrity | `uv run scripts/generate_metrics_report.py` | Formats `reports/METRICS_REPORT.md` |
