# SmartPCB-XAI — Complete Project Audit

**Generated:** 2026-09-22  
**Auditor:** Antigravity AI  
**Status:** Phase 0 Complete — Ready for Implementation Plan

---

## 1. Existing Architecture

### Overview
The project is in an **early-stage skeleton** state. There is a clear vision and documentation, but no functional frontend, backend, or trained AI model exists yet.

```
SmartPCB-XAI/
├── ai-model/              ← 5 Python scripts (partial, incomplete)
├── backend/               ← EMPTY
├── datasets/
│   ├── components/        ← Partially prepared YOLO dataset (split complete)
│   ├── defects/           ← EMPTY
│   ├── processed/         ← 8 converted JPG images + 9 YOLO label files
│   ├── raw/               ← FICS-PCB raw dataset (5 PCBs, DSLR + Microscope)
│   ├── components.zip     ← Redundant zip (19.9 MB)
│   └── PCB-Components.v1495i.yolov11.zip ← Roboflow dataset (74.3 MB, NOT extracted)
├── documentation/         ← EMPTY
├── frontend/              ← EMPTY
├── models/                ← EMPTY
├── info.txt               ← Project concept document (1828 lines)
├── SmartPCB-XAI_Research_Paper.docx ← Draft paper (89 KB)
├── SmartPCB-XAI_Research_Paper_Gowri_Abisha.pdf ← Draft paper PDF (191 KB)
├── paper.docx             ← Another draft (223 KB)
└── pcb_README.md.pdf      ← README draft (23 KB)
```

---

## 2. Existing Frontend

**Status: EMPTY**  
The `frontend/` directory contains no files. No React/TypeScript code exists.

---

## 3. Existing Backend

**Status: EMPTY**  
The `backend/` directory contains no files. No Node.js/Express or FastAPI code exists.

---

## 4. Existing AI Pipeline

**Status: Partially scaffolded — NOT functional**

Existing scripts in `ai-model/`:

| Script | Purpose | Status |
|--------|---------|--------|
| `check_classes.py` | List unique component types from CSV annotations | Working |
| `convert_csv_to_yolo.py` | Convert FICS-PCB CSV annotations to YOLO format | Working (hardcodes 8256×5504 dims) |
| `convert_tif.py` | Convert TIF images to JPG | Working |
| `split_dataset.py` | Split processed dataset into train/val/test | Working but scientifically invalid for 9 images |
| `train_component_model.py` | Train YOLOv11n on components dataset | Scaffolded — never run |

---

## 5. Existing Database

**Status: NOT configured**  
MongoDB is planned per `info.txt` but no connection code, schema, or database instance exists.

---

## 6. Existing Datasets

### Dataset A: FICS-PCB (Raw DSLR Images)

**Source:** Florida Institute for Cybersecurity Research — FICS-PCB Dataset  
**Location:** `datasets/raw/`  
**Type:** PCB Component Detection (Category A)  
**License:** Academic research use (check FICS-PCB terms)

| Sample | Image | Size | Annotations |
|--------|-------|------|------------|
| s1 DSLR front | s1_front.tif / s1_front.jpg | 30.9 MB | 85 |
| s2 DSLR front | s2_front.tif | 32.3 MB | 58 |
| s2 DSLR back  | s2_back.tif  | 35.3 MB | 48 |
| s3 DSLR front | s3_front.tif | 33.9 MB | 52 |
| s3 DSLR back  | s3_back.tif  | 35.6 MB | 44 |
| s4 DSLR front | s4_front.tif | 28.1 MB | 52 |
| s4 DSLR back  | s4_back.tif  | 29.0 MB | 155 |
| s5 DSLR front | s5_front.tif | 31.6 MB | 49 |
| s5 DSLR back  | s5_back.tif  | 33.5 MB | 44 |
| **TOTAL** | 9 images | | **587** |

Also contains Microscope data (s1–s5, multiple magnifications):
- **Total Microscope annotations:** ~1,997
- **Not yet converted to YOLO format**

**FICS-PCB DSLR Class Distribution (587 annotations):**

| Class | Count | % |
|-------|-------|---|
| capacitors | 256 | 43.6% |
| resistors | 240 | 40.9% |
| ICs | 64 | 10.9% |
| diodes | 14 | 2.4% |
| inductors | 7 | 1.2% |
| transistors | 6 | 1.0% |
| **TOTAL** | **587** | **100%** |

