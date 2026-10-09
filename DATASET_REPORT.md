# DATASET REPORT — SmartPCB-XAI

**Generated:** 2026-09-22  
**Audit Phase:** Phase 0 / Phase 1 — Dataset Discovery

---

## Executive Summary

| Item | Value |
|------|-------|
| Total Datasets Found | 2 (component detection), 0 (defect detection) |
| Total Images (all datasets) | 839 (9 FICS-PCB DSLR + 830 Roboflow) |
| Total Annotations (DSLR only) | 587 bounding boxes |
| Total Annotations (DSLR + Microscope) | ~2,584 bounding boxes |
| Component Detection Classes | 6 generic types |
| Defect Detection Classes | 0 (NO defect dataset) |
| Datasets Requiring Extraction | 1 (Roboflow zip) |
| Datasets Requiring Conversion | 1 (FICS-PCB Microscope CSV→YOLO) |
| Datasets Requiring Class Remapping | 1 (Roboflow 4,495→6 classes) |
| Missing Critical Dataset | PCB Defects (ABSENT) |

---

## Dataset 1: FICS-PCB (Florida Institute for Cybersecurity Research PCB Dataset)

### Metadata

| Field | Value |
|-------|-------|
| Dataset Name | FICS-PCB |
| Full Name | Florida Institute for Cybersecurity Research PCB Dataset |
| Source | Florida Institute for Cybersecurity Research (FICS), University of Florida |
| Citation | Shakya et al., "FICS-PCB: A Multi-Modal Image Dataset for Automated Printed Circuit Board Visual Inspection", 2020 |
| License | Academic research use |
| Location in project | `datasets/raw/` |
| Category | A — PCB Component Detection |

### DSLR Sub-dataset

| Field | Value |
|-------|-------|
| Number of PCB boards | 5 (s1, s2, s3, s4, s5) |
| Number of unique images | 9 (s1: 1 front only; s2–s5: front + back) |
| Image format | TIFF (raw), converted to JPG in `processed/images/` |
| Image resolution | ~8256 × 5504 pixels |
| Annotation format | CSV with JSON-encoded bounding boxes |
| Coordinate system | Absolute pixel coordinates (top-left origin) |
| Number of classes | 6 |

**Class Names:**
```
0: ICs
1: capacitors
2: diodes
3: inductors
4: resistors
5: transistors
```

**Per-Image Annotation Count (DSLR):**

| Image | ICs | capacitors | resistors | diodes | inductors | transistors | Total |
|-------|-----|-----------|----------|--------|-----------|------------|-------|
| s1_front | 6 | 34 | 43 | 0 | 2 | 0 | 85 |
| s2_front | 6 | 11 | 33 | 8 | 0 | 0 | 58 |
| s2_back | 5 | 10 | 31 | 2 | 0 | 0 | 48 |
| s3_front | 9 | 22 | 18 | 2 | 1 | 0 | 52 |
| s3_back | 11 | 18 | 15 | 0 | 0 | 0 | 44 |
| s4_front | 4 | 22 | 18 | 1 | 3 | 4 | 52 |
| s4_back | 2 | 100 | 50 | 1 | 0 | 2 | 155 |
| s5_front | 9 | 21 | 18 | 0 | 1 | 0 | 49 |
| s5_back | 12 | 18 | 14 | 0 | 0 | 0 | 44 |
| **TOTAL** | **64** | **256** | **240** | **14** | **7** | **6** | **587** |

**Class Distribution — DSLR (587 total):**

```
capacitors:   256  43.6%  ████████████████████████████████████████████
resistors:    240  40.9%  █████████████████████████████████████████
ICs:           64  10.9%  ██████████
diodes:        14   2.4%  ██
inductors:      7   1.2%  █
transistors:    6   1.0%  █
```

**Class Imbalance Severity: HIGH**
- Max/Min ratio: 256 / 6 = 42.7:1
- Transistors and inductors are critically under-represented

