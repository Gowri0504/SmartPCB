# FINAL COMPONENT MODEL EVALUATION — 2026-09-23

All numbers measured on this machine (CPU) by
`python scripts/evaluation/evaluate_deployed_models.py --model component`
against `models/component_best.pt` (10 classes, trained at imgsz 1024;
Kaggle-trained, `trained_in_this_repository=False`, provenance block in
`metrics/component_metrics.json`).

## Results (components_curated split: val 30 / test 50)

| Threshold | Source | mAP50 | mAP50-95 | micro-F1 |
|-----------|--------|-------|----------|----------|
| 0.25 | default | 0.09335 | 0.04371 | 0.23196 |
| 0.15 | val-calibrated | 0.09528 | 0.04249 | 0.24440 |

Val micro-F1 at calibrated 0.15 = 0.36836 (30 val images).

Per-class @0.25 — only 6 of 10 model classes have GT in this split:

| Class | AP50 | Precision | Recall | GT | Pred |
|-------|------|-----------|--------|----|------|
| transistor | 0.252174 | 0.5625 | 0.3913 | 23 | 16 |
| ic | 0.158449 | 0.5455 | 0.2195 | 82 | 33 |
| capacitor | 0.076440 | 0.2967 | 0.2164 | 536 | 391 |
| resistor | 0.066148 | 0.3944 | 0.1640 | 433 | 180 |
| diode | 0.006868 | 0.2308 | 0.0214 | 140 | 13 |
| inductors | 0.000000 | 0.0 | 0.0 | 24 | 0 |
| battery, buzzer, led, relay, switch | n/a | — | — | 0 GT | 34 preds total |

## Stability check

The same numbers were produced by two evaluator revisions (2026-09-23 15:38
and the current refactored evaluator with raw persistence): mAP50 0.093346 in
both runs. The low score is a property of the deployed checkpoint on the
curated dataset, NOT an evaluation artifact.

## Honest assessment

The deployed component detector is WEAK on the curated component dataset:
macro mAP50 ≈ 0.09, recall ≤ 0.39 for every class. Contributing factors
(evident from data, not proven quantitatively): (a) PARTIAL taxonomy — 5 of
10 model classes (relay, buzzer, switch, battery, led) have no curated GT;
(b) the curated split is small (230 images total); (c) the checkpoint was
trained on an external mixed taxonomy. This must not be presented as a strong
component detector. The defect detector carries the inspection workload
(mAP50 0.915); component detection is auxiliary and currently low-reliability.

## Known limitations

- 5 model classes unevaluable on this split (zero GT) — reported, not hidden.
- 34 predictions across unevaluated classes count as noise on curated data.
- CUDA latency NOT VERIFIED (no GPU on this machine).

---

## Generalization Risk Assessment — 2026-09-26

### Test Split Board Distribution (components_unified)

**Analysis Date:** 2026-09-26  
**Test Split:** `datasets/components_unified/test` (89 images after cleanup)

**Board Count Analysis:**
- **Total test images:** 89
- **Distinct physical boards:** 9
- **Board IDs:** ArduinoMega, ML450, PCBA, SystemAce, XLVDSproSupply, inductor13, inductor64, s1, transistor58

**Board Distribution:**
| Board ID | Image Count | Percentage |
|----------|-------------|------------|
| s1 | 57 | 64.0% |
| PCBA | 25 | 28.1% |
| ArduinoMega | 1 | 1.1% |
| inductor13 | 1 | 1.1% |
| inductor64 | 1 | 1.1% |
| ML450 | 1 | 1.1% |
| SystemAce | 1 | 1.1% |
| transistor58 | 1 | 1.1% |
| XLVDSproSupply | 1 | 1.1% |

**Generalization Risk:** MODERATE to HIGH

**Rationale:**
- One board (s1) dominates the test split with 64% of images (57/89)
- This concentration may cause the model to overfit to the specific characteristics of the s1 board
- Generalization to unseen boards may be weaker than the test mAP50 suggests
- The other 8 boards have only 1-25 images each, providing limited diversity
- This is a dataset construction limitation, not a model architecture issue

**Recommendation:**
- This limitation should be documented in any publication
- Future data collection should aim for more balanced board distribution
- For now, test metrics should be reported with this caveat

---

## FROM-SCRATCH RETRAINING ATTEMPT (2026-09-26)

### Attempt Summary

**Objective:** Train YOLO11s from scratch on `datasets/components_unified` to replace the weak deployed component model (mAP50 0.093)

**Notebook:** `notebooks/train_component_gpu.ipynb`
**Training Environment:** Kaggle GPU
**Dataset Intended:** `datasets/components_unified` (6 classes: ICs, capacitors, diodes, inductors, resistors, transistors)

### Failure: Wrong Dataset

**Root Cause:** Dataset path bug in notebook execution

**Evidence:**
- Model file: `component_best_new.pt` (19.2 MB)
- Class names from checkpoint: `{0: 'open', 1: 'short', 2: 'mousebite', 3: 'spur', 4: 'copper', 5: 'pin-hole'}`
- These are **defect classes**, not component classes
- Training data path in checkpoint: `/kaggle/working/data_kaggle.yaml` (rewritten during training)

**Discrepancy Explained:**
- **Kaggle-reported metrics:** mAP50 0.9767 (on defect dataset)
- **Local evaluation:** mAP50 ~0 (on component dataset - completely different classes)
- The model was trained on the defect dataset, not the component dataset

### Resolution

**Action Taken:**
- Discarded `component_best_new.pt` (trained on wrong dataset)
- Kept deployed `component_best.pt` (mAP50 0.093) as current model
- Documented this failure for future work

**Status:**
- Component detector remains WEAK (mAP50 0.093)
- This is a documented open item for future work, not a live blocker
- The defect detector carries the inspection workload (mAP50 0.951)

### Required Fix for Future Retrain

The component training notebook must be corrected to:
1. **Hardcode the exact dataset path** to the components_unified upload (no auto-detection)
2. **Verify only ONE component dataset** is uploaded to Kaggle
3. **Confirm class names** match canonical component taxonomy before training
4. **Validate locally** against `datasets/components_unified` immediately after training

### Current Deployment

**Deployed Model:** `models/component_best.pt`
- Classes: 10 (relay, buzzer, ic, switch, battery, transistor, capacitor, resistor, led, diode)
- Test mAP50: 0.093 (9.3%) on curated component dataset
- Status: WEAK, auxiliary detection only
- Primary workload: Defect detection (mAP50 0.951)