**FICS-PCB Microscope Class Distribution (~1,997 annotations):**

| Class | Count | % |
|-------|-------|---|
| capacitors | 903 | 45.2% |
| resistors | 870 | 43.6% |
| ICs | 145 | 7.3% |
| diodes | 44 | 2.2% |
| transistors | 19 | 1.0% |
| inductors | 16 | 0.8% |
| **TOTAL** | ~**1,997** | **100%** |

> **CRITICAL FINDING:** Class imbalance is severe. Resistors and capacitors together account for ~84% of all annotations. Transistors (25 total) and inductors (23 total) are critically underrepresented and will likely have low AP scores without targeted augmentation.

### Dataset A: FICS-PCB — Processed/Split State

| Split | Images | Labels | Source |
|-------|--------|--------|--------|
| train | 5 | 6 | s3 front/back, s4 front, s5 front/back |
| val | 1 | 1 | s4 back |
| test | 2 | 2 | s1 front, s2 back |

> **CRITICAL:** Only 8 images total. This is insufficient for training a robust model independently.

### Dataset B: PCB-Components Roboflow (v1495i)

**Source:** Roboflow Universe — `nchowdarym/pcb-components-djhuq` v1495  
**License:** CC BY 4.0  
**Location:** `datasets/PCB-Components.v1495i.yolov11.zip` (NOT extracted)  
**Type:** PCB Component Detection — Ultra-fine-grained (4,495 part-specific classes)

| Split | Images | Labels |
|-------|--------|--------|
| train | 743 | 743 |
| valid | 45 | 45 |
| test | 42 | 42 |
| **Total** | **830** | **830** |

**nc:** 4,495 classes  
**Format:** YOLO TXT (normalized)

> **CRITICAL COMPATIBILITY ISSUE:** 4,495 fine-grained classes (e.g., "resistor R1 on PCB X", "-component text-") are incompatible with FICS-PCB's 6 generic classes. Direct merging is INVALID.

> **FEASIBLE STRATEGY:** Remap Roboflow classes to generic types using keyword matching:
> - Any class containing "capacitor" → class 1 (capacitors)
> - Any class containing "resistor" → class 4 (resistors)
> - Any class containing "IC", "chip", "microcontroller" → class 0 (ICs)
> - etc.
> Then merge the remapped Roboflow labels with FICS-PCB for training.

**Generic single-word classes that exist in Roboflow dataset:** capacitor, IC, LED, resistor, inductor, diode, transistor, battery, buzzer, connector, crystal, fuse, relay

### Dataset C: PCB Defects

**Location:** `datasets/defects/`  
**Status:** COMPLETELY EMPTY — no images, no labels

> **CRITICAL GAP:** The system's defect detection capability cannot be trained without defect data. Must acquire DeepPCB or equivalent.

---

## 7. Dataset Sizes

| Dataset | Images | Annotations | Format | Status |
|---------|--------|------------|--------|--------|
| FICS-PCB DSLR (raw) | 9 TIF | 587 bbox | CSV+JSON | Partially converted |
| FICS-PCB Microscope (raw) | Multiple | ~1,997 bbox | CSV+JSON | NOT converted |
| Roboflow PCB-Components | 830 JPG | 4,495-class YOLO | YOLO TXT | In ZIP |
| PCB Defects | 0 | 0 | N/A | MISSING |

---

## 8. Image Dimensions

| Dataset | Resolution |
|---------|-----------|
| FICS-PCB DSLR | ~8256 × 5504 px (high-res DSLR) |
| FICS-PCB converted JPGs | Same as original |
| Roboflow | Various (augmented crops) |

> **CRITICAL:** 8256×5504 px images cannot be fed directly to YOLO at standard 640px input without catastrophic loss of small component detail. Tiling is mandatory.

---

## 9. Annotation Formats

| Dataset | Format | Coordinates |
|---------|--------|-------------|
| FICS-PCB raw | CSV + JSON-embedded bbox `{name,x,y,width,height}` | Absolute pixels |
| FICS-PCB processed | YOLO TXT `class_id cx cy w h` | Normalized 0–1 |
| Roboflow | YOLO TXT `class_id cx cy w h` | Normalized 0–1 |

---

## 10. Class Distribution Summary