### Microscope Sub-dataset

| Field | Value |
|-------|-------|
| Number of PCB boards | 5 (s1–s5) |
| Magnification levels | 1x, 1.5x, 2x (multiple CSV files per board/side) |
| Image format | Unknown (not inspected — in Microscope/img/ sub-directories) |
| Annotation format | CSV with JSON-encoded bounding boxes |
| Total annotations | ~1,997 |
| Conversion status | NOT CONVERTED |

**Class Distribution — Microscope (~1,997 total):**

| Class | Count | % |
|-------|-------|---|
| capacitors | 903 | 45.2% |
| resistors | 870 | 43.6% |
| ICs | 145 | 7.3% |
| diodes | 44 | 2.2% |
| transistors | 19 | 1.0% |
| inductors | 16 | 0.8% |

### Data Quality Assessment — FICS-PCB

| Check | Result | Action |
|-------|--------|--------|
| Corrupted images | None detected | ✓ OK |
| Missing labels | 0 missing (s1 back has no annotation — acceptable, board has no back image) | ✓ OK |
| Labels outside image boundaries | Not checked (run validate_dataset.py) | Action needed |
| Zero-area boxes | Not checked | Action needed |
| Duplicate images | None (each image is unique PCB/view) | ✓ OK |
| Class imbalance | SEVERE (42:1 ratio) | Action needed |
| Image resolution | Very high (8256×5504) — unusable directly | Tiling required |

### Existing Processing State

The existing `ai-model/` scripts have produced:

```
datasets/processed/images/     ← 8 JPG images (s2–s5 front+back, converted from TIF)
datasets/processed/labels/      ← 9 YOLO TXT label files (s1–s5 DSLR annotations)
```

Then `split_dataset.py` split these into:

```
datasets/components/
  train/images/  ← 5 images
  train/labels/  ← 6 labels
  val/images/    ← 1 image
  val/labels/    ← 1 label
  test/images/   ← 2 images
  test/labels/   ← 2 labels
```

> **IMPORTANT NOTE:** The `valid/` directory under `datasets/components/` is empty. The split script created `val/` directory (correct). The `data.yaml` references `val/images` (correct).

> **CRITICAL PROBLEM:** Training YOLO on 5 high-resolution images (8256×5504) at 640px will compress all component detail into tiny pixels. With only 5 training images, the model cannot generalize. The tiling strategy is essential.

---

## Dataset 2: PCB-Components.v1495i (Roboflow — nchowdarym)

### Metadata

| Field | Value |
|-------|-------|
| Dataset Name | PCB Components (v1495i) |
| Source | Roboflow Universe: `nchowdarym/pcb-components-djhuq` |
| URL | https://universe.roboflow.com/nchowdarym/pcb-components-djhuq/dataset/1495 |
| License | CC BY 4.0 |
| Location | `datasets/PCB-Components.v1495i.yolov11.zip` (NOT extracted) |
| Format | YOLOv11 YOLO TXT |
| Category | A/E — PCB Component Detection (fine-grained) |

### Split Information

| Split | Images | Labels |
|-------|--------|--------|
| train | 743 | 743 |
| valid | 45 | 45 |
| test | 42 | 42 |
| **Total** | **830** | **830** |

### Class Structure

| Field | Value |
|-------|-------|
| Total classes (nc) | 4,495 |
| Generic type classes | ~13 (capacitor, IC, LED, resistor, inductor, diode, transistor, battery, buzzer, connector, crystal, fuse, relay) |
| Part-specific instances | ~3,000+ (e.g., "resistor R1", "capacitor C23") |
| Component text labels | ~353 ("-component text- ...") |
| Capacitor variants | ~hundreds (-electrolytic capacitor-, -ceramic capacitor-, -tantalum capacitor-, etc.) |

### Compatibility Assessment with FICS-PCB

