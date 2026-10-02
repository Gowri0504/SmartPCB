# FINAL ACCEPTANCE REPORT — SmartPCB-XAI

**Date:** 2026-09-23
**Machine:** Windows 10, Python 3.13.5, PyTorch 2.13.0+cpu (CUDA unavailable), Node v24.18.0, MongoDB 127.0.0.1:27017
**Method:** every number below was produced by an executed command on this machine. Nothing is inherited from historical claims unless marked VERIFIED against a reproducible artifact. Unverified items are labeled **NOT VERIFIED**.

---

## 1. Test Suite

- **Result: 47/47 PASS** (`Ran 47 tests in 28.236s … OK`, exit 0), floor of 37 maintained.
- Coverage: FastAPI health & class contracts, severity engine, repair KB, XAI smoke, zero-detection contract, dataset validator, report generator, auth/backend, tiling, model safety.

## 2. Dataset Validation

- DeepPCB local split: train 850 / val 150 / test 500; test = official held-out split; all splits mutually disjoint (verified by filename-set comparison).
- Components dataset: 13 out-of-range class IDs documented, unfixed; 10 empty labels; 3 duplicate groups (train-internal).
- **Known calibration bias (disclosed):** local val ⊂ official DeepPCB train pool. Threshold calibration on val is optimistic vs. a fresh-distribution test set; headline test metrics use the official test split.

## 3. Model Safety

- `component_best.pt`: 10 raw classes; loads and runs; class_names_match = PARTIAL (guarded by `COMPONENT_CLASS_ALIASES` normalization).
- `defect_best.pt`: 6 classes; loads and runs; verified alignment mode = **FULL (positional)** via `DEFECT_MODEL_INDEX_TO_CANONICAL = {0:open, 1:short, 2:mousebite, 3:spur, 4:copper, 5:pin-hole}`.
- Geometric verification against DeepPCB GT: 921/923 matched pairs, mean IoU 0.899.
- The disproven `missing_hole → pin-hole` name pairing is **WITHDRAWN** (DEFECT_CLASS_SCHEMA.md §7).

## 4. Class Mapping

- Defect model: FULL positional contract, enforced in engine + asserted by tests/test_fastapi_health.py (6/6 pass).
- Component model: PARTIAL name-based alignment; 5 of 10 classes have zero GT in the local test split — honestly labeled LOW reliability (COMPONENT_CLASS_SCHEMA.md §6).

## 5. Frontend

- `tsc` typecheck: PASS. `vite build`: PASS (verified this session).
- Grep audit of `frontend/src` for stale claims (`missing_hole|97.6|98.2|16.1|PARTIAL|approximate`): **no matches**.
- `ModelPerformance.tsx` renders only real artifacts from `/api/model-evaluation` with "NOT VERIFIED" fallback; `DigitalTwin.tsx` holds no mock data and renders an explicit empty state.

## 6. Backend

- Express (5000) live: JWT auth (ADMIN self-register → 403 verified), bcryptjs, multer 25 MB image-only fileFilter with randomized filenames, CORS allowlist, generic server-error references, feedback-input validation, schema-agnostic `/api/model-evaluation`.
- `/api/model-evaluation`: **all 7 artifacts AVAILABLE** after fixing `EVAL_ARTIFACTS` paths (`per_class_metrics_*.csv` → actual `per_class_*.csv`) and regenerating stale pipeline artifacts. Served `full_pipeline_metrics.json` = 23 current records (4 REVIEW_REQUIRED), modified 2026-09-23T19:28 local.
- Analytics endpoint: descriptive counts only; withheld (REVIEW_REQUIRED) scores excluded from averages, never counted as 100.

## 7. Benchmark

- CPU-only, synthetic 640×640: mean total ≈ 2,508 ms (N=3) — `reports/benchmark/inference_benchmark.json`.
- Real 20-image validation: mean 4.07 s/image (min 2.57 s, max 10.87 s) — `results/final_20_image_validation.csv`.
- Historical "16.1 ms" figure: **NOT VERIFIED** (would require GPU + optimization).

## 8. End-to-End (real HTTP)

- Chain verified: Express upload → FastAPI inspect → quality score → XAI → PDF/Excel reports; PDF magic `%PDF-1.4`, XLSX magic `PK` verified.
- Live API result for DeepPCB `00041200.jpg`: 5 defects (copper, pin-hole, mousebite, spur, open), quality 52.2, FAIL — independently reproduced by the offline pipeline script (52.2), cross-validating API and engine.

## 9. XAI

- Grad-CAM path runs end-to-end; heatmap shape matches input; corrupt target box handled without crash (tests).
- Honesty label in force: `activation_energy_approximation` — NOT true gradient Grad-CAM++; disclaimer always returned and printed on reports. Faithfulness to model weights: **NOT VERIFIED**.

## 10. Reports