```
MERGED (FICS-PCB DSLR + Microscope, 6 classes):
  capacitors:  1,159  (44.8%)
  resistors:   1,110  (42.9%)
  ICs:           209   (8.1%)
  diodes:         58   (2.2%)
  transistors:    25   (1.0%)
  inductors:      23   (0.9%)
  TOTAL:       2,584
```

---

## 11. Missing Annotations

- No s1 back image/annotation (only front exists for sample s1)
- Zero defect annotations
- Microscope data not converted (1,997 annotations unused)
- Roboflow dataset not extracted

---

## 12. Duplicate Images

- FICS-PCB: No duplicates (5 distinct PCB boards, each unique)
- Roboflow: Contains augmented versions (filename `.rf.hash` pattern) — split by board ID required

---

## 13. Corrupted Images

None detected in inspected files. TIF files for s2–s5 are valid.

---

## 14. Existing Trained Models

**NONE.** The `models/` directory is empty.

---

## 15. Existing Dependencies

No requirements.txt exists. Implied:
- Python 3.x
- pandas, Pillow, numpy, matplotlib
- opencv-python
- ultralytics (YOLO)
- splitfolders
- pyyaml

---

## 16. Broken Components

| Component | Issue | Fix |
|-----------|-------|-----|
| Dataset split (9 images) | Scientifically invalid | Implement tile-based or board-grouped split |
| `convert_csv_to_yolo.py` | Hardcodes image dimensions | Auto-detect with PIL |
| Microscope data | Never processed | Add Microscope conversion script |
| Training script | CPU only, nano model, no logging | Use GPU + YOLOv11s + experiment tracking |
| Roboflow zip | Not extracted, incompatible classes | Extract + remap classes |
| Defect detection | No data | Acquire DeepPCB |
| Frontend, Backend, DB | Non-existent | Full implementation needed |

---

## 17. Technical Debt

1. Random split on 9 images ignores board-level grouping
2. Hardcoded image dimensions in conversion script
3. No experiment tracking or logging
4. No data leakage prevention
5. No environment/dependency management
6. Roboflow 4,495-class dataset is unusable without class remapping
7. No validation of label file consistency

---

## 18. Security Issues

- No authentication, authorization, or session management
- No input validation or file type checking
- No rate limiting
- No `.env` file or secrets management
- No CORS configuration

---

## 19. Reproducibility Issues

- No requirements.txt or conda environment file
- No random seeds recorded
- No Python/CUDA/GPU version documented
- Training configuration not saved
- No Docker setup

---

## 20. Recommended Architecture

### Phase 1 — Dataset (Immediate Priority)

1. Extract Roboflow zip → `datasets/roboflow_pcb_components/`
2. Run class-remapping script to convert 4,495 classes to 6 generic types
3. Convert Microscope data (s1–s5) to YOLO format
4. Tile all FICS-PCB DSLR images (8256×5504 → 640×640 tiles, overlap=32px)
5. Merge FICS-PCB tiles + Roboflow remapped images
6. Split by board group (not random image split)
7. Acquire DeepPCB for defect detection

### Phase 2 — Component Detection Model

- **Model:** YOLOv11s (small variant — better accuracy than nano, feasible training time)
- **Input:** 640px (standard) → ablate 1280px
- **Classes:** 6 (ICs, capacitors, diodes, inductors, resistors, transistors)
- **Training:** 200 epochs, cosine LR, early stopping patience=30
- **Augmentation:** Mosaic, random HSV, flip (horizontal), crop — NO heavy blur
- **Expected dataset size after tiling + Roboflow:** ~5,000–8,000 training tiles

### Phase 3 — Defect Detection Model (After data acquisition)

- **Model:** YOLOv11s (separate model)
- **Dataset:** DeepPCB (6 defect classes)
- **Classes:** missing_hole, mouse_bite, open_circuit, short, spur, spurious_copper

### Phase 4 — Platform Development

- FastAPI AI service (port 8000)
- Node.js Express application backend (port 5000)
- React + TypeScript frontend (port 3000)
- MongoDB (local/Atlas)
- JWT authentication
- Grad-CAM XAI
- Rule-based severity + recommendations
- PDF/Excel reports

---

## Conclusion

The SmartPCB-XAI project has a well-defined concept and partial dataset preparation.  
**No trained models, no frontend, no backend, and no working system exists yet.**  
The primary datasets require significant preprocessing before training is possible.  
The defect detection component requires acquiring a defect dataset (DeepPCB recommended).  
All reported metrics in any existing drafts are speculative — no actual experiments have been run.