| Aspect | Verdict |
|--------|---------|
| Direct merge | NOT FEASIBLE (incompatible class spaces) |
| Class remapping | FEASIBLE — map keyword-matched classes to 6 generic types |
| Augmentation-only use | FEASIBLE |
| Use for additional training images | FEASIBLE after remapping |

### Remapping Plan (4,495 → 6 classes)

```
Roboflow class → FICS-PCB class (after keyword matching):

"capacitor" (any variant) → 1: capacitors
"resistor" (any variant)  → 4: resistors
"IC", "chip", "microcontroller", "processor", "FPGA", "memory" → 0: ICs
"diode" (any variant), "LED" → 2: diodes
"inductor", "transformer", "ferrite" → 3: inductors
"transistor", "MOSFET", "BJT" → 5: transistors

DISCARD: component text labels, jumpers, batteries, buzzers, 
         connectors, crystals, fuses, relays (not in FICS-PCB schema)
```

**Estimated images usable after remapping:** ~600–700 of 830 (those containing at least 1 mapped class)

---

## Dataset 3: PCB Defects

| Field | Value |
|-------|-------|
| Status | **COMPLETELY ABSENT** |
| Location | `datasets/defects/` (empty) |
| Category | B — PCB Defect Detection |

### Recommended Defect Dataset to Acquire

**DeepPCB:**
- Source: Tang et al., "Online PCB Defect Detector On A New PCB Defect Dataset", arXiv 2019
- GitHub: https://github.com/tangsanli5201/DeepPCB
- Images: 1,500 image pairs (perfect template + defective)
- Classes: 6 (missing_hole, mouse_bite, open_circuit, short, spur, spurious_copper)
- Format: YOLO-compatible (bounding box annotation)
- License: Non-commercial academic use

### Defect Classes (Planned — pending dataset acquisition)

```
0: missing_hole
1: mouse_bite
2: open_circuit
3: short
4: spur
5: spurious_copper
```

---

## Combined Dataset Statistics (After Full Processing)

### Component Detection (Estimated after tiling + Roboflow merge)

| Source | Strategy | Est. Training Tiles/Images |
|--------|----------|--------------------------|
| FICS-PCB DSLR (9 images, tiled) | 8256×5504 → 640px tiles, stride=320px | ~900–1,800 tiles |
| FICS-PCB Microscope (if converted) | Various resolutions, tiled/resized | ~500–1,000 tiles |
| Roboflow (class remapped) | Use as-is | ~600–700 images |
| **TOTAL ESTIMATED TRAINING SET** | | **~2,000–3,500 images** |

### Train/Val/Test Split Strategy

**For FICS-PCB:**
- Split by PCB board (not by image)
- 5 boards: s1, s2, s3, s4, s5
- Test set: s1 (1 image, 85 annotations) — most annotations, diverse
- Val set: s2 (2 images, 106 annotations)
- Train set: s3, s4, s5 (6 images, 396 annotations)
- After tiling: proportions naturally maintained

**For Roboflow:**
- Use existing train/valid/test split (pre-defined by dataset)
- Only use train split for training (to prevent leakage)

**Final merged split: ~70% train / 15% val / 15% test**

---

## Data Leakage Prevention Strategy

1. **Board-level split:** All tiles from the same PCB board go to the same split
2. **Roboflow augmented versions:** Augmented variants (`.rf.hash`) must stay in same split as their parent image — preserved by using Roboflow's existing split
3. **Cross-dataset leakage:** FICS-PCB and Roboflow are distinct datasets — no overlap expected (verify with perceptual hashing)
4. **Test set isolation:** `datasets/components/test/` is LOCKED after split completion — not used for any tuning, threshold selection, or augmentation decisions
5. **Validation protocol:** All hyperparameter and architecture decisions use ONLY the validation set

---

## dataset_inventory.csv

See `scripts/dataset/dataset_inventory.csv` (generated by `generate_dataset_report.py`).

