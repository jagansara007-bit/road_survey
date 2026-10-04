# Severity and Road Condition Assessment

This document explains the pure-logic computations used in Phase 3 of the Road Damage Detection and Repair-Decision System to measure severity and condition.

## 1. Near-Zone Severity

### Rationale
In the previous detection demo, severity was calculated as the bounding box area divided by the total frame area. This approach suffered from perspective distortion: a pothole far away near the top of the frame appears much smaller than when it is directly in front of the camera, leading to unstable and incorrectly low severity ratings.

To resolve this, we implement **Near-Zone Severity**:
1. We restrict measurements to a defined "near-zone" (e.g., the bottom 50% of the image).
2. For tracked defects, we calculate the severity only at the defect's **closest approach** (when its bounding box is lowest in the frame and has the largest area).

### Formula
$$ \text{Near-Zone Ratio} = \frac{\text{Clipped Box Area}}{\text{Near-Zone Area}} $$

- **Clipped Box Area**: The area of the bounding box restricted entirely to the near-zone boundaries.
- **Near-Zone Area**: `frame_width` × `(frame_height - near_zone_top)`.

### Provisional Thresholds
> **IMPORTANT:** The current thresholds (`low_max_ratio = 0.02`, `medium_max_ratio = 0.08`) are carried over from legacy systems and adapted to the near-zone. These are **provisional** and will remain so until the Phase 8 expert calibration round, where they will be tuned against civil engineer ratings (measured by Cohen's kappa).

## 2. Road Condition Index (Union-Area)

### Rationale
Previously, the road condition index was calculated by summing the areas of all bounding boxes in a frame or segment. This resulted in significant **double-counting**, particularly for compound damage like alligator cracks (D20) where multiple overlapping boxes frequently cover the same physical area.

### Implementation
We resolve this by using a **Union-Area** calculation:
- All bounding boxes are drawn onto a single 2D binary raster (using `numpy`).
- The damaged area is calculated by counting the number of `True` pixels on the canvas.
- This mathematically guarantees that overlapping boxes are only counted once.

### Formula
$$ \text{Damage Index} = \frac{\text{Union Area in Pixels}}{\text{Total Segment Area in Pixels}} $$

### Condition Rating
The Stage 4 condition rules (Good / Fair / Poor) have been preserved as pure functions driven by `thresholds.yaml`:
- **Good**: `Damage Index < condition.fair_min_index`
- **Fair**: `condition.fair_min_index <= Damage Index < condition.poor_min_index`
- **Poor**: `Damage Index >= condition.poor_min_index`

*(These original cut-offs were ported directly from the legacy Stage 4 implementation in `condition.py`.)*
