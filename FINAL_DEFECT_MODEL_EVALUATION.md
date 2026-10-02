# FINAL DEFECT MODEL EVALUATION — 2026-09-23

All numbers below were produced on this machine (Windows, Python 3.13.5,
torch 2.13.0+cpu, CPU inference) by
`python scripts/evaluation/evaluate_deployed_models.py --model defect`.
They are measured outputs of the deployed checkpoint `models/defect_best.pt`
on the held-out official DeepPCB test split. Nothing is copied from training
logs; the training-side self-reported figure is cited only as corroboration.

## Alignment (decoding contract)

- Mode: **positional** (`DEFECT_ALIGNMENT_MODE = "positional"`).
- Checkpoint name strings are NOT authoritative (verified 2026-09-23 by
  class-agnostic geometric matching on val: 921/923 diagonal pairs,
  mean IoU 0.899).
- Model decode: `DEFECT_MODEL_INDEX_TO_CANONICAL = {0:open, 1:short,
  2:mousebite, 3:spur, 4:copper, 5:pin-hole}`; index takes precedence.
- GT decode: identity (dataset names already canonical).
- This replaces the disproven name-based decode whose stale artifact
  (`metrics/defect_metrics.json` mAP50 = 0.000112) was an artifact of label
  mismatch, not model quality. The file has been regenerated.

## Test results (500 images, 3140 GT boxes — held out from calibration)

| Threshold | Source | mAP50 | mAP50-95 | micro-F1 |
|-----------|--------|-------|----------|----------|
| 0.25 | default | 0.91473 | 0.723308 | 0.946753 |
| 0.70 | val-calibrated (best micro-F1) | 0.927359 | 0.738340 | 0.959630 |

Threshold sweep ran on VALIDATION ONLY (0.10–0.70 step 0.05); val micro-F1 at
0.70 = 0.988147 (150 val images, 930 GT boxes).

Per-class AP50 @0.25 (all 6 classes present in GT; zero predicted classes
absent from GT):

| Class | AP50 | Precision | Recall | GT | Pred |
|-------|------|-----------|--------|----|------|
| open | 0.967579 | 0.972892 | 0.980273 | 659 | 664 |
| mousebite | 0.959813 | 0.963394 | 0.988055 | 586 | 601 |
| spur | 0.953396 | 0.971134 | 0.975155 | 483 | 485 |
| copper | 0.939022 | 0.919355 | 0.982759 | 464 | 496 |
| short | 0.867292 | 0.868321 | 0.951883 | 478 | 524 |
| pin-hole | 0.801279 | 0.797619 | 0.997872 | 470 | 588 |

Corroboration: the checkpoint's training-side self-reported mAP50 was 0.9079;
our independently measured 0.91473 @0.25 / 0.92736 @0.70 is consistent.

## Determinism / reproducibility

- `--from-raw` re-score from persisted per-image detections/GT
  (`metrics/raw/defect_{val,test}_raw.json`) reproduced identical numbers
  (mAP50 0.91473 / 0.927359). Verified 2026-09-23.
- Repeat engine runs on the same image produce identical detections (CPU).

## Calibration bias disclosure

Local splits: train 850 / val 150 / test 500. Val is drawn from the OFFICIAL
DeepPCB train pool (1000 images), not from local train; val ∩ test = 0,
val ∩ train = 0, test ∩ train = 0 (verified 2026-09-23 by filename-set
comparison). Test is the official held-out 500. Threshold calibration is
therefore biased toward the official-train distribution; test metrics remain
uncontaminated.

## Artifacts

- `metrics/defect_metrics.json` (regenerated 2026-09-23, positional alignment)
- `metrics/threshold_sweep_defect.csv`, `metrics/per_class_defect.csv`
- `metrics/raw/defect_val_raw.json`, `metrics/raw/defect_test_raw.json`
- Log: `metrics/eval_run_defect_positional.log`, determinism:
  `metrics/eval_run_defect_fromraw.log`

## Known limitations

- pin-hole precision 0.80 is the weakest per-class figure (119 FP @0.25);
  FP rate drops at the calibrated 0.70 threshold (80 FP, precision 0.854).
- IoU match threshold fixed at 0.5; COCO-style mAP uses all-point interpolation.
- CUDA latency NOT VERIFIED (no GPU on this machine).
