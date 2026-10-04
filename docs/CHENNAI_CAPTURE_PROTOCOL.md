# Chennai Road Capture & Ground-Truth Protocol

This document defines the standardized procedure for capturing mobile road survey data in Chennai, Tamil Nadu, and annotating ground-truth validation manifests.

---

## 1. Hardware & Mounting Setup

- **Camera Device:** Standard consumer smartphone (e.g., OnePlus, Samsung, Pixel) capable of recording 1080p at 30 fps.
- **Mounting:** Rigid suction-cup windshield mount positioned on the center centerline behind the rearview mirror.
- **Orientation:** Landscape, downward tilt showing the hood line at the extreme bottom edge (ensuring the lower 50% of the frame is clear road surface).
- **GPS Logging:** Hardware GNSS receiver or phone GPS log sampling at $\ge 1\text{ Hz}$ in CSV or GPX format.

---

## 2. Survey Driving Rules

1. **Speed:** Maintain steady travel speed between $25\text{ km/h}$ and $40\text{ km/h}$.
2. **Lighting:** Daytime surveys between 09:00 and 16:00 to minimize long shadow artifacts. Avoid wet road surfaces immediately following rain.
3. **Synchronization:** Note the exact start time of the video recording and calibrate with the GPS clock timestamp.

---

## 3. Ground-Truth Data Format

Ground-truth files must be stored in:
`data/chennai/<route>/<date>/ground_truth.csv`

### Required Columns
| Column | Type | Constraints | Description |
|---|---|---|---|
| `defect_id` | Integer | Positive, unique within file | Unique identifier for ground-truth defect |
| `class` | String | Must match recognized classes (`crack`, `alligator_crack`, `pothole`) | Damage category |
| `lat` | Real | $[-90.0, 90.0]$ | WGS84 latitude coordinate |
| `lon` | Real | $[-180.0, 180.0]$ | WGS84 longitude coordinate |
| `severity_note` | String | Free-form text | Field inspector notes (e.g. "Low", "Medium", "High", or depth notes) |

### Validation
Run the validator script to ensure CSV compliance:
```bash
python scripts/validate_ground_truth.py data/chennai/<route>/<date>/ground_truth.csv
```
