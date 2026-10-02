# VERIFICATION_LOG_DEFECT_MODEL.md - APPENDIX

## MAP DISCREPANCY RECONCILIATION (2026-09-25)

### Two Numbers Reported

**Number 1:** 0.91473 (91.47%) mAP50 @ conf 0.25
- Source: `scripts/evaluation/evaluate_deployed_models.py --model defect`
- Date: 2026-09-23
- Documented in: `FINAL_DEFECT_MODEL_EVALUATION.md`
- Checkpoint: `models/defect_best.pt`
- Split: Test (500 images, 3140 GT boxes)

**Number 2:** 0.983 (98.3%) mAP50
- Source: Ultralytics standard `yolo val`
- Date: 2026-09-24
- Documented in: `reports/eval/PHASE1_DEFECT_VERIFICATION.md`
- Checkpoint: `models/defect_best.pt` (SAME as above)
- Split: Test (500 images, 3140 GT boxes)

### Methodological Differences

| Aspect | Custom Evaluator (0.91473) | Ultralytics Standard (0.983) |
|--------|---------------------------|-------------------------------|
| IoU matching threshold | 0.5 (fixed) | 0.6 (specified in command) |
| Confidence handling | Fixed threshold (0.25) | Full PR curve integration (all confidences) |
| mAP calculation | Custom all-point interpolated AP | Framework-native COCO-style AP |
| Class name handling | Positional index mapping | Checkpoint native names |
| AP integration | Custom implementation | Ultralytics optimized implementation |

### Root Cause of Difference

The ~7 percentage point difference (0.91473 vs 0.983) is due to:

1. **Confidence integration:** Ultralytics integrates over ALL confidence thresholds, including very low confidences that yield higher recall. The custom evaluator uses a fixed threshold of 0.25, which is more representative of actual deployment.

2. **IoU threshold:** Ultralytics uses iou=0.6 (slightly more lenient), while the custom evaluator uses iou=0.5 (slightly stricter).

3. **Implementation:** Ultralytics uses the framework's native, optimized COCO-style AP calculation, while the custom evaluator uses a custom all-point interpolated AP implementation.

### Which Number is "Correct"?

**For research/publication context:** The Ultralytics standard (0.983) is the "correct" number because:
- It uses the framework-native evaluation method
- It matches how YOLO models are typically evaluated in published research
- It integrates over the full confidence distribution (more robust)

**For deployment context:** The custom evaluator (0.91473) is more representative because:
- It uses a fixed confidence threshold (0.25) that matches actual deployment
- It uses a stricter IoU threshold (0.5) that is more conservative
- It uses the positional index mapping that matches the system's actual operation

### Recommendation

**Until from-scratch training is completed, the citable/publishable number should be 0.91473** because:
- It reflects the actual deployment scenario (fixed confidence threshold)
- It is more conservative (safer to report lower number)
- It is from a carefully-verified independent evaluator
- The higher Ultralytics number (0.983) may be inflated by including very low-confidence detections

**After from-scratch training is completed:**
- Evaluate the new model with BOTH methods
- Report BOTH numbers with clear methodological labels
- Use the Ultralytics standard for research/publication
- Use the custom evaluator for deployment configuration

### Contamination Risk

The checkpoint provenance recovery shows:
- Trained on Kaggle (unknown training data source)
- YOLO11m, 50 epochs, multi-GPU
- Remote dataset path: `/kaggle/working/data_rtdetr_fixed.yaml`
- Local train/test leakage: VERIFIED NONE
- Remote contamination: UNVERIFIABLE

The tight clustering of train (0.993) / val (0.993) / test (0.983) mAP50 is suspicious and could indicate train/test overlap in the remote Kaggle training data.

### Next Step

The ONLY way to resolve this contamination ambiguity is to train from scratch on the local dataset using the prepared notebook `notebooks/train_defect_from_scratch.ipynb`. This will provide a verified, contamination-free number.

### Command to Re-produce Custom Evaluator Result

```bash
python scripts/evaluation/evaluate_deployed_models.py --model defect
```

### Command to Re-produce Ultralytics Standard Result

```bash
yolo val model=models/defect_best.pt data=datasets/defects/data.yaml split=test imgsz=640 conf=0.001 iou=0.6
```

### Conclusion

**Same checkpoint (models/defect_best.pt), different evaluation methods.**
- Custom evaluator: 0.91473 (fixed conf 0.25, iou 0.5)
- Ultralytics standard: 0.983 (full PR curve, iou 0.6)

**Pending from-scratch training to resolve contamination ambiguity.**