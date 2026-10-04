# System Metrics and Evaluation Report

**Generated on:** 2026-10-05  
**Status:** Evaluation Framework Active (Field Captures Pending)

---

## 1. Headline Metrics Summary

The table below summarizes the six core evaluation metrics defined in the Upgrade Blueprint. Unmeasured items are explicitly labeled as **NOT MEASURED** until field data collection in Chennai is completed.

| # | Metric | Target / Definition | Result | Sample Size ($N$) | Evaluation Date | Data Source |
|---|---|---|---|---|---|---|
| **1** | **Unique-Defect Precision / Recall / F1** | Post-dedup matching against ground truth ($\le 10$ m, same class) | **NOT MEASURED** | 0 defects | — | `data/chennai/<route>/<date>/ground_truth.csv` |
| **2** | **False Positives per km** | False positive rate on verified-clean road stretch | **NOT MEASURED** | 0 km | — | `data/chennai/clean_stretch/` |
| **3** | **Survey Throughput (km/h)** | Automated phone survey speed vs. manual walking inspection | **NOT MEASURED** | 0 surveys | — | `data/timing/timing_log.csv` |
| **4** | **Severity Agreement (Cohen's $\\kappa_w$)** | Quadratic-weighted Cohen's kappa vs. expert consensus | **NOT MEASURED** | 0 rated crops | — | `reports/expert_rating/completed_ratings.csv` |
| **5** | **Repair Verification Accuracy** | Correct classification across Open / Repaired / Failed / New | **NOT MEASURED** | 0 spots | — | `data/chennai/resurvey/repaired_spots.csv` |
| **6** | **Detection-to-Ticket Latency** | Time from video upload to ranked repair queue | **NOT MEASURED** | 0 runs | — | `data/timing/timing_log.csv` |

---

## 2. Baseline Model Context

For context, the baseline object detection performance on the sequence-grouped split (Phase 2) is reported below. This is strictly a per-box detection baseline on benchmark data and does not represent end-to-end unique-defect decision metrics.

- **Split Strategy:** Sequence-Grouped Split (70% train, 15% val, 15% test) to prevent adjacent-frame leakage.
- **Classes:** 3 super-classes (`crack`, `alligator_crack`, `pothole`).
- **Baseline Metric:** `mAP@0.5 = 0.528` (Benchmark reference only; clearly labeled as baseline).

---

## 3. Methodological Limitations

1. **Sample Size ($N$):** Field data collection on live Indian roads is in active preparation; current field sample size is $N = 0$.
2. **Geographical Scope:** Captures are planned exclusively on designated test corridors in Chennai, Tamil Nadu. Generalization to other cities with different asphalt types or marking standards remains to be verified.
3. **Hardware Uniformity:** Capture protocol specifies a single consumer smartphone (OnePlus / Samsung standard camera) mounted at a fixed windshield angle. Varying focal lengths or suspension dynamics may require threshold calibration.

---

## 4. Privacy & Data Protection Metrics (Phase 9)

In compliance with the Digital Personal Data Protection (DPDP) Act, 2023 and MoRTH data protection guidelines, the table below documents privacy redaction metrics. Field benchmark metrics remain **NOT MEASURED** pending labelled real-world evaluation data.

| # | Privacy Metric | Target / Definition | Result | Sample Size ($N$) | Evaluation Date | Protocol / Source |
|---|---|---|---|---|---|---|
| **P1** | **Blur Recall on Faces** | Fraction of identifiable civilian faces blurred before write ($\text{IoU} \ge 0.3$) | **NOT MEASURED** | 0 faces | — | `docs/PRIVACY.md` / `measure_blur_recall` |
| **P2** | **Blur Recall on Plates** | Fraction of legible vehicle registration plates blurred before write ($\text{IoU} \ge 0.3$) | **NOT MEASURED** | 0 plates | — | `docs/PRIVACY.md` / `measure_blur_recall` |
| **P3** | **Redaction Latency Overhead** | Per-crop blurring runtime overhead | **< 3.5 ms** | 100 benchmark crops | 2026-10-05 | `ai-service/tests/test_phase9.py` |
| **P4** | **Data Retention Window** | Maximum automated storage lifespan of unpurged media | **30 days** | — | 2026-10-05 | `scripts/purge_old_media.py` |

