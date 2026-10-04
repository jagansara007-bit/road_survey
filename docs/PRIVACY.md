# Privacy & Data Protection Architecture (Phase 9)

**Status:** Active  
**Compliance Baseline:** Digital Personal Data Protection (DPDP) Act, 2023 (India) & MoRTH Road Infrastructure Data Guidelines

---

## 1. Legal & Regulatory Context

Automated video collection for municipal infrastructure assessment involves recording public roads and adjacent thoroughfares. Under the **Digital Personal Data Protection Act, 2023 (DPDP)**, personal identifiers captured in public view (including identifiable faces of pedestrians and vehicle registration number plates) qualify as digital personal data when processed by an automated system.

Furthermore, Ministry of Road Transport and Highways (**MoRTH**) digital asset guidelines require that roadway condition intelligence systems process only asset health indicators and actively prevent the unauthorized collection or dissemination of civilian behavioral patterns.

---

## 2. Threat Model

| Threat | Source | Severity | Mitigation in Architecture |
|---|---|---|---|
| **Facial Identification** | Pedestrians, motorists, roadside vendors captured in near/mid-field dashcam footage | High | Automatic facial segmentation and heavy Gaussian blurring before image persistence. |
| **Vehicle Tracking (HSRP)** | High-Security Registration Plates captured on preceding or adjacent vehicles | High | Horizontal gradient filtering for high-contrast alphanumeric plates; Gaussian blurring before disk write. |
| **Long-Term Data Exposure** | Forgotten raw survey files and uncompressed video stored on local servers indefinitely | Medium | Configurable retention threshold (`retention_days = 30`) with automated purging via `scripts/purge_old_media.py`. |
| **Cloud Interception** | Exfiltration of unblurred video during network transmission | Critical | Fully offline execution: redaction occurs at the capture/edge pipeline prior to database or API serialization. |

---

## 3. Redaction Architecture: The `Redactor` Interface

The system encapsulates all privacy transformations behind a pluggable `Redactor` protocol defined in [`app/privacy.py`](file:///C:/Users/jagan/.gemini/antigravity-ide/scratch/road-damage-system/ai-service/app/privacy.py):

```python
class Redactor(Protocol):
    def redact(self, image: np.ndarray) -> np.ndarray: ...
    def detect_sensitive_regions(self, image: np.ndarray) -> list[tuple[int, int, int, int, str]]: ...
```

### 3.1 Offline Detector Options
1. **Rule-Based Heuristic Redactor (Default Offline Mode):**
   - **Faces:** Skin-tone segmentation in YCrCb color space combined with morphological filtering for face-proportioned ovals (aspect ratio 0.8–2.2).
   - **Plates:** Sobel gradient density analysis detecting rectangular regions matching Indian vehicle number plate dimensions (aspect ratio 1.8–5.5).
   - **Blur Engine:** Adaptive Gaussian blur ($\sigma = 30.0$, kernel size $\ge 15\text{ px}$) applied directly to detected bounding boxes.
2. **Pluggable Deep Learning Redactor:**
   - Production installations can inject external ONNX detectors (e.g. YOLOv8-face or LPRNet) via the `Redactor` interface without modifying the core pipeline or API layer.

---

## 4. What Is Blurred vs. What Is NOT Blurred

### What IS Blurred:
- Human facial regions across driver, passenger, and roadside bystander positions.
- Vehicle registration plates on commercial and private automobiles, motorcycles, and auto-rickshaws.

### What is NOT Blurred:
- The road asphalt surface, road base, and shoulders.
- All structural defect manifestations: longitudinal cracks (D00), transverse cracks (D10), alligator fatigue cracking (D20), and potholes (D40).
- Road furniture, curbs, manhole covers, and lane markings required for spatial contextualization.

---

## 5. Media Retention & Purging Policy

1. **Storage Tiering:**
   - Real-time video frames and extracted defect crops are stored inside the survey upload directory (`UPLOAD_DIR/<survey_id>/`).
2. **Configurable Retention Window:**
   - Governed by `thresholds.yaml` under `privacy.retention_days` (default: 30 days).
3. **Automated Purge Script:**
   - `scripts/purge_old_media.py` crawls the media directories, evaluates file modification timestamps against the retention cutoff, and purges expired assets:
   ```bash
   # Preview expired media (safe dry-run)
   python scripts/purge_old_media.py --target-dir /tmp/road_damage_uploads --retention-days 30

   # Commit deletions
   python scripts/purge_old_media.py --target-dir /tmp/road_damage_uploads --retention-days 30 --apply
   ```

---

## 6. Verification and Empirical Status

- Hand-labelled empirical recall on live Chennai street scenes is currently **NOT MEASURED** pending scheduled field data collection.
- Automated regression tests in `ai-service/tests/test_phase9.py` guarantee that any synthetic image containing face-like or plate-like regions undergoes high-frequency energy reduction prior to disk persistence.
