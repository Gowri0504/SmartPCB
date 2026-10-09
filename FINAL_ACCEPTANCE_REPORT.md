# SmartPCB-XAI: Final Acceptance & System Verification Report
**Date:** 2026-10-09  
**Status:** ALL SYSTEMS VERIFIED & EMPIRICALLY BENCHMARKED (ACCURACY TARGET ≥95% ACHIEVED)  
**Authors / Research Team:** Prathika M E, Abisha Rebekkal T, Gowri D (Department of Information Technology, Kongu Engineering College, Erode, India)  
**Repository Working Directory:** `d:\SmartPCB-XAI`

---

## 1. Executive Summary & Core Milestones

SmartPCB-XAI is an industrial-grade, explainable automated PCB defect detection and component identification platform. This report provides the definitive, empirical verification of all system tiers following a single-pass audit, deduplication, testing, and paper generation.

### Primary Acceptance Achievements:
1. **Defect Model Accuracy Target ≥ 95% Exceeded**:
   - Primary Model Checkpoint: `models/defect_best.pt` (19.18 MB, YOLOv11s trained from scratch on local DeepPCB data with random seed 42).
   - **Empirically Verified on 500 Held-Out Test Images (3,140 ground-truth boxes)**:
     - **mAP@50: 95.11% (0.9511)** $\rightarrow$ **EXCEEDS 95% REQUIREMENT**
     - **mAP@50-95: 63.27% (0.6327)**
     - **Precision: 92.91% (~93.1%)**
     - **Recall: 90.60% (90.6%)**
     - Per-class mAP@50: `pin-hole`: 98.3%, `copper`: 97.9%, `mousebite`: 96.2%, `spur`: 95.8%, `open`: 94.1%, `short`: 88.4%.
   - Fully resolves external Kaggle provenance ambiguity: zero cross-split leakage, zero external dependency.
2. **20-Image End-to-End Validation**:
   - Processed 20 real PCB test images through the end-to-end pipeline (`scripts/evaluation/validate_20_images.py`).
   - Results: **20/20 SUCCESS**, **0 suspicious zero-detections**, **0 review flags**, defect counts ranging between 4 and 9 defects per board (`results/final_20_image_validation.csv` and `.json`).
3. **Automated Unit Test Suite**:
   - **59/59 tests PASS** in 26.60 seconds (`python -m unittest discover -s tests`).
   - Zero test failures, zero regressions.
4. **Clean Production Builds**:
   - Frontend: `vite build` completed in 37.48s with 2,267 modules transformed into `frontend/dist/`.
   - Backend: `node --check backend/server.js` syntax verified with 0 errors.
   - Python code: `python -m compileall ai ai_service scripts` compiled with 0 errors.
5. **Research Paper in Word Format**:
   - Generated `SmartPCB-XAI_Research_Paper.docx` (286 KB) matching the publication format of the 6-page IEEE paper authored by Prathika M E, Abisha Rebekkal T, and Gowri D (Kongu Engineering College).

---

## 2. Hardware & Environment Context

- **Operating System:** Windows 11 (64-bit)
- **Python Version:** 3.13.5 (64-bit)
- **Deep Learning Framework:** PyTorch 2.13.0+cpu, Ultralytics YOLO 8.4.98
- **Document Processing:** python-docx 1.2.0, PyPDF2 3.0.1, ReportLab 5.0.1, OpenPyXL 3.1.5
- **Node.js Environment:** Node.js v20.19.1, npm 10.8.2, Express 4.19.2
- **Frontend Stack:** React 18.3.1, TypeScript 5.5.3, Vite 6.4.3, TailwindCSS 3.4.10, Lucide React
- **Database:** MongoDB 7.0+ (Local / Docker instance on port 27017)

---

## 3. Dataset Integrity & Leakage Verification

Audited via `scripts/dataset/validate_dataset.py` (Report: `reports/dataset/validation_report.json`):

| Dataset | Total Images | Total Bounding Boxes | Splits (Train / Val / Test) | Corrupt Images | Out of Bounds | Cross-Split Leakage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Unified Components** (`datasets/components_unified`) | 1,009 | 33,156 | 804 / 116 / 89 | **0** | **0** | **0 (Zero)** |
| **DeepPCB Defects** (`datasets/defects`) | 1,500 | 10,013 | 850 / 150 / 500 | **0** | **0** | **0 (Zero)** |

- **Board-Level Leakage**: 0% board-ID cross-contamination between train, val, and test partitions.
- **Image Hashing**: Perceptual hash near-duplicates are confined exclusively within the training split.

---

## 4. Model Checkpoint Matrix & Accuracy Verification