- PDF + Excel generate with measured numbers only; Limitations sheet lists UNVERIFIED items explicitly (historical mAP, 16.1 ms, GPU latency).
- Item 7.7 corrected this session: component PARTIAL / defect FULL-positional, with index map and geometric evidence.

## 11. Descriptive vs. Predictive Separation (STEP 28)

- **Descriptive** (this system): inspection counts, defect distributions, pass/rework/fail tallies, latency measurements, dataset statistics. No extrapolation.
- **Predictive** (the ML models): component/defect detectors and their mAP/precision/recall. The UI and reports never present descriptive analytics as predictive performance, and never present predictive outputs as verified ground truth — every model number traces to an executed eval run.

## 12. Protected-File Preservation

- Append-only files (`README.md`, `PROJECT_AUDIT.md`, `DATASET_REPORT.md`, `info.txt`, `FINAL_IMPLEMENTATION_AUDIT.md`, `DATA_LEAKAGE_AUDIT.md`, `DEFECT_CLASS_SCHEMA.md`, `COMPONENT_CLASS_SCHEMA.md`): every change this session was a tail-anchored append — the exact tail was read immediately before each Edit, the Edit matched only that anchor, and new content was inserted below it. No existing line was edited or deleted; stale content was superseded by dated "UPDATE / CORRECTION" sections below it, per policy.
- Code files legitimately edited: `tests/test_fastapi_health.py` (assertion fix), `ai/reports/report_generator.py` (7.7 disclaimer), `scripts/evaluation/evaluate_component_model.py` (None-score record bug), `backend/server.js` (EVAL_ARTIFACTS paths).

## 13. Files Created / Changed This Session

**Created:** `scripts/evaluation/validate_20_images.py`, `results/` (final_20_image_validation.csv/.json, annotated/*.jpg), `FINAL_DEFECT_MODEL_EVALUATION.md`, `FINAL_COMPONENT_MODEL_EVALUATION.md`, `DEFECT_CLASS_REPORT.md`, `COMPONENT_CLASS_REPORT.md`, `XAI_VALIDATION_REPORT.md`, `SEVERITY_SCORING.md`, `SECURITY_AUDIT.md`, `FINAL_ACCEPTANCE_REPORT.md` (this file), regenerated `metrics/*` artifacts, e2e/auth/eval logs in `metrics/`.

**Append-only updates:** README.md, PROJECT_AUDIT.md, FINAL_IMPLEMENTATION_AUDIT.md, DATA_LEAKAGE_AUDIT.md, DATASET_REPORT.md, DEFECT_CLASS_SCHEMA.md, COMPONENT_CLASS_SCHEMA.md, info.txt.

**Code edits:** tests/test_fastapi_health.py, ai/reports/report_generator.py, scripts/evaluation/evaluate_component_model.py, backend/server.js.

## 14. Known Limitations

1. Component detector genuinely weak: test mAP50 0.093346 (5/10 classes zero GT locally). Not hidden.
2. Historical mAP 97.6%/98.2% and 16.1 ms latency: **UNVERIFIED**, labeled as such everywhere.
3. XAI faithfulness (activation-energy proxy vs. true gradients): **NOT VERIFIED**.
4. CPU-only: no GPU measurements possible on this machine.
5. DeepPCB val ⊂ official train pool — calibration bias disclosed.
6. Security: dev-only JWT_SECRET fallback, no rate limiting, public /uploads route, no TLS, stateless JWT logout (all disclosed in SECURITY_AUDIT.md).
7. Training reproduction in-repo: NOT ACHIEVED (runs incomplete, no finished locally-trained model).
8. Checkpoint ↔ remote Kaggle training-data overlap: UNVERIFIABLE (remote data absent).

## 15. Reproduce Commands

```bash
# Tests
python -m unittest discover -s tests

# Defect evaluation (positional alignment)
python scripts/evaluation/evaluate_defect_model.py            # writes metrics/defect_metrics.json, metrics/per_class_defect.csv
python scripts/evaluation/evaluate_defect_model.py --from-raw # determinism re-score from metrics/raw/

# Component evaluation
python scripts/evaluation/evaluate_component_model.py component

# Full pipeline metrics (23 images)
python scripts/evaluation/evaluate_full_pipeline.py           # writes metrics/full_pipeline_metrics.json + pipeline_20_images_report.csv

# 20-image validation
python scripts/evaluation/validate_20_images.py

# E2E smoke (requires both servers + MongoDB)
curl -X POST http://localhost:5000/api/inspection/upload -F "image=@datasets/defects/test/images/00041200.jpg" -H "Authorization: Bearer <token>"

# Model evaluation artifacts endpoint
curl http://localhost:5000/api/model-evaluation

# Frontend
cd frontend && npm run build
```

**Bottom line:** every executed check passes with real, reproducible numbers; every unverifiable claim is labeled UNVERIFIED/NOT VERIFIED. No fabricated metrics exist in the repo as of this report.
