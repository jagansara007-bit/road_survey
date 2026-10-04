# Evaluation Metrics Specification

This document defines the mathematical foundations, sample size requirements, and reporting guidelines for the six core evaluation metrics of the Road Damage Detection and Repair-Decision System.

---

## 1. Unique-Defect Precision, Recall, and F1 Score

### Rationale
Standard object detection benchmarks evaluate per-frame boxes using mAP. In real road maintenance workflows, a single defect (e.g. a pothole) is observed across multiple video frames. Counting detections inflates defect totals and penalizes longer tracks. We evaluate **unique defects** after spatial-temporal tracking and GPS deduplication.

### Mathematical Formulation
Given a set of predicted unique defects $\mathcal{P} = \{p_1, \dots, p_M\}$ and ground-truth defects $\mathcal{G} = \{g_1, \dots, g_N\}$:
1. A prediction $p_i$ matches a ground-truth defect $g_j$ if and only if:
   $$\text{class}(p_i) = \text{class}(g_j) \quad \text{and} \quad d_{\text{haversine}}(p_i, g_j) \le R_{\text{match}}$$
   where $R_{\text{match}} = 10.0\text{ m}$ by default (configured via `verification.match_radius_m`).
2. Matching is **greedy one-to-one**, sorted in ascending order of distance:
   $$\text{TP} = |\text{Matched Pairs}|, \quad \text{FP} = |\mathcal{P}| - \text{TP}, \quad \text{FN} = |\mathcal{G}| - \text{TP}$$
3. Metrics:
   $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}, \quad \text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}, \quad \text{F1} = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

---

## 2. False Positives per Kilometer (FP/km)

### Rationale
High recall is useless if false alarms trigger expensive physical inspections. False positive rate is evaluated on designated **verified-clean stretches** of road where ground-truth damage is zero.

### Mathematical Formulation
$$\text{FP/km} = \frac{N_{\text{FP}}}{D_{\text{clean}}}$$
where $D_{\text{clean}}$ is the total route distance in kilometers computed from the synchronized GPS trajectory.

---

## 3. Survey Throughput (km/h)

### Rationale
Quantifies operational efficiency of vehicle-mounted phone survey compared against traditional walking/windshield visual manual surveys.

### Mathematical Formulation
$$\text{Throughput} = \frac{D_{\text{survey}}}{T_{\text{survey}} / 3600}$$
where $D_{\text{survey}}$ is road distance in kilometers and $T_{\text{survey}}$ is elapsed survey time in seconds.

---

## 4. Severity Agreement (Quadratic-Weighted Cohen's $\kappa_w$)

### Rationale
Validates that automated closest-approach severity ratings (`Low`, `Medium`, `High`) align with professional civil engineering judgments.

### Mathematical Formulation
For $K = 3$ ordered categories ($0 = \text{Low}, 1 = \text{Medium}, 2 = \text{High}$):
$$w_{ij} = 1 - \frac{(i - j)^2}{(K - 1)^2}$$
$$\kappa_w = 1 - \frac{\sum_{i=1}^K \sum_{j=1}^K w_{ij} O_{ij}}{\sum_{i=1}^K \sum_{j=1}^K w_{ij} E_{ij}}$$
where $O_{ij}$ is the observed confusion matrix and $E_{ij}$ is the expected matrix under chance agreement.

---

## 5. Repair Verification Accuracy

### Rationale
Measures contractor accountability by validating automated state transitions between consecutive surveys.

### Status Classes
- `New`: Newly detected defect not present in baseline survey.
- `Open`: Known defect still detected at verified location.
- `Repaired`: Known defect no longer detected, with verified route coverage within $R_{\text{coverage}}$.
- `Failed`: Previously repaired defect that has re-opened (sets `recurrence=True`).
- `unverified`: Known defect where the resurvey route did not pass within $R_{\text{coverage}}$.

$$\text{Verification Accuracy} = \frac{\sum_{c} \text{Correct Status}_c}{N_{\text{inspected spots}}}$$

---

## 6. Detection-to-Ticket Latency

### Rationale
Measures responsiveness of the end-to-end automated pipeline from video upload completion to ranked repair queue delivery.
$$\text{Latency} = T_{\text{queue delivery}} - T_{\text{upload completion}}$$

---

## Reporting Rules
1. **Never fabricate numbers**: When field capture data is absent, scripts emit `NOT MEASURED` and exit code `0`.
2. **Deterministic execution**: All sampling, splitting, and matching must be seeded (`seed=42`).