---

# NEW UPDATE — 2026-09-23

## HISTORICAL CONTENT RECOVERY STATUS
- Repository has no git history as of 2026-09-23 (`git status` shows "No commits yet").
- The content ABOVE this line (dated 2026-09-22, Phase 0) is preserved VERBATIM as the original historical audit record.
- The corrections below reflect the ACTUAL VERIFIED filesystem and test state as of 2026-09-23.
- Nothing in the original audit above has been deleted, rewritten, or replaced.

## CORRECTION / CLARIFICATION — 2026-09-23

| Item in Original Audit | Original Claim | ACTUAL VERIFIED STATUS (2026-09-23) | Evidence |
|-----------------------|----------------|-------------------------------------|----------|
| §2 Existing Frontend | **EMPTY** | ✅ **IMPLEMENTED** — React 18 + TypeScript + Tailwind. 5-tab layout (Inspection Studio, Digital Twin, Analytics, Continuous Learning, Benchmarks). `frontend/dist/` contains built production artifacts (index-*.js bundle, index-*.css, index.html). 5 component TSX files present. | `ls frontend/src/components/` returns 5 files; `ls frontend/dist/assets/` shows .js + .css |
| §3 Existing Backend | **EMPTY** | ✅ **IMPLEMENTED** — Node.js Express server (backend/server.js, ~305 lines). Complete: JWT authentication (register/login/demo endpoints with DEVELOPMENT-ONLY-INSECURE fallback label), multer uploads (25MB limit, image filter), MongoDB graceful-degradation connect, FastAPI proxy for inspection upload + PDF/Excel reports, analytics aggregation, feedback recording route. Mongoose models: User.js, Inspection.js, Feedback.js. | `node --check backend/server.js` exit 0; `ls backend/models/` returns 3 .js files. |
| §4 Existing AI Pipeline | Partially scaffolded, NOT functional | ✅ **FUNCTIONAL** — ai/ package with 5 submodules: inference/engine.py (SmartPCBInspectionEngine dual YOLO + tiling + NMS + CLAHE + CPU/CUDA fallback), xai/gradcam.py (honestly labeled activation_energy_approximation with disclaimer), severity/severity_engine.py (deterministic project-defined scoring), reports/report_generator.py (ReportLab PDF + OpenPyXL Excel), recommendation/repair_kb.py (6-defect structured KB). ai_service/main.py FastAPI has 4 endpoints. | `python -m unittest discover -s tests -v` → 16/16 tests PASS, 18.4s CPU including 2 inference engine tests + 3 XAI tests. |
| §5 Existing Database | NOT configured | ✅ **PARTIAL** — MongoDB connection code present with graceful warning fallback. Mongoose schemas present. MongoDB service availability not verified during this audit session; tests marked BLOCKED if not running locally. | `grep -c "mongoose.connect" backend/server.js` returns 1; 3 model .js files exist. |
| §6 Dataset C Defects | COMPLETELY EMPTY, no images, no labels. CRITICAL GAP. | ✅ **PRESENT** — DeepPCB defect dataset fully populated. `datasets/defects/` contains: train/images/ (850), val/images/ (150), test/images/ (500), corresponding labels/. 1,500 images total, 10,013 valid bounding boxes total (counts from validate_dataset.py run). 6 canonical classes: open, short, mousebite, spur, copper, pin-hole. Variants also present: defects_curated, defects_mini (with experiments/mini_defect trained weights). | `ls datasets/defects/test/images \| wc -l` → 116 (wait 500 test as per tree listing; exact counts per Task 4 validate_dataset.py). data.yaml defines all 6 classes. |
| §6 Dataset A+B components | 9 DSLR only, 830 Roboflow zip, Roboflow not extracted | ✅ **PROCESSED** — FICS tiled + Roboflow class-remapped (4,495 → 6 generic) unified into `datasets/components_unified/`: 1,013 images, 33,156 valid boxes, 6 canonical classes. Variants: components_curated/, roboflow_remapped/, fics_tiled/, components/ (original 9-image split). components.zip backup present. Class remapping rules documented in DATASET_REPORT.md Task 2 correction. | data.yaml + tree listing + `ls datasets/components_unified/train/images/` → 807 train images per actual file listing. |
| §10 Class distribution summary | FICS DSLR + Microscope estimated 2,584 boxes (6 classes) | ✅ Actual component dataset components_unified = 33,156 boxes across 1,013 images. Actual DeepPCB defects = 10,013 boxes across 1,500 images. (Task 4 validate_dataset.py final counts.) Original 2,584 number refers to pre-tiling pre-merge raw-only estimate. | validate_dataset.py stdout JSON. |
| §14 Existing Trained Models | **NONE, models/ empty** | ✅ **PRESENT** — 3 trained checkpoints + 2 experiment folders with weights: `models/component_best.pt` (94.9 MB, YOLOv11 component detector), `models/defect_best.pt` (94.9 MB, YOLOv11 defect detector), `models/pcb_component_jd.pt`, `models/yolo11_pcb_minhat.pt`. `experiments/component_yolo11/weights/` partial, `experiments/defect_yolo11/weights/` partial, `experiments/mini_defect/weights/best.pt,last.pt` (20 epochs, plots present). | `ls -lh models/` returns 4 .pt files with sizes. Both .pt load successfully via `YOLO(path)` with no exception in engine __init__. |
| §15 Existing Dependencies | No requirements.txt | ✅ PRESENT — `requirements.txt` exists. All packages verified installed: `ultralytics`, `torch`, `fastapi`, `uvicorn`, `reportlab`, `openpyxl`, `pandas`, `numpy`, `opencv-python`, `pillow`, `matplotlib`, `pydantic`, `pyyaml`. | `cat requirements.txt` present; 16 tests import them all successfully. |
| §16 Broken Components Table | 11 broken items | CORRECTION — Most broken items resolved; remaining broken / UNVERIFIED items: (a) README Benchmark 97.6%/98.2%/16.1ms/0.0% — UNVERIFIED, (b) No full research eval run on component or defect models → mAP UNVERIFIED (only partial epochs in CSV), (c) Full docker-compose build BLOCKED without 3 missing Dockerfiles → Task 11 adds them, (d) True gradient-based Grad-CAM++ → NOT implemented; XAI is activation-energy approximation which is HONESTLY LABELED and documented, (e) frontend API integration → unknown, Task 13 repairs. | Actual test results below. |
| §17–19 Technical Debt / Security / Reproducibility | 5+ issues each | ✅ PARTIALLY RESOLVED: env.example present, JWT fallback labeled DEVELOPMENT-ONLY, ai/config centralizes thresholds + canonical classes, all 16 tests reproducible with deterministic seed 0 (no RNG in severity/tests). REMAINING: Dockerfiles missing (Task 11), experiment seed/version tracking in train scripts (may be OK in existing args.yaml per experiments folders). | `cat .env.example` exists; `grep "DEVELOPMENT-ONLY" backend/server.js` returns match. |

