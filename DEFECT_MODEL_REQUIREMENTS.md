# DEFECT MODEL REQUIREMENTS

**Date:** 2026-09-24  
**Project:** SmartPCB-XAI Defect Detection Accuracy Improvement  
**Base Paper:** "A Lightweight PCB Defect Detection Algorithm Based on an Improved YOLOv11s," Ye et al., IEEE Access 2026

---

## OBJECTIVE

Match or exceed the base paper's reported **92.3% mAP@50** on the **same defect-detection task** using **DeepPCB dataset** (PKU-Market-PCB NOT AVAILABLE).

**Stretch Target:** >94% mAP@50

---

## DATASETS TO BE USED

### ACTUAL DATASET STATUS (UPDATED 2026-09-24)

**LIMITATION DOCUMENTATION:**
- **PKU-Market-PCB: NOT AVAILABLE** - Dataset not present in repository, not acquired due to CPU-only environment and time constraints
- **DeepPCB: AVAILABLE WITH DISCREPANCIES** - Present but class counts and split ratio differ from paper

### Primary Datasets (As Originally Specified)
1. **PKU-Market-PCB** (693 images, 6 classes) - NOT AVAILABLE
   - Classes: missing_hole, mouse_bite, open_circuit, short, spur, spurious_copper
   - Target counts (per paper Table 3):
     - missing hole: 497
     - mouse bite: 492
     - open circuit: 482
     - short: 491
     - spur: 488
     - spurious copper: 503

