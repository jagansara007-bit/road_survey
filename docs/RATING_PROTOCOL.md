# Expert Severity Rating Protocol

This guide instructs civil and municipal engineers on providing ground-truth severity ratings for automated road damage crops.

---

## 1. Overview
The automated pipeline extracts **closest-approach crops** of detected road damage when the defect is lowest in the frame and closest to the vehicle. To calibrate the model's area-ratio thresholds, engineers independently rate a stratified sample of approximately 100 crops.

---

## 2. Severity Classification Criteria

| Level | Physical Definition | Visual Indicator in Crop |
|---|---|---|
| **Low** | Superficial hairline cracks, shallow minor depressions ($< 25\text{ mm}$ depth), early raveling. No immediate risk to vehicle suspension. | Narrow linear features, minimal dark shadow depth, negligible surface disruption. |
| **Medium** | Moderate cracks ($3\text{--}6\text{ mm}$ width), potholes of moderate depth ($25\text{--}50\text{ mm}$), interconnecting alligator patterns. | Clearly visible crack boundaries, distinct shallow depression. |
| **High** | Severe structural potholes ($> 50\text{ mm}$ depth), wide open fissures, spalling with loose aggregate. High vehicle damage risk. | Deep shadows indicating significant depth, wide surface loss, jagged edges. |

---

## 3. Workflow for Experts

1. Open the exported spreadsheet: `reports/expert_rating/rating_sheet.csv`.
2. Inspect the corresponding image crop in `reports/expert_rating/crops/<filename>`.
3. In your assigned column (`rater_1`, `rater_2`, or `rater_3`), enter exactly one of:
   - `Low`
   - `Medium`
   - `High`
4. Do not consult with other raters prior to completing the sheet (ensures independent inter-rater evaluation).
5. Return the completed CSV to the evaluation team for kappa scoring via:
   ```bash
   python scripts/eval_severity_kappa.py --ratings completed_ratings.csv
   ```