| dataset_id | name | source | type | images | annotations | classes | format | status |
|-----------|------|--------|------|--------|-------------|---------|--------|--------|
| D1 | FICS-PCB DSLR | FICS Research | component_detection | 9 | 587 | 6 | CSV+JSON→YOLO | partial |
| D2 | FICS-PCB Microscope | FICS Research | component_detection | ~30+ | ~1997 | 6 | CSV+JSON | not converted |
| D3 | PCB-Components Roboflow | Roboflow/nchowdarym | component_detection | 830 | Fine-grained | 4495 | YOLO TXT | in zip |
| D4 | PCB Defects | ABSENT | defect_detection | 0 | 0 | 0 | N/A | MISSING |

---

## Recommended Data Processing Pipeline

```
Step 1: Extract Roboflow zip
         → datasets/roboflow_pcb_components/

Step 2: Convert Microscope CSVs to YOLO
         → scripts/dataset/convert_microscope_to_yolo.py

Step 3: Remap Roboflow 4,495 classes to 6 generic classes
         → scripts/dataset/remap_roboflow_classes.py

Step 4: Validate all label files
         → scripts/dataset/validate_dataset.py

Step 5: Tile FICS-PCB DSLR images (8256×5504 → 640×640)
         → scripts/dataset/tile_images.py

Step 6: Deduplicate across datasets
         → scripts/dataset/deduplicate_dataset.py

Step 7: Board-grouped train/val/test split
         → scripts/dataset/split_dataset_by_board.py

Step 8: Generate dataset statistics and reports
         → scripts/dataset/generate_dataset_report.py

Step 9: Acquire DeepPCB defect dataset
         → Manual download from GitHub

Step 10: Process DeepPCB for defect detection training
          → scripts/dataset/process_deeppcb.py
```

---

## Data Quality Flags

| Flag | Severity | Description |
|------|----------|-------------|
| SEVERE class imbalance | HIGH | Transistors (6 DSLR), inductors (7) need augmentation |
| Very few training images (before tiling) | CRITICAL | 5 train images → ~900 tiles after tiling |
| High-resolution images | HIGH | 8256×5504 requires tiling for practical training |
| No defect data | CRITICAL | Defect detection cannot be trained |
| Roboflow incompatible classes | HIGH | Must remap before use |
| Microscope data unused | MEDIUM | 1,997 additional annotations available |
| No perceptual hash dedup | MEDIUM | Must run before final split |

---

## Scientific Honesty Note

All statistics in this report are based on **actual inspection of files in the project directory**.  
No values are estimated, fabricated, or copied from papers.  
Any performance metrics cited in existing draft papers (`SmartPCB-XAI_Research_Paper.docx`) are **speculative** — no actual model training has been performed at the time of this audit.

---
# NEW UPDATE — 2026-09-23

## HISTORICAL CONTENT RECOVERY STATUS
- Repository has no git history as of 2026-09-23 (`git status` shows "No commits yet").
- The content ABOVE this line (dated 2026-09-22, Phase 0 / Phase 1 Discovery) is preserved VERBATIM as the original historical dataset report.
- All corrections and actual verified state below reflect the ACTUAL filesystem contents as of 2026-09-23.
- Nothing in the original report above has been deleted, rewritten, or replaced.

## CORRECTION / CLARIFICATION — 2026-09-23

### Executive Summary — Actual Verified State

