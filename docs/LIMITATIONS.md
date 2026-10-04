# Known Limitations and Mitigation Strategies

This document tracks the known limitations of the underlying CRDDC/RDD dataset and our baseline model, along with the specific strategies implemented in this repository to mitigate them.

## 1. The D10 (Transverse Crack) Imbalance

**Limitation:** The dataset contains extremely few examples of transverse cracks (D10) compared to longitudinal cracks (D00) or potholes (D40) — often fewer than 50 boxes in a city's dataset. A YOLO model forced to predict D10 as a distinct class will overfit or ignore it, dragging down overall mAP.

**Mitigation (Implemented in Phase 1):**
*   **Super-class grouping:** `training/convert_to_3class.py` merges D00 and D10 into a single `crack` (class 0) super-class for object detection.
*   **Sub-classifier:** `training/make_orientation_crops.py` extracts the crack boxes, preserving their original D00/D10 labels, to train a specialized, lightweight orientation classifier (e.g., logistic regression on aspect ratio) to separate longitudinal from transverse *after* detection.

## 2. Train/Test Data Leakage

**Limitation:** A standard random 70/15/15 split on a video-derived dataset places adjacent video frames (which are nearly identical) into both the training and test sets. This artificially inflates test metrics (data leakage).

**Mitigation (Implemented in Phase 1):**
*   **Sequence-Grouped Split:** `training/make_split.py` groups images by their capture sequence (using filename prefix, index windows, or perceptual hashing) *before* splitting. The 70/15/15 ratio is applied at the group level, ensuring a single physical sequence never straddles the train and test splits.
*   **Leakage Verification:** `training/check_leakage.py` runs as a CI step to mathematically prove that no group leaks across splits.

## 3. Severity Measurement Artifacts

**Limitation:** In the baseline demo, severity is estimated by the ratio of the bounding box area to the total frame area. However, because of perspective, a pothole looks much smaller (lower ratio) when it is far away at the top of the frame than when it is directly in front of the camera.

**Mitigation (Planned for Phase 4 / Feature F5):**
*   **Closest-Approach Measurement:** Instead of taking the average severity across all frames, the system will track the defect (using ByteTrack) and measure its severity *only* at its closest approach (when the box is largest and lowest in the frame).
*   **Expert Calibration:** The hard-coded 2% and 8% thresholds will be validated against ratings provided by civil engineers (Cohen's kappa).

## 4. Double Counting of Compound Damage

**Limitation:** Large areas of alligator cracking (D20) are often labeled with multiple overlapping bounding boxes. Summing the areas of these boxes results in double-counting the damaged area, sometimes yielding a damage index > 100%.

**Mitigation (Planned for Phase 5):**
*   **Union-Area Rasterization:** When computing the road condition index in `condition.py`, all bounding boxes for a segment will be drawn onto a single binary 2D canvas. The damage area is the count of True pixels, ensuring overlapping boxes are only counted once.