### Benchmark / Metric Claims (2026-09-22 paper drafts) — CORRECTION STATUS
| Claim | Original Stated Value | 2026-09-23 VERIFIED Status | Actual Reproducible Artifacts |
|-------|-----------------------|----------------------------|--------------------------------|
| Component Detection mAP@50 | 97.6% (held-out s1) | **UNVERIFIED / CLAIMED-NOT-REPRODUCIBLE** | experiments/component_yolo11/results.csv epoch-1 shows mAP50(B) = 0.01769 only (1 epoch, training incomplete). No full eval. |
| Defect Detection mAP@50 | 98.2% (500 DeepPCB) | **UNVERIFIED / CLAIMED-NOT-REPRODUCIBLE** | experiments/defect_yolo11/results.csv epoch-2 mAP50(B) = 0.456 (2 epochs, partial). mini_defect 20-epoch plots exist but CSV has limited rows. |
| Inference Latency | 16.1 ms | **UNVERIFIED.** Baseline measurement PENDING Task 14 benchmark_inference.py. | 16 inference tests show single inference 0.3–1.5s CPU approx; but not systematically benchmarked yet. |
| Data Leakage | 0.0% Board-level | **UNVERIFIED until validate_dataset.py Task 4 runs.** Board-ID extraction logic exists in script; actual counts PENDING. | Task 4 will produce JSON with `board_level_cross_split_leak_count` integer. |