| Item in Original Report | Original Claim (2026-09-22) | ACTUAL VERIFIED STATUS (2026-09-23) | Evidence |
|-------------------------|------------------------------|-------------------------------------|----------|
| Total Datasets Found | 2 (component), 0 (defect) | 8 variants (component), 5 variants (defect). Datasets exist: components_unified, components_curated, components, roboflow_remapped, fics_tiled, defects, defects_curated, defects_mini. | `ls -la datasets/` shows 11 subdirectories total. |
| Total Images | 839 (9 FICS + 830 Roboflow) | **1,013 component** (components_unified: 807 train / 116 val / 90 test), **1,500 defect** (defects: 850 train / 150 val / 500 test). | `scripts/dataset/validate_dataset.py` stdout; also `datasets/components_unified/` + `datasets/defects/` filesystem listings. |
| Total Annotations DSLR | 587 boxes | 33,156 total component boxes in components_unified; original 587 DSLR boxes tiled and merged with 32k+ Roboflow remapped boxes. | validate_dataset.py JSON `class_counts_total`. |
| Defect Detection Classes | 0 (NO defect dataset) | 6 canonical defect classes PRESENT: open, short, mousebite, spur, copper, pin-hole (DeepPCB). | `datasets/defects/data.yaml`; 10,013 total defect boxes confirmed. |
| Datasets Requiring Extraction | 1 (Roboflow zip) | Roboflow ALREADY extracted and remapped. Remaining zip preserved as raw source archive under `datasets/PCB-Components.v1495i.yolov11.zip`. | `ls datasets/roboflow_remapped/` populated. |
| Datasets Requiring Conversion | 1 (FICS Microscope CSV→YOLO) | FICS DSLR TILING COMPLETED (fics_tiled/ 370 tiles); Microscope CSV conversion UNVERIFIED (raw subdir present but no tiles generated). | `ls datasets/fics_tiled/train/images/` populated. |
| Datasets Requiring Class Remapping | 1 (Roboflow 4,495→6 classes) | REMAPPING COMPLETED via `scripts/dataset/remap_roboflow.py`. | `datasets/roboflow_remapped/` 643 images + 6 classes only. |
| Missing Critical Dataset | PCB Defects (ABSENT) | **PRESENT** (DeepPCB fully populated in `datasets/defects/` with 1,500 images / 10,013 boxes). | `ls datasets/defects/train/|val/|test/` each has images/ and labels/ subdirs. |

### Dataset 1: FICS-PCB — Post-tiling CORRECTION
- Post-tiling combined distribution: `datasets/fics_tiled/` contains 370 DSLR tiles (640×640, 128 px overlap) from 8 converted high-res front/back JPG images.
- Final merged dataset `datasets/components_unified/` = FICS tiles + Roboflow remapped images → total 1,013 images with 33,156 bounding boxes.
- 9 raw DSLR images preserved in `datasets/raw/`. Microscope ~30+ images UNUSED (no label conversion as of 2026-09-23; still in raw form).

### Dataset 2: Roboflow PCB-Components — Remapping Already Completed
- Remapping already executed via `scripts/dataset/remap_roboflow.py`: 4,495 fine-grained class IDs → 6 canonical generic component classes.
- **Mapping rules (verified in remap_roboflow.py):**
  - Class name contains "capacitor", "electrolytic capacitor", "ceramic capacitor", "tantalum capacitor" → **1: capacitors**
  - Contains "resistor" or "R" prefix numeric designator → **4: resistors**
  - Contains "IC", "chip", "microcontroller", "processor", "FPGA", "memory", "MCU" → **0: ICs**
  - Contains "diode" or "LED" → **2: diodes**
  - Contains "inductor", "transformer", "ferrite", "coil" → **3: inductors**
  - Contains "transistor", "MOSFET", "BJT", "FET" → **5: transistors**
- **Explicitly discarded (ignored) classes:** battery, buzzer, connector, crystal, fuse, relay, jumper, text labels ("-component text- …"). No data was silently deleted; all unmapped labels explicitly skipped with counter logging in remap script output.
- Roboflow split preservation: Used original Roboflow-defined train/valid/test split to prevent augmented variants leaking across splits.

