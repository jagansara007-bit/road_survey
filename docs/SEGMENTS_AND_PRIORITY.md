# Segments and Priority Queue

This document details the pure-logic computations used in Phase 5 to divide a road into segments, evaluate their condition, and rank discovered defects by repair priority.

## 1. Segment Bucketing and Condition

Instead of evaluating road condition per-frame, the system evaluates it over consistent road segments (e.g., 50 meters).

### Bucketing
The GPS trajectory is converted into a continuous polyline.
Cumulative distance is calculated using the Haversine formula.
The total route is divided into segments of `cfg.segments.length_m` (default 50 m). 
*Note on the last segment:* The final segment of the route may be shorter than the target length if the total distance is not perfectly divisible.

### Coverage & Gaps
If a segment falls entirely within a GPS gap (exceeding `cfg.gps.max_time_gap_s`), it is marked as `NoData`. A segment is never assumed `Good` unless it was successfully traversed with valid GPS and no defects were found.

### Segment Damage Index (Provisional)
Defects are snapped to the nearest point on the route polyline and assigned to their respective segments.
The damage index for a segment is calculated using the **Union-Area Rasterization** method from Phase 3, combining all representative bounding boxes for the segment's defects.

$$ \text{Segment Damage Index} = \frac{\text{Union Area of Defect Boxes (pixels)}}{\text{Total Frame Area (pixels)}} $$

> **IMPORTANT:** This pixel-based damage index formula is **provisional**. Translating pixel areas accurately to physical surface areas is impossible without camera calibration. The cut-offs for `Good / Fair / Poor` will be calibrated in Phase 8 against expert engineering ratings.

## 2. Priority Score

Instead of a binary "fix/don't fix", defects are ranked into a queue using a configurable formula.

### Formula
$$ \text{Priority} = \text{Severity} \times \text{Road Weight} \times \text{Exposure} \times \text{Recurrence} $$

| Factor | Description | Example Config Values |
| --- | --- | --- |
| **Severity Score** | From visual severity | High=3.0, Medium=2.0, Low=1.0 |
| **Road Weight** | OSM Highway Tag | primary=1.5, secondary=1.25, residential=1.0 |
| **Exposure Factor** | Near school/hospital (< 200m) | Yes=1.5, No=1.0 |
| **Recurrence Factor** | Failed prior repair | Yes=1.5, No=1.0 |

### Worked Example
Imagine a deep pothole (`Severity = High`), located on a `primary` road, 100m away from a `school`. It has not been repaired before.
* Severity Score = 3.0
* Road Weight = 1.5
* Exposure Factor = 1.5
* Recurrence = 1.0

$$ \text{Priority} = 3.0 \times 1.5 \times 1.5 \times 1.0 = 6.75 $$

Compare this to a shallow crack (`Low`) on a `residential` road, far from sensitive amenities:
$$ \text{Priority} = 1.0 \times 1.0 \times 1.0 \times 1.0 = 1.0 $$

## 3. Cost Estimation and Budgeting

### Cost Estimate Assumption
To allow for budget planning, a rough cost is assigned to each defect:
$$ \text{Cost} = \text{Nominal Area } (m^2) \times \text{Unit Rate } (INR/m^2) $$

> **CRITICAL ASSUMPTION:** The system maps visual severity directly to a nominal area (e.g., Low=0.5m², High=3.0m²). Because pixel area cannot be reliably converted to physical square meters, this output is strictly an **estimate (assumption)**. Every UI label and report must reflect this.

### Budget Selection Algorithm
When a budget is applied via `select_within_budget`:
1. The queue is walked in **Priority order** (descending). Tie-breaks resolve via severity (desc), then defect ID (asc).
2. For each item, if its estimated cost fits within the `remaining_budget`, it is **selected** and the budget is reduced.
3. If it exceeds the remaining budget, the item is **skipped**, and the algorithm *continues* checking the rest of the queue for smaller items that might fit the leftover funds (Greedy Knapsack approach).