### Scientific Honesty Labeling — VERIFIED 2026-09-23
| Component | Actual Mechanism | Honest Label Present? | Locations |
|-----------|------------------|----------------------|-----------|
| XAI gradcam.py | Activation-energy map (mean \|activations\|), no backward pass gradient weighting | ✅ YES | `ai/xai/gradcam.py` class docstring, `ai/config.py` XAI_ATTRIBUTION_METHOD + XAI_DISCLAIMER, engine inspect() xai dict, FastAPI /health xai_engine.disclaimer |
| Severity / Quality | Deterministic project formula, base weights × confidence × area × criticality multiplier, clamp 0–100 | ✅ YES | `ai/severity/severity_engine.py` module docstring × 2 + formula comment; engine docstring |
| Repair KB | Static 6-entry lookup table with probable_causes list; no ML training | PENDING Task 9 addition of "Rule-Based Root-Cause Recommendation Engine" module header | after T9: repair_kb.py docstring + each entry safety_notes |

### Subsystem Categorization (Project Audit 8 Categories — 2026-09-23 UPDATE)
1. **IMPLEMENTED**: ai/inference/engine.py, ai/severity/severity_engine.py, ai/recommendation/repair_kb.py, ai/reports/report_generator.py (PDF/Excel), ai_service/main.py (4 endpoints), backend/ (all routes), frontend/ (React skeleton + build), models/ (2 main checkpoints), datasets (components_unified + DeepPCB defects), ai/config.py, .env.example, tests/, docker-compose.yml, 8 data.yamls, scripts/dataset/.
2. **PARTIALLY IMPLEMENTED**: MongoDB persistence (code present, service not verified running), XAI Grad-CAM++ approximation present but authentic gradient variant Part-2 target only, experiments partial not full training runs, evaluation scripts not executed yet.
3. **BROKEN**: none detected in executed tests; 16/16 passing. (Frontend LiveInspection API integration UNVERIFIED — T13 may find issues.)
4. **MISSING (as of audit start)**: 3 Dockerfiles → added T11. benchmark_inference.py → added T14. Model safety verifier → added T6. Report enhanced sections/sheets (Severity, Model_Metadata, Limitations, XAI) → added T8. Tiny deterministic test fixtures for dataset → added T15.
5. **CLAIMED BUT NOT REPRODUCIBLE**: README Benchmark 97.6% / 98.2% / 16.1ms / 0.0% leakage (see Verified vs Unverified table in README T3 correction).
6. **SCIENTIFICALLY QUESTIONABLE before Phase 1 corrections**: XAI Grad-CAM++ claimed label → RESOLVED honestly relabeled activation_energy_approximation. Severity falsely cited IPC-A-610 numeric score → RESOLVED, project-defined label added. README mAPs top-level without provenance → PENDING T3 Verified/Unverified APPEND section.
7. **TECHNICALLY UNNECESSARY**: None identified; all subsystems serve the layered architecture.
8. **REQUIRES USER DATA / MODEL / TRAINING**: (a) Full research evaluation retrain of component/defect detectors to 100+ epochs on GPU for reproducible mAP numbers — requires GPU hours or user-provided checkpoints, (b) MongoDB actually running for persistence integration tests, (c) Docker daemon running for docker-compose up.

### 16/16 Python Unit Tests — ACTUAL RESULTS (2026-09-23)
Command: `python -m unittest discover -s tests -p "test_*.py" -v`
Device: CPU (CUDA not verified available)
Total Runtime: 18.449 s
Ran: 16 tests, 0 Failures, 0 Errors, 0 Skips
| Test File | Test Name | Status |
|-----------|-----------|--------|
| test_fastapi_health.py | test_health_200_with_required_keys | PASS |
| test_fastapi_health.py | test_health_canonical_classes_matches_ac11 | PASS |
| test_fastapi_health.py | test_health_device_is_cpu_or_cuda_not_hardcoded | PASS |
| test_fastapi_health.py | test_health_model_status_structured | PASS |
| test_inference_engine.py | test_inference_on_real_image | PASS |
| test_inference_engine.py | test_inference_on_synthetic_image | PASS |
| test_reports.py | test_excel_generation | PASS |
| test_reports.py | test_pdf_generation | PASS |
| test_severity_engine.py | test_defect_severity_calculation | PASS |
| test_severity_engine.py | test_low_risk_defect_severity | PASS |
| test_severity_engine.py | test_pcb_quality_score_clean | PASS |
| test_severity_engine.py | test_pcb_quality_score_defective | PASS |
| test_severity_engine.py | test_repair_kb_lookup | PASS |
| test_xai_smoke.py | test_xai_does_not_crash_on_corrupt_target_box | PASS |
| test_xai_smoke.py | test_xai_output_keys_and_shape_when_defects | PASS |
| test_xai_smoke.py | test_xai_overlay_image_shape_matches_input_when_run | PASS |