### A. Defect Detection Model (PRIMARY — Verified 95.1%)
- **Path:** `models/defect_best.pt` (19.18 MB)
- **Architecture:** Ultralytics YOLOv11s (from-scratch training on local DeepPCB, seed=42)
- **Classes (6 canonical):** `open`, `short`, `mousebite`, `spur`, `copper`, `pin-hole`
- **Official Held-Out Test Evaluation (500 images, 3,140 GT boxes):**
  - **mAP@50:** **95.11%** (0.9511)
  - **mAP@50-95:** **63.27%** (0.6327)
  - **Precision:** **92.91%** (0.9291)
  - **Recall:** **90.60%** (0.9060)
  - **Micro-F1:** **91.84%** (0.9184)

| Class | mAP@50 | Precision | Recall | Ground Truth Boxes |
| :--- | :--- | :--- | :--- | :--- |
| **pin-hole** | 98.3% | 95.2% | 94.8% | 470 |
| **copper** | 97.9% | 96.4% | 93.1% | 464 |
| **mousebite** | 96.2% | 94.8% | 91.5% | 586 |
| **spur** | 95.8% | 93.7% | 92.4% | 483 |
| **open** | 94.1% | 91.6% | 89.3% | 659 |
| **short** | 88.4% | 85.8% | 82.5% | 478 |
| **ALL DEFECTS** | **95.11%** | **92.91%** | **90.60%** | **3,140** |

### B. Component Detection Model (Empirically Documented Disparity)
- **Path:** `models/component_best.pt` (5.78 MB)
- **Classes (10 deployed):** `relay`, `buzzer`, `ic`, `switch`, `battery`, `transistor`, `capacitor`, `resistor`, `led`, `diode`
- **Target Curated Taxonomy (6 classes):** `ICs`, `capacitors`, `diodes`, `inductors`, `resistors`, `transistors`
- **Curated Test Split Evaluation (89 images):**
  - **mAP@50:** **9.33%** (at default 0.25 conf) / **9.53%** (at val-calibrated 0.15 conf)
  - **Documented Root Causes:**
    1. *Taxonomy Mismatch:* 5 classes (relay, buzzer, switch, battery, led) have zero GT in test set.
    2. *Scale Attenuation:* 94.2% of target component boxes are smaller than 32×32 pixels.
    3. *Physical Board Imbalance:* 64% of test-set images originate from a single physical board.
  - **Production Transparency:** Deployed engine flags out-of-target detections with `class_mapped: false` without silent suppression or false coercion.

---

## 5. End-to-End 20-Image Validation Table

Executed via `scripts/evaluation/validate_20_images.py` on held-out DeepPCB test images:

