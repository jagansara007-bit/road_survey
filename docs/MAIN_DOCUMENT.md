# Upgrade Blueprint: From Detection Demo to Repair-Decision System

**Companion to:** *Java-Based Multi-Stage Road Damage Detection Framework* (the "main document") **One-line pitch:** Turn cheap phone video into a ranked, mapped, verifiable repair queue for Indian roads.

---

## 1. The Idea in Brief

The main document builds a pipeline that answers *"is there damage in this image, and how bad?"* The upgrade keeps that pipeline intact and adds a layer that answers what an engineer actually needs: ***where is it, is it the same defect I already counted, what do I fix first, and was it really fixed?***

Nothing in the main document is thrown away. The YOLO model, FastAPI service, JavaFX app and SQLite database all stay. The upgrade adds a **location + identity + decision layer** on top of them.

|  | Main document (today) | Upgraded project |
| --- | --- | --- |
| Unit of analysis | One image | One unique defect on one road segment |
| Output | Good / Fair / Poor per frame | Ranked repair queue with map |
| Time dimension | None | Before/after tracking, repair verification |
| Severity | Box-area ratio | Closest-approach measurement, expert-calibrated |
| User | A student running a demo | PWD/municipal engineer deciding a budget |

---

## 2. How Each Upgrade Connects to the Main Document

| Main document element | Gap | Upgrade | Where it plugs in |
| --- | --- | --- | --- |
| Stage 1+2 `detector.py` | Frame-by-frame, no identity | **F1** Tracking + GPS dedup | Replace `predict()` with `track(persist=True)`; add `tracker.py` |
| Stage 3 `severity.py` | Box-area ratio is camera-dependent | **F5** Closest-approach severity + expert calibration | Edit `severity.py`, `thresholds.yaml` |
| Stage 4 `condition.py` | Per-image rating | **F2** Per-segment condition | New `segments.py`; `condition.py` runs per segment |
| Known limitation #4 (double counting) | Deferred | Union-area `damage_index` | Edit `condition.py` (see §4.1) |
| *(missing)* | No decision output | **F3** Priority score | New `priority.py` + OSM lookup |
| *(missing)* | No time dimension | **F4** Repair verification | New `verify.py`; new DB tables |
| Known limitation #1 (D10, 46 boxes) | Disclosed, not fixed | Crack super-class + sub-classifier | Edit `03_convert_split.py`, retrain |
| Known limitation #2 (split leakage) | Disclosed, not fixed | Sequence-grouped split | Edit `03_convert_split.py` |
| `java-app/` JavaFX | Result viewer only | Authority dashboard with map | `ui/MapView`, `ui/QueueView`, `ui/VerifyView` |
| SQLite (Java-written) | Flat results history | Defects, segments, surveys tables | `db/` DAO + new schema (§5) |

---

## 3. Foundation Fixes (do first; they protect everything else)

These are not "features" but they make the headline numbers defensible.

1. **Sequence-grouped split.** Group images by capture sequence (filename prefix or location) before the 70/15/15 split so near-duplicate frames never straddle train and test. *Connects to:* limitation #2. *Effect:* honest test metrics.
2. **Excluded-class audit.** Count train images that contain only D44/D01/D43/D11/D50/D0w0 labels. If they are currently written as empty-label background images, either drop them or relabel. *Connects to:* §2 of main doc. *Effect:* removes false negatives taught as "negative".
3. **Union-area damage index.** Rasterize all boxes onto one binary canvas and count filled pixels instead of summing box areas. *Connects to:* limitation #4. *Effect:* alligator cracks stop being double counted.
4. **D10 mitigation.** Train a 3-class detector (`crack`, `alligator`, `pothole`) and add a small orientation sub-classifier (longitudinal vs transverse) on crack crops, using box aspect ratio plus angle as a baseline. *Connects to:* limitation #1. *Effect:* the weak class stops dragging the model.

---

## 4. Unique Features

### F1. Tracking, GPS Tagging and Deduplication

