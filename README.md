# SmartPCB-XAI

**SmartPCB-XAI: An Explainable AI-Based Intelligent PCB Inspection and Manufacturing Analytics Platform for Industry 4.0**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Node.js 20+](https://img.shields.io/badge/Node.js-20%2B-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135%2B-teal.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3-cyan.svg)](https://react.dev/)
[![YOLOv11](https://img.shields.io/badge/YOLO-v11s-purple.svg)](https://docs.ultralytics.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Overview
**SmartPCB-XAI** is a research-grade, explainable Automated Optical Inspection (AOI) and manufacturing analytics platform. It combines dual YOLOv11s detectors, CLAHE trace contrast enhancement, authentic Grad-CAM++ feature attribution, deterministic IPC-A-610 defect severity scoring, an interactive 2D Digital Twin, and automated compliance reporting.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 20+ & npm
- MongoDB running locally on port 27017

### 1. Install Dependencies
```bash
# Python dependencies
pip install -r requirements.txt

# Backend dependencies
cd backend && npm install && cd ..

# Frontend dependencies
cd frontend && npm install && cd ..
```

### 2. Run the Services
Open 3 separate terminals:

**Terminal 1 — FastAPI AI Inference Engine:**
```bash
python -m uvicorn ai_service.main:app --port 8000 --reload
```

**Terminal 2 — Express Application Backend:**
```bash
cd backend
npm start
```

**Terminal 3 — React Industrial Dashboard:**
```bash
cd frontend
npm run dev
```

Open your browser at **`http://localhost:3000`**.

---

## 🧪 Automated Testing & Verification
Execute the test suite to verify datasets, inference engines, scoring, and PDF/Excel generation:
```bash
# Run unit & integration test suites
python -m unittest discover -s tests -p "test_*.py"

# Evaluate models on held-out test splits
python evaluate.py

# Verify frontend production build
npm run build --prefix frontend
```

---

## 📂 Project Architecture
```
SmartPCB-XAI/
├── ai/                      # Core AI & Analytical Modules
│   ├── inference/           # Unified dual-head inference pipeline
│   ├── recommendation/      # IPC-A-610 prescriptive repair knowledge base
│   ├── reports/             # PDF certificate & Excel audit generator
│   ├── severity/            # Deterministic defect severity & quality scoring
│   ├── training/            # YOLOv11 training pipelines
│   └── xai/                 # Authentic Grad-CAM++ feature attribution hooks
├── ai_service/              # FastAPI REST microservice (port 8000)
├── backend/                 # Node.js Express server + MongoDB models (port 5000)
├── datasets/                # Standardized datasets
│   ├── components_unified/  # 1,013 images, 33,156 boxes (FICS + Roboflow)
│   ├── defects/             # 1,500 pairs, 10,013 boxes (DeepPCB benchmark)
│   └── raw/                 # Original FICS-PCB DSLR & Microscope data
├── frontend/                # React 18 + TypeScript + TailwindCSS dashboard (port 3000)
│   └── src/components/      # LiveInspection, DigitalTwin, Analytics, Feedback, Benchmarks
├── models/                  # Trained YOLOv11 model checkpoints
├── reports/                 # Dataset charts, evaluations, and generated PDF reports
├── scripts/dataset/         # Tiling, remapping, and validation scripts
├── tests/                   # Automated unittest suite
├── aboutproject-info.txt    # Technical companion guide for conference defense
├── DATASET_REPORT.md        # Full dataset inventory & provenance report
├── PROJECT_AUDIT.md         # Repository architectural audit
├── references.bib           # IEEE BibTeX references
└── SmartPCB-XAI_Research_Paper.md # Complete IEEE conference paper draft
```

---

## 📊 Benchmark Summary
- **Component Detection mAP@50**: **97.6%** (Held-out FICS-PCB `s1` test partition)
- **Defect Detection mAP@50**: **98.2%** (500 isolated DeepPCB test boards)
- **Inference Latency**: **16.1 ms** (Multi-threaded CPU execution)
- **Data Leakage**: **0.0%** (Board-level disjoint isolation)

---

## 📖 Citation
If you use SmartPCB-XAI in academic research, please cite:
```bibtex
@article{smartpcbxai2026,
  title={SmartPCB-XAI: An Explainable AI-Based Intelligent PCB Inspection and Manufacturing Analytics Platform for Industry 4.0},
  author={Raj, Dharma & Research Group},
  year={2026}
}
```

---
# NEW UPDATE — 2026-09-23

## HISTORICAL CONTENT RECOVERY STATUS
- Repository has no git history as of 2026-09-23. All content above this line is preserved VERBATIM as the original 2026-09-22 project README.
- The corrections below reflect verified, measured filesystem state rather than historical claims.
- Nothing in the original README above has been deleted, rewritten, or replaced.

## CORRECTION / CLARIFICATION — 2026-09-23

### Benchmark Section — Honest Status
Original Section 📊 Benchmark Summary (lines 108–113 above) contains the following numerical claims. As of 2026-09-23, their status is:

| Claim (as written above) | Verifiable From Repo Artifacts? | Actual Verified Status |
|---------------------------|---------------------------------|------------------------|
| Component Detection mAP@50 = **97.6%** | NO — only `experiments/component_yolo11/training_logs/results.csv` epoch-1 data found showing mAP@50=0.01769 (essentially random init). No complete evaluation output on held-out `s1` test partition. | **UNVERIFIED — aspirational target only.** Treat as an aspirational benchmark until `python evaluate.py` is actually executed with the test split locked. |
| Defect Detection mAP@50 = **98.2%** | NO — `experiments/defect_yolo11/training_logs/results.csv` shows epoch-2 mAP@50=0.456 (interrupted training). No full evaluation on 500 isolated DeepPCB test boards. | **UNVERIFIED — aspirational target only.** |
| Inference Latency = **16.1 ms** | NO — no `scripts/benchmark_inference.py` existed before this audit; no timing JSON log files. | **UNVERIFIED.** Will be measured by T14 and appended below. |
| Data Leakage = **0.0%** | PENDING — validate_dataset.py computes board-level cross-split overlap counts; integers not yet captured. | **UNVERIFIED UNTIL T4 runs.** |

### Overview Line — Honest Labeling Corrections
Original Overview (line 15 above) states:
> "Combines dual YOLOv11s detectors, CLAHE trace contrast enhancement, **authentic Grad-CAM++ feature attribution**, deterministic **IPC-A-610 defect severity scoring**, …"

CORRECTION / CLARIFICATION — 2026-09-23:
1. **XAI/Grad-CAM++**: The current implementation in `ai/xai/gradcam.py` is **honestly labeled as an approximation** (`attribution_method = "activation_energy_approximation"`). It computes mean(|activations|) on the bottleneck layer under `torch.no_grad()` — it does **NOT** compute true Grad-CAM++ alpha-weighted higher-order gradient weights. A DISCLAIMER is emitted in every engine output, every XAI API response, and every report. If true Grad-CAM++ cannot be implemented reliably for Ultralytics YOLOv11 due to output-head fusion complexity, it will remain explicitly APPROXIMATION-labeled.
2. **Severity Scoring**: The formula in `ai/severity/severity_engine.py` is explicitly titled **"SmartPCB-XAI project-defined severity score"** in its module docstring ×2 locations and in the formula section. **It is NOT an IPC-A-610 standard score** — IPC-A-610 is used as workmanship guidance for accept/reject criteria, but the 0–100 numeric value and base-weight table are project definitions, not official IPC math. The phrase "IPC-A-610 defect severity scoring" in line 15 should be read as: *severity scoring informed by IPC-A-610 workmanship guidance, with a project-defined numeric formula.*

---
## Verified vs Unverified Claims

| Claim | Status | Supporting Evidence | Notes |
|-------|--------|---------------------|-------|
| Python 3.11+ environment works | VERIFIED | `pip list` shows ultralytics 8.3.x, torch 2.5.x installed; 16/16 tests PASS. | Entry environment TraeAI-7 terminal |
| Node.js 20+ available | VERIFIED | `node --version` in terminal; `backend/package.json` installs succeed. | - |
| FastAPI /health endpoint returns real status | VERIFIED | `tests/test_api.py` TestClient ×4 health cases PASS. | Returns actual `torch.cuda.is_available()`, engine.device, and model load booleans. |
| Component checkpoints load via YOLO() | VERIFIED | 4 checkpoints exist and all load without exception. `models/component_best.pt` 94.9MB, `models/defect_best.pt` 94.9MB. | `ls -la models/` |
| Defect checkpoints load via YOLO() | VERIFIED | Same as above. | - |
| Dual YOLO inference produces detections | VERIFIED | `tests/test_inference_engine.py` ×2 cases (synthetic + real image) PASS with bbox outputs. | - |
| XAI produces an overlay image | VERIFIED | `tests/test_xai.py` ×3 smoke tests PASS. Attribution method explicitly = `activation_energy_approximation`. | NOT true gradient Grad-CAM++. |
| Severity engine produces deterministic scores | VERIFIED | `tests/test_severity_engine.py` severity ×5 + quality ×1 = PASS. | Project-defined score, not IPC math. |
| Quality score 0–100 clamp works | VERIFIED | Same test file. Formula: `overall = clamp(100 - Σ(severity/5 × conf), 0, 100) + component_integrity`. | - |
| Repair KB returns structured data | VERIFIED | `tests/test_severity_engine.py` repair_kb ×1 PASS. | Rule-Based engine, not trained AI. |
| PDF generator produces non-empty file | VERIFIED | `tests/test_reports.py` PDF ×1 PASS. | 6 sections output. |
| Excel generator produces non-empty file | VERIFIED | `tests/test_reports.py` Excel ×1 PASS. | 4 sheets output. |
| Frontend production build succeeds | UNVERIFIED in current audit session; dist/ has stale artifacts. | Will be re-run in T13. | - |
| Backend server syntax is valid | UNVERIFIED. | Will be checked in T12 with `node --check`. | - |
| Component mAP@50 97.6% | UNVERIFIED | No evaluate.py output. | Treat as aspirational. |
| Defect mAP@50 98.2% | UNVERIFIED | No evaluate.py output. | Treat as aspirational. |
| 16.1 ms end-to-end inference | UNVERIFIED | Will be measured in T14. | - |
| 0.0% board-level data leakage | UNVERIFIED UNTIL T4. | validate_dataset.py will report integers. | - |
| 9/9 tests passing (historical claim) | FAILED / SUPERSEDED | Actual count is **16/16 PASS** on 2026-09-23 with the expanded test suite. | Historical claim was a stale baseline. |

---
## Scientific Honesty Labeling Summary — Active Labels In-Force

| Module | Label In Force | Where Verified |
|--------|----------------|----------------|
| XAI Heatmaps | `activation_energy_approximation` — NOT true gradient Grad-CAM++. DISCLAIMER always returned. | `ai/config.py` XAI_ATTRIBUTION_METHOD, engine.py inspect() return xai.disclaimer, PDF/Excel Limitations page. |
| Defect Severity (0–100) | "SmartPCB-XAI project-defined severity score". Uses IPC-A-610 for workmanship guidance only, NOT for numeric formula. | `ai/severity/severity_engine.py` docstring ×2, formula comment, reports. |
| Root-Cause / Repair Engine | "Rule-Based Root-Cause Recommendation Engine". Recommendations are framed as `possible cause`, not proven causality. | `ai/recommendation/repair_kb.py` module docstring header (added T9 2026-09-23). |
| PCB Quality Score | Deterministic weighted formula. Documented inputs / weights / normalization in severity_engine module doc. | Same module. |
| Model mAP Numbers | Marked "UNVERIFIED" in this table. "Evaluation pending" until evaluate.py actually runs. | PROJECT_AUDIT.md, DATASET_REPORT.md. |
| Data Leakage | "UNVERIFIED UNTIL T4" until validate_dataset.py board-ID integers captured. | DATASET_REPORT.md, above. |

## FINAL CONTINUATION PASS UPDATE — 2026-09-23

The "Model mAP Numbers" and "Data Leakage" rows above are superseded by same-day measured results (see FINAL_DEFECT_MODEL_EVALUATION.md, FINAL_COMPONENT_MODEL_EVALUATION.md, DATASET_REPORT.md UPDATE, DATA_LEAKAGE_AUDIT.md UPDATE):

- Full unittest suite: **47/47 PASS** (`python -m unittest discover -s tests`).
- Defect model (FULL, positional alignment; index map 0=open, 1=short, 2=mousebite, 3=spur, 4=copper, 5=pin-hole): test **mAP50 = 0.91473** @default 0.25; **0.927359** @val-calibrated 0.70 (mAP50-95 0.738340, micro-F1 0.959630). Geometric verification: 921/923 matched GT pairs, mean IoU 0.899.
- Component model (PARTIAL, name-based alignment): test **mAP50 = 0.093346** @0.25 — genuinely weak detector, labeled LOW reliability. 5 of 10 classes have zero GT in the local test split.
- Pipeline latency on this CPU-only machine: mean ≈ 4.07 s/image (20-image validation; min 2.57 s, max 10.87 s). The historical "16.1 ms" figure remains **UNVERIFIED**.
- Data leakage: board-ID/filename cross-split overlap = 0 for both datasets; pHash near-duplicate groups are intra-split only. Known calibration bias: local val ⊂ official DeepPCB train pool (disclosed in DATASET_REPORT.md).
# SmartPCB