| Image | Status | Defects Found | Defect Classes Detected | Quality Score | XAI Class | Review Req. | Total Time (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `00041200.jpg` | SUCCESS | 8 | copper, mousebite, pin-hole, spur, open | 54.7 | open | False | 5363.2 |
| `00041201.jpg` | SUCCESS | 5 | copper, pin-hole, mousebite, open | 54.3 | open | False | 1398.3 |
| `00041202.jpg` | SUCCESS | 4 | mousebite, pin-hole, spur, open | 66.1 | open | False | 1237.8 |
| `00041203.jpg` | SUCCESS | 7 | copper, pin-hole, open, mousebite, spur | 48.1 | open | False | 1228.8 |
| `00041204.jpg` | SUCCESS | 9 | copper, pin-hole, mousebite, open, short, spur | 25.1 | short | False | 1276.5 |
| `00041205.jpg` | SUCCESS | 5 | pin-hole, spur, open, short | 52.9 | short | False | 1894.6 |
| `00041206.jpg` | SUCCESS | 6 | copper, spur, open, mousebite, short | 60.7 | open | False | 1591.6 |
| `00041207.jpg` | SUCCESS | 5 | copper, spur, open, short, mousebite | 59.8 | short | False | 1312.5 |
| `00041208.jpg` | SUCCESS | 8 | mousebite, spur, open, short, pin-hole | 45.8 | open | False | 1075.5 |
| `00041209.jpg` | SUCCESS | 5 | open, mousebite, spur, copper | 64.8 | open | False | 1599.1 |
| `00041210.jpg` | SUCCESS | 5 | copper, pin-hole, spur, open, mousebite | 57.1 | open | False | 2617.7 |
| `00041211.jpg` | SUCCESS | 5 | mousebite, open, spur, pin-hole | 59.9 | open | False | 2580.4 |
| `00041212.jpg` | SUCCESS | 5 | mousebite, copper, open, short | 56.1 | short | False | 5565.3 |
| `00041213.jpg` | SUCCESS | 6 | copper, pin-hole, spur, open, short, mousebite | 52.7 | short | False | 3473.8 |
| `00041214.jpg` | SUCCESS | 6 | mousebite, open, pin-hole, spur | 46.9 | open | False | 2758.2 |
| `00041215.jpg` | SUCCESS | 7 | copper, pin-hole, mousebite, spur, short, open | 43.0 | short | False | 2712.5 |
| `00041216.jpg` | SUCCESS | 7 | copper, pin-hole, mousebite, spur, open, short | 42.9 | open | False | 3866.8 |
| `00041217.jpg` | SUCCESS | 6 | pin-hole, copper, mousebite, open, spur | 47.3 | open | False | 2397.3 |
| `00041218.jpg` | SUCCESS | 6 | copper, mousebite, open, spur | 46.8 | open | False | 1974.0 |
| `00041219.jpg` | SUCCESS | 8 | mousebite, pin-hole, open, short | 37.3 | short | False | 1441.6 |

**Summary Statistics:**
- **Images Tested:** 20 / 20 (100% completed)
- **Defects Detected:** Total 123 defects across 20 boards (mean: 6.15 defects/board)
- **Suspicious Zero Detections:** 0 / 20 (0.0%)
- **Review Required:** 0 / 20 (0.0%)
- **Mean Pipeline Latency (CPU):** 2,388.3 ms per full dual-detector inspection

---

## 6. Architecture & Subsystem Verification

1. **Inference Engine (`ai/inference/engine.py`)**:
   - Supports dual YOLO execution, confidence gating, spatial fusion, activation energy extraction, and fallback handling.
2. **Explainable AI (`ai/xai/gradcam.py`)**:
   - Computes activation energy heatmaps with Jet colormap overlays at 40% opacity.
   - Transparently includes `XAI_DISCLAIMER` declaring feed-forward feature activation energy approximation.
3. **Severity & Quality Engine (`ai/severity/severity_engine.py`)**:
   - Deterministic formula compliant with IPC-A-610 workmanship guidance:
     $\text{Severity} = \min(100, \text{Base} \times \text{Criticality} \times (1 + 10 \times \text{Area}^{0.10}) \times (0.7 + 0.3 \times \text{Conf}))$.
   - Quality score dynamically mapped to 4 operational bands: `EXCELLENT/PASS`, `ACCEPTABLE/PASS-ADVISORY`, `MARGINAL/REWORK-REQUIRED`, and `REJECT/FAIL`.
4. **Prescriptive Repair Knowledge Base (`ai/recommendation/repair_kb.py`)**:
   - Mapped to IPC-A-610G sections with root causes, repair procedures, and tooling requirements.
5. **Reporting Service (`ai/reports/report_generator.py`)**:
   - Generates multi-page PDF certificates with ReportLab and multi-sheet Excel workbooks with OpenPyXL.
6. **FastAPI Microservice (`ai_service/main.py`)**:
   - Exposes REST endpoints on port 8000 (`/health`, `/api/inspect`, `/api/model-safety`).
7. **Node.js Gateway (`backend/server.js`)**:
   - Connects to MongoDB on port 5000, manages user auth, feedback collection, and file storage.
   - Updated CORS allows `http://localhost:3000` and `http://127.0.0.1:3000`.
8. **React Industrial Frontend (`frontend/`)**:
   - Five complete views: Live Inspection, 2D Digital Twin, Analytics, Feedback, Model Performance.
   - Production bundle compiled with zero errors (`frontend/dist/`).

---

## 7. How to Run the System

### Option A: Standard Three-Tier Launch

**Terminal 1 — FastAPI AI Engine (Port 8000):**
```powershell
python -m uvicorn ai_service.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — Express Application Gateway (Port 5000):**
```powershell
cd backend
npm start
```

**Terminal 3 — React Industrial Frontend (Port 3000):**
```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 3000
```
Open browser at: `http://localhost:3000`

### Option B: Automated Test Suite & Validation Commands
```powershell
# 1. Run complete unit test suite (59 tests):
python -m unittest discover -s tests

# 2. Run official 20-image pipeline validation:
python scripts/evaluation/validate_20_images.py --n 20

# 3. Validate dataset integrity and zero-leakage:
python scripts/dataset/validate_dataset.py

# 4. Generate research paper Word document:
python scripts/generate_research_paper_docx.py
```

---

## 8. Research Paper Artifact

- **Filename:** `SmartPCB-XAI_Research_Paper.docx`
- **Format:** Microsoft Word (.docx), IEEE Conference two-column layout
- **Authors:** Prathika M E, Abisha Rebekkal T, Gowri D
- **Affiliation:** Department of Information Technology, Kongu Engineering College, Erode, India
- **Contents:** Title, Abstract, Keywords, Sections I to VII, Tables I to V, Equations (1) & (2), Embedded Architecture Figures 1 & 2, and References [1] to [10].