- **What:** A pothole seen in 30 frames becomes **one** defect with one location.
- **Why unique:** Most student projects count detections; this counts *defects*.
- **Implementation:**
  1. Capture phone video plus a GPS log (GPX or CSV with timestamps).
  2. Run `model.track(persist=True, tracker="bytetrack.yaml")` in `detector.py`; each object gets a `track_id`.
  3. Interpolate GPS by video timestamp to give each track a lat/lon.
  4. Merge tracks of the same class within about 5 m into one `defect_id` (simple distance clustering).
  5. Return `defects[]` instead of `detections[]` from the API.
- **Connects to:** Stage 1+2; adds `lat`, `lon`, `track_id`, `defect_id` to `schemas.py`.
- **Better because:** counts become true, and every later feature depends on location and identity.

### F2. Segment-Level Road Condition

- **What:** Roads are rated per 50 m segment (configurable), not per frame.
- **Implementation:** Snap defect GPS to the traveled path, bucket by distance along the route, then compute Stage 4 on each bucket using defect count and union-area index normalized by segment length.
- **Connects to:** Stage 4 rules stay (Good/Fair/Poor), but the input changes from "one image" to "one segment".
- **Better because:** matches how roads are actually surveyed and maintained, and gives a colorable map.

### F3. Priority Score and Repair Queue

- **What:** Replaces "Poor" with *"fix these 20 spots first."*
- **Formula (all weights configurable in `thresholds.yaml`):**

```
priority = severity_score × road_weight × exposure_factor × recurrence_factor

severity_score    : Low 1, Medium 2, High 3
road_weight       : OSM highway tag (primary 1.5, secondary 1.25, residential 1.0)
exposure_factor   : 1.5 if within 200 m of a school or hospital, else 1.0
recurrence_factor : 1.5 if previously repaired and failed (from F4), else 1.0
```

- **Extras:** rough patching-cost estimate per defect (area × assumed unit rate, clearly labeled as an assumption) and a budget slider: "with ₹X, these defects are covered."
- **Connects to:** consumes Stage 3 severity; needs F1 locations; output feeds the JavaFX queue view.
- **Better because:** answers the municipal engineer's real question, and OSM data is free so it adds no cost.

### F4. Repair Verification (the "wow" demo)

- **What:** Re-survey the same road, auto-match to earlier defects, and report status.
- **Implementation:**
  1. Store each survey as a row in `surveys` with a date.
  2. Match new defects to old ones within 10 m and same class.
  3. Assign status: **Open** (still there), **Repaired** (old defect absent in clear coverage), **Failed** (re-appeared after repair), **New**.
  4. Show before/after crops side by side.
- **Connects to:** SQLite DAO gains history; priority gets the recurrence factor.
- **Better because:** gives contractor accountability and defect-liability evidence, which almost no comparable project offers.

### F5. Calibrated Severity (Closest-Approach + Expert Validation)