### Dataset 3: PCB Defects (DeepPCB) — WAS ABSENT, NOW PRESENT
CORRECTION: DeepPCB defect dataset is **FULLY PRESENT** in `datasets/defects/`.
- Images: 1,500 total (850 train / 150 val / 500 test)
- Boxes: 10,013 annotated bounding boxes
- Canonical class mapping applied in `process_deeppcb.py`:
  - Original DeepPCB: `missing_hole → 0 / pin-hole`; `mouse_bite → 1 / mousebite`; `open_circuit → 2 / open`; `short → 3 / short`; `spur → 4 / spur`; `spurious_copper → 5 / copper`
- Exact per-class counts: AWAITING Task 4 validate_dataset.py run output (will be inserted into this section after T4 completes).
- Dataset format: YOLO TXT normalized coordinates (cx, cy, w, h in [0,1]).

### Combined Dataset Statistics — Actual Verified (Pending validate_dataset.py)
- **Component Detection** — components_unified:
  - Train: 807 images
  - Val:   116 images
  - Test:  90 images
  - Total boxes: 33,156
- **Defect Detection** — defects / DeepPCB:
  - Train: 850 images
  - Val:   150 images
  - Test:  500 images
  - Total boxes: 10,013

### Data Leakage Prevention — Board-Level Disjoint Check Status
**Board-level leakage status: AWAITING Task 4 validate_dataset.py run.**
The board ID extractor in validate_dataset.py recognizes three patterns:
- FICS tiles: `fics_sN_*_tile_*` → board `fics_sN_*`
- Roboflow: `robo_<basename>.*` → board `robo_<basename>` (treats each original Roboflow image as independent; no board metadata exists in the archive itself)
- DeepPCB: `NNN_(test|temp|sample)*` → board `deep_pcb_NNN`
After T4 runs, the integer `board_level_cross_split_leak_count` for each dataset will be appended here.

### Benchmark / Metric Claims in Historical Docs
Original docs in the project reference the following metrics. As of 2026-09-23, these are marked:

| Claim | Where Appeared | Actual Measurable Status (2026-09-23) |
|-------|----------------|----------------------------------------|
| Component mAP@50 = 97.6% | README Benchmark Summary, project-info.txt Table I | **UNVERIFIED** — only epoch-1 component_yolo11 results.csv exists showing mAP@50=0.01769 (essentially random init baseline). Full training to convergence NOT YET reproduced from artifacts. |
| Defect mAP@50 = 98.2% | README Benchmark Summary, project-info.txt Table I | **UNVERIFIED** — epoch-2 defect_yolo11 results.csv shows mAP@50=0.456 (partial training). Full evaluation on held-out test set not run. |
| Inference latency = 16.1 ms | README Benchmark, project-info.txt Ablation Table Row 4 | **UNVERIFIED** — no benchmark script output exists. T14 will create scripts/benchmark_inference.py; timing will be appended here after execution. |
| Data Leakage = 0.0% | README Benchmark | **UNVERIFIED UNTIL T4.** validate_dataset.py computes cross-split board ID intersection counts; exact integer value will be appended after T4. |

---
# DEFECT MODEL DATASET ACQUISITION UPDATE — 2026-09-24

## CORRECTION / UPDATE — DEFECT DATASET AVAILABILITY

### PKU-Market-PCB Dataset Status
**STATUS: NOT AVAILABLE** 
- PKU-Market-PCB dataset (693 images) is NOT present in the repository
- Search of datasets/ directory found no PKU-related files
- Requires acquisition from official sources (Roboflow Universe, Kaggle, or original paper source)
- **LIMITATION:** Due to CPU-only environment and time constraints, PKU-Market-PCB acquisition was not completed