2. **DeepPCB** (1,500 images, 6 classes) - AVAILABLE WITH DISCREPANCIES
   - Classes: open, short, mousebite, spur, copper, pin-hole
   - **ACTUAL counts (measured):**
     - open_circuit: 1,942 (paper target: 1,702, +240 difference)
     - short: 1,506 (paper target: 1,317, +189 difference)
     - mouse_bite: 1,965 (paper target: 1,748, +217 difference)
     - spur: 1,625 (paper target: 1,445, +180 difference)
     - spurious_copper: 1,474 (paper target: 1,320, +154 difference)
     - missing_hole: 1,501 (paper target: 1,320, +181 difference)
   - **Total boxes: 10,013** (paper target: 8,852, +1,161 difference)
   - **Split ratio: 850:150:500** (56.7%:10%:33.3%, differs from paper's 8:1:1)

### Data Acquisition Strategy (REVISED)
- **PKU-Market-PCB:** NOT ACQUIRED - documented limitation
- **DeepPCB:** Use existing dataset with acknowledged discrepancies
- Class count differences: +1,161 total boxes vs paper target
- Split ratio differences: Different train/val/test distribution
- All discrepancies documented in DATASET_REPORT.md (append)
- Use existing DeepPCB split (not paper's 8:1:1) due to dataset structure

---

## EVALUATION PROTOCOL

### Metrics (matching paper's Table 6-10)
- **Precision (P)**
- **Recall (R)**
- **mAP@50**
- **mAP@50-95**
- **Parameters (params)**
- **FLOPs**
- **Model size (MB)**
- **FPS (frames per second)**

### Success Criteria
- **Base Paper Target:** >92.3% mAP@50
- **Stretch Target:** >94% mAP@50
- **Honest Reporting:** Report actual achieved numbers, even if targets not met

---

## HARDWARE/SOFTWARE ENVIRONMENT

### Available Hardware (ACTUAL)
- **OS:** Windows 10
- **CPU:** 12 cores
- **GPU:** CUDA unavailable (CPU-only execution)
- **RAM:** Standard workstation memory

### Software Versions
- **Python:** 3.13.5
- **PyTorch:** 2.13.0+cpu
- **Ultralytics:** 8.4.98
- **Node.js:** v24.18.0

### Adaptations from Paper (DOCUMENTED DEVIATIONS)
1. **GPU vs CPU:** Paper uses RTX 5060Ti with CUDA 12.9; this environment is CPU-only
   - **Impact:** Reduced batch size, longer training time, no GPU FPS measurements
   - **Adaptation:** Use CPU-compatible batch sizes, report CPU latency instead of GPU FPS

2. **Training Runs:** Paper uses 5 independent runs; this environment may support fewer due to compute/time constraints
   - **Impact:** May report single-run results instead of mean±std
   - **Adaptation:** Document actual number of runs completed

3. **Epochs:** Paper uses 300 epochs; may be infeasible on CPU
   - **Impact:** Early stopping with documented patience
   - **Adaptation:** Use early stopping, report actual epoch count reached

4. **Batch Size:** Paper uses batch size 16; may need reduction for CPU memory
   - **Impact:** Slower convergence, potential performance impact
   - **Adaptation:** Use smaller batch size, document actual value used

5. **Dataset Differences:** Paper uses PKU-Market-PCB + DeepPCB (2,193 images, 8,852 boxes); this environment has DeepPCB only (1,500 images, 10,013 boxes)
   - **Impact:** Different dataset size, class counts, and split ratio
   - **Adaptation:** Use DeepPCB-only training, document dataset discrepancies honestly

6. **Split Ratio:** Paper uses 8:1:1 (80%:10%:10%); DeepPCB has 850:150:500 (56.7%:10%:33.3%)
   - **Impact:** Different train/val/test distribution
   - **Adaptation:** Use existing DeepPCB split, document ratio difference

---

## SEPARATION FROM COMPONENT-DETECTION WORK

**CRITICAL DISTINCTION:**
- **This workstream = DEFECT detection task** (6 classes, DeepPCB only - PKU-Market-PCB NOT AVAILABLE)
- **Previous workstream = COMPONENT detection task** (6 classes, FICS + Roboflow, different data)
- **These are SEPARATE tasks on DIFFERENT datasets**
- **Never present component-detection numbers as defect-detection benchmarks**
- **Never mix the datasets or taxonomies**

### Component-Detection Workstream Status (PRESERVED)
- Canonical 6-class component dataset: 9 images, 587 boxes
- High-resolution tiled inference: 960×960 tiles, 33% overlap
- Improved detection: High-resolution tiled inference (precision/recall metrics require proper test set evaluation)
- **Status:** COMPLETE and UNDISTURBED

### Defect-Detection Workstream (THIS PROJECT)
- **NEW TASK:** Defect detection on DeepPCB only (PKU-Market-PCB NOT AVAILABLE)
- **NEW DATA:** DeepPCB dataset (1,500 images, 10,013 boxes) with documented discrepancies
- **NEW EVALUATION:** Separate metrics, separate baselines
- **GOAL:** Achieve >92.3% mAP@50 on defect-detection task (with dataset limitations)

---

## WORKSTREAM STRUCTURE

### Phase 1: Requirements & Planning ✅ (THIS FILE)
- Define objective, datasets, evaluation protocol, success criteria
- Document hardware/software environment and adaptations
- Clearly separate from component-detection work

### Phase 2: Dataset Acquisition & Validation ✅ COMPLETED WITH LIMITATIONS
- PKU-Market-PCB: NOT ACQUIRED (documented limitation)
- DeepPCB: AVAILABLE but with discrepancies (documented in DATASET_REPORT.md)
- Validated class counts: 10,013 boxes vs paper's 8,852 (+1,161 difference)
- Validated split ratio: 850:150:500 vs paper's 8:1:1
- Documented all discrepancies in DATASET_REPORT.md (append)

### Phase 3: Baseline Replication
- Train plain YOLOv11s baseline on DeepPCB dataset
- Use paper's hyperparameters as starting point (adapted for CPU)
- Evaluate on held-out test split
- Save baseline results as `results/baseline_yolo11s_defect.json/.csv`
- This is the number all improvements must beat

### Phase 4: Architecture Improvements (Incremental Ablation)
- Implement backbone swap (EfficientViT-style)
- Implement neck improvement (PConv + EMA)
- Implement loss function improvement (Inner-IoU + Wise-IoU v3)
- Each stage ablated separately with real measured deltas
- Produce ablation table matching paper's Table 6 format

### Phase 5: Hyperparameter & Threshold Calibration
- Sweep confidence thresholds on validation data only
- Report precision/recall/F1 for each threshold
- Select operating threshold from evidence
- Multi-run statistics if compute allows (or document single-run caveat)

### Phase 6: Testing (SDLC Test Layer)
- Unit tests for new components (loss functions, attention blocks, etc.)
- Integration tests for full modified model
- Regression tests for existing component-detection pipeline
- End-to-end test with real images
- Record test counts and pass/fail in TEST_REPORT.md

### Phase 7: Comparative & Generalization Evaluation
- Reproduce comparison table vs. other YOLO variants (Table 10 format)
- Zero-shot evaluation on third dataset if accessible (DsPCBSD+)
- Generate qualitative visual comparisons (Fig. 7 style)

### Phase 8: Deployment / Efficiency Check
- Export final model to ONNX
- Measure CPU inference latency on actual hardware
- Report model size and latency numbers
- Edge deployment only if hardware genuinely available

### Phase 9: Documentation & Report
- Produce FINAL_DEFECT_MODEL_EVALUATION.md
- Update DATASET_REPORT.md and PROJECT_AUDIT.md (append-only)
- Rewrite unsupported claims with actual measured numbers
- Honest final verdict on whether 92.3% and 94% targets achieved

---

## FINAL DELIVERABLE CHECKLIST

- [x] DEFECT_MODEL_REQUIREMENTS.md created ✅ (THIS FILE)
- [x] PKU-Market-PCB + DeepPCB dataset validation completed with limitations documented
- [ ] Baseline YOLOv11s trained and evaluated, results saved
- [ ] Backbone, neck, and loss improvements implemented incrementally, each ablated
- [ ] Confidence threshold calibrated on validation data only
- [ ] Multi-run statistics reported honestly (or single-run caveat stated)
- [ ] Unit, integration, regression, and end-to-end tests written and passing
- [ ] Comparison table vs. other YOLO variants produced
- [ ] Qualitative visual comparisons saved
- [ ] Deployment/efficiency numbers measured (or marked not attempted)
- [ ] FINAL_DEFECT_MODEL_EVALUATION.md written with honest final verdict
- [x] All protected docs updated append-only, component-detection track left intact

---

## FINAL RESPONSE FORMAT REQUIREMENT

At completion of this workstream, I will state:

1. **Exact final mAP@50 and mAP50-95 achieved** (on which dataset/split, hardware, runs)
2. **Whether this exceeds 92.3%** (paper baseline) and **whether it exceeds 94%** (stretch target)
3. **Every ablation stage's measured delta** (backbone, neck, loss)
4. **Test counts and pass/fail** (unit, integration, regression, end-to-end)
5. **What was NOT attempted and why** (compute, data, hardware, time)
6. **Exact commands to reproduce every reported number**

**NO vague "successfully improved accuracy" summaries — only real numbers or NOT VERIFIED status.**

---

**STATUS:** Phase 1-2 Complete ✅ (with documented limitations)  
**NEXT:** Phase 3 - Baseline Replication (YOLOv11s training on DeepPCB)