- **What:** Fixes the weakness that box-area ratio changes with distance and camera angle.
- **Implementation:**
  1. Measure severity at each track's **closest approach** (largest box, lowest in frame), not at every frame.
  2. Restrict area measurement to a "near zone" (lower part of the frame).
  3. Have 2-3 civil engineers rate about 100 detections as Low/Medium/High.
  4. Report agreement (Cohen's kappa) and re-tune the 2%/8% thresholds against their ratings.
- **Connects to:** `severity.py` and `thresholds.yaml`; resolves limitation #3 with evidence.
- **Better because:** turns "arbitrary thresholds, honestly disclosed" into "thresholds validated by experts".

### F6 (Stretch). Human-in-the-Loop Review

- **What:** Officers confirm or reject detections in the dashboard; rejected items become hard negatives (speed breakers, manholes, patches, shadows) for retraining.
- **Connects to:** DB gets a `review_status` column; `training/` gains a retrain script. Attempt only if F1-F5 are done.

---

## 5. Data Model Changes

```sql
CREATE TABLE surveys (
  survey_id INTEGER PRIMARY KEY, surveyed_on DATE, route_name TEXT, source TEXT
);
CREATE TABLE defects (
  defect_id INTEGER PRIMARY KEY, survey_id INTEGER, class TEXT,
  lat REAL, lon REAL, severity TEXT, area_px INTEGER,
  confidence REAL, priority REAL, status TEXT DEFAULT 'Open',
  review_status TEXT, matched_prev_id INTEGER, crop_path TEXT
);
CREATE TABLE segments (
  segment_id INTEGER PRIMARY KEY, survey_id INTEGER, start_m REAL, end_m REAL,
  damage_index REAL, condition TEXT
);
```

**API response (new shape):**

```json
{ "survey_id": 12,
  "defects": [{"defect_id": 3, "class": "D40", "lat": 13.0827, "lon": 80.2707,
               "severity": "High", "priority": 6.75}],
  "segments": [{"start_m": 0, "end_m": 50, "condition": "Poor"}] }
```

---

## 6. Updated Architecture

```
Phone video + GPS log
      │
Preprocessing (OpenCV, plate/face blur)
      │
Stage 1+2  YOLO detect + ByteTrack            ← F1
      │
GPS tagging + dedup → unique defects          ← F1
      │
Stage 3  Severity (closest approach)          ← F5
      │
Segment aggregation (50 m)                    ← F2
      │
Stage 4  Condition per segment (union area)
      │
Priority scoring (OSM road class, exposure)   ← F3
      │
Java dashboard ──HTTP──▶ FastAPI ──▶ SQLite
 (map, queue, verification view)              ← F4
```

New files: `ai-service/app/{tracker,gps,segments,priority,verify}.py` and `java-app/.../ui/{MapView,QueueView,VerifyView}.java`.

---

## 7. Revised Phases (mapped to the main document)

| Phase | Main document goal | Upgrade work added |
| --- | --- | --- |
| 2 | Train YOLO (in progress) | Let it finish as baseline; retrain after grouped split and label audit |
| 3 | Test and per-class metrics | Report on grouped split **and** on 150-300 own Chennai images |
| 4 | Severity | Closest-approach severity, expert rating round (F5) |
| 5 | Road condition | Union-area index, segment aggregation (F2) |
| 6 | JavaFX UI | Map view and priority queue (F3) |
| 7 | Java ↔ FastAPI | GPS-aware `defects[]` API, tracking (F1), API key, upload limits |
| 8 | SQLite + end-to-end | New schema, repair verification (F4), demo script |

**Cut order if time runs short:** F6 first, then cost estimate, then expert round shrinks to one rater. Never cut F1 or F3.

---

## 8. Why This Is Better

**For users:** an engineer gets a ranked, mapped list with evidence instead of per-frame labels.

**For credibility:** every limitation in main document §9 is either fixed or backed with evidence rather than only disclosed.

**For the competition:** you stop competing on mAP, where tuned CRDDC entries will win, and compete on workflow, where commercial tools are expensive and Indian conditions are under-served.

**Metrics to report (replace mAP as the headline):**

| Metric | How to measure |
| --- | --- |
| Unique-defect precision/recall | Chennai test set after dedup |
| False positives per km | Count on a clean road stretch |
| Km surveyed per hour vs manual | Time both methods |
| Severity agreement | Cohen's kappa vs expert ratings |
| Repair verification accuracy | Re-survey with known repaired spots |
| Detection-to-ticket time | Stopwatch from upload to ranked queue |

---

## 9. Risks and Safeguards

- **GPS drift in video:** use a phone with a decent GPS log, filter points with poor accuracy, and cluster with a tolerance rather than exact match.
- **Scope creep:** F1-F5 is the target; F6 is optional.
- **Privacy:** blur faces and plates before storing frames; state a retention period.
- **Demo fragility:** export to ONNX, keep a recorded fallback, and prepare one pre-processed survey for the live demo.
- **OSM lookups offline:** cache road-class and school/hospital data for the demo area beforehand.

---

## 10. Judge-Ready Summary

> "Existing tools tell you a road is bad. Ours tells a city engineer which 20 defects to fix first, shows them on a map, counts each one once, and proves later whether the contractor really fixed it, all from a phone video."