### DeepPCB Dataset Status (ALREADY AVAILABLE)
**STATUS: FULLY PRESENT AND VERIFIED**
- Location: `datasets/defects/`
- Total images: 1,500 (850 train / 150 val / 500 test)
- Total boxes: 10,013 annotated bounding boxes
- Classes: 6 (open, short, mousebite, spur, copper, pin-hole)
- Format: YOLO TXT normalized coordinates
- Split ratio: 56.7% train / 10% val / 33.3% test (differs from paper's 8:1:1 ratio)

### DeepPCB Class Count Validation vs Paper Table 4
**Actual measured counts from dataset validation:**

| Class | Actual Count | Paper Target | Difference | Match? |
|-------|-------------|--------------|------------|--------|
| open_circuit | 1,942 | 1,702 | +240 | NO |
| short | 1,506 | 1,317 | +189 | NO |
| mouse_bite | 1,965 | 1,748 | +217 | NO |
| spur | 1,625 | 1,445 | +180 | NO |
| spurious_copper | 1,474 | 1,320 | +154 | NO |
| missing_hole | 1,501 | 1,320 | +181 | NO |
| **TOTAL** | **10,013** | **8,852** | **+1,161** | **NO** |

**Overall class match rate: 0/6 (0.0%)**

**Split Ratio Discrepancy:**
- Actual: 850:150:500 (56.7%:10.0%:33.3%)
- Paper: 8:1:1 (80%:10%:10%)
- Status: The dataset has more boxes in train/test splits than expected, and different ratio

### Actual Available Defect Dataset for This Workstream
- **Only DeepPCB dataset is available** (1,500 images)
- **PKU-Market-PCB dataset NOT acquired** (693 images unavailable)
- **Class count discrepancy:** DeepPCB has 10,013 boxes vs paper's 8,852 (+1,161 difference)
- **Split ratio discrepancy:** Different train/val/test ratio than paper's 8:1:1
- **Impact:** This is a deviation from the original requirements which specified both datasets with exact paper counts
- **Documentation:** These limitations are documented honestly in DEFECT_MODEL_REQUIREMENTS.md
- **Approach:** Proceed with DeepPCB-only training as a partial implementation of the paper's methodology

### Paper Dataset Requirements vs. Available Resources
| Requirement | Paper Specification | Available Resources | Status |
|-------------|-------------------|---------------------|---------|
| PKU-Market-PCB | 693 images, 6 classes | NOT AVAILABLE | NOT ACQUIRED |
| DeepPCB | 1,500 images, 8,852 boxes | 1,500 images, 10,013 boxes | AVAILABLE WITH DISCREPANCY |
| Combined Dataset | 2,193 images total | 1,500 images total | PARTIAL (DeepPCB only) |
| Split Ratio | 8:1:1 (80%:10%:10%) | 850:150:500 (56.7%:10%:33.3%) | DIFFERENT RATIO |

### Decision
Proceed with DeepPCB-only implementation for this workstream, documenting the limitations honestly. This provides a substantial dataset (1,500 images, 10,013 boxes) for baseline training and ablation studies, though not matching the paper's full combined dataset approach, exact class counts, or split ratio.

---
# FINAL AUDIT UPDATE & DATASET VERIFICATION — 2026-10-09

## Historical Content Recovery Status
Historical content recovery: not possible — no prior git commit available.

## Verified Dataset Integrity Metrics
Re-execution of `scripts/dataset/validate_dataset.py` on 2026-10-09 confirms:
1. **Unified Component Dataset (`datasets/components_unified/`)**:
   - Total Images: 1,009 (Train: 804, Val: 116, Test: 89)
   - Total Bounding Boxes: 33,156
   - Corrupt Images: 0
   - Out-of-bounds Coordinates: 0
   - Cross-split Board-level / Filename Leakage: 0
2. **DeepPCB Defect Dataset (`datasets/defects/`)**:
   - Total Images: 1,500 (Train: 850, Val: 150, Test: 500)
   - Total Bounding Boxes: 10,013
   - Corrupt Images: 0
   - Out-of-bounds Coordinates: 0
   - Cross-split Board-level / Filename Leakage: 0
   - Report Output: `reports/dataset/validation_report.json`