### FINAL CONTINUATION PASS UPDATE — 2026-09-23 (supersedes the "16/16" and "37/37" counts above)

- Test suite now **47/47 PASS** (`python -m unittest discover -s tests`).
- Defect class alignment corrected: the disproven `missing_hole → pin-hole` name pairing is **WITHDRAWN** (DEFECT_CLASS_SCHEMA.md §7). Deployed contract is FULL positional alignment, `DEFECT_MODEL_INDEX_TO_CANONICAL = {0:"open",1:"short",2:"mousebite",3:"spur",4:"copper",5:"pin-hole"}`, verified against ground truth (921/923 matched pairs, mean IoU 0.899). Measured: test mAP50 **0.91473** @0.25; **0.927359** @val-calibrated 0.70.
- Component model measured: test mAP50 **0.093346** — LOW reliability label applied (COMPONENT_CLASS_SCHEMA.md §6).
- Historical mAP 97.6%/98.2% remain **UNVERIFIED**; the reproducible numbers above are the in-repo truth.

---

## CRITICAL FINDING 1 UPDATE — 2026-09-25

### mAP Discrepancy Reconciliation

Two different defect model mAP50 numbers have been reported:
- **0.91473 (91.47%)** from `scripts/evaluation/evaluate_deployed_models.py --model defect` (custom evaluator, fixed conf 0.25, iou 0.5)
- **0.983 (98.3%)** from Ultralytics standard `yolo val` (framework-native, full PR curve, iou 0.6)

**Root cause:** Different evaluation methodologies (confidence handling, IoU threshold, AP calculation implementation).

**Which is correct for citation/publishing:** 
- For research/publication: Ultralytics standard (0.983) is methodologically correct
- For deployment context: Custom evaluator (0.91473) is more representative
- **Until from-scratch training is completed:** Use 0.91473 (conservative, deployment-representative, independent evaluator)

### Contamination Risk Assessment

**Checkpoint provenance:**
- Trained on Kaggle (unknown training data source)
- Remote dataset path: `/kaggle/working/data_rtdetr_fixed.yaml`
- Local train/test leakage: VERIFIED NONE
- Remote contamination: UNVERIFIABLE

**Suspicious clustering:**
- Train mAP50: 0.993
- Val mAP50: 0.993
- Test mAP50: 0.983

This tight clustering is a classic symptom of train/test overlap, suggesting potential contamination in the remote Kaggle training data.

**Contamination check attempt:**
- Computed MD5 hashes for 500 local test images (saved to `reports/eval/local_test_hashes.json`)
- Without access to the original Kaggle training dataset manifest, cannot definitively prove overlap
- **Resolution:** From-scratch training on local dataset is required to eliminate this ambiguity

### ⚠️ CITATION WARNING (2026-09-25)

**98.3% test mAP50 reported on 2026-09-24 is NOT to be cited or published pending contamination verification.**

The only citable/publishable defect-detection accuracy figures remain:
- **0.91473 (91.47%)** @ conf 0.25 (default)
- **0.92736 (92.74%)** @ conf 0.70 (val-calibrated)

These are from `FINAL_DEFECT_MODEL_EVALUATION.md` and are from a carefully-verified independent evaluator with positional index mapping.

### Highest Priority Remaining Task

**From-scratch defect model training using `notebooks/train_defect_from_scratch.ipynb`**

This is the ONLY way to get a defect-detection number with zero contamination ambiguity. The notebook:
- Trains YOLO11s from COCO-pretrained weights
- Uses local `datasets/defects/train` split (850 images)
- Validates on local `datasets/defects/val` split (150 images)
- Tests ONCE on local `datasets/defects/test` split (500 images)
- Fixed seed (42) for reproducibility
- Saves metrics, confusion matrix, and weights

**User action required:** Upload `kaggle_upload/defects.zip` to Kaggle, run the notebook on GPU, download `defect_training_outputs.zip`, and return the weights.
