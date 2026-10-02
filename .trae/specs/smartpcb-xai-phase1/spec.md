# SmartPCB-XAI Phase 1 — Product Requirements Document

## Overview
- **Summary**: Audit, scientifically validate, repair, document, and build-verify the existing SmartPCB-XAI end-to-end repository so that it is a defensible, reproducible, working foundation for a final-year academic project. Cover AI layer (Python/YOLO), XAI, scoring, reports, FastAPI microservice, Express backend, MongoDB models, React frontend skeleton, datasets, and tests.
- **Purpose**: Eliminate fabricated claims, repair broken components, verify every subsystem independently, and leave the project in a demonstrable Part-1 state before Part-2 adds deep frontend polish, digital-twin, analytics dashboards, and full research evaluation.
- **Target Users**: Academic advisor (audit/research credibility), final-year student (defense preparation), Part-2 engineers (resuming from a clean, verified state).

## Goals
1. Independently verify or mark UNVERIFIED every performance claim in existing docs.
2. Repair broken or scientifically invalid components (XAI Grad-CAM hooks, class-name consistency, dataset leakage prevention, deterministic scoring).
3. Update all documentation (PROJECT_AUDIT, DATASET_REPORT, README, info txts) to reflect ground truth.
4. Ensure 9 core tests actually run (dataset validation, inference, severity, quality, KB, reports, XAI smoke, FastAPI health, backend import).
5. Pass Python syntax/import checks, the Python test suite, a FastAPI startup/health check, backend syntax start check, and frontend production build.
6. Produce PHASE1_VERIFICATION.md with a PASS/PARTIAL/FAIL/UNVERIFIED/BLOCKED evidence table.

## Non-Goals
- Part-2 work: advanced digital twin interactive layer, full analytics dashboard UX, deep feedback/continuous-learning retraining loop, final research evaluation benchmark with held-out runs, full deployment pipeline.
- Retraining models from scratch (CPU retraining would take days). Will verify existing checkpoints load and evaluate numbers from available CSV logs only.
- Adding new model architectures beyond existing YOLOv11 checkpoints.
- Requiring MongoDB to be running for passing tests (tests must degrade gracefully).

## Background & Context
Repository root: `d:\SmartPCB-XAI`.

Confirmed **actual** state via filesystem inspection (2026-09-23):

**Present (working/partially-working)**:
- AI: `ai/inference/engine.py` dual YOLO inference engine with tiling, CLAHE, NMS.
- AI: `ai/severity/severity_engine.py` deterministic scoring engine.
- AI: `ai/xai/gradcam.py` hooks registered but uses `torch.no_grad()` in forward path (Grad-CAM invalid).
- AI: `ai/recommendation/repair_kb.py` structured 6-defect KB.
- AI: `ai/reports/report_generator.py` ReportLab+OpenPyXL reports.
- AI Service: `ai_service/main.py` FastAPI with `/health`, `/inspect`, `/report/pdf`, `/report/excel`.
- Backend: `backend/server.js` Express + MongoDB + JWT + multer + FastAPI proxy. Models: User.js, Inspection.js, Feedback.js.
- Frontend: React 18 + TS + Tailwind, `App.tsx` with 5 tabs. Components: LiveInspection, DigitalTwin, AnalyticsView, FeedbackView, ModelPerformance. `frontend/dist/` has built artifacts.
- Datasets: `components_unified/` (1013 images, 33156 boxes, 6 classes), `defects/` (1500 images, 10013 boxes, 6 classes, DeepPCB).
- Datasets: `roboflow_remapped/`, `components/`, `fics_tiled/`, `components_curated/`, `defects_curated/`, `defects_mini/`.
- Models: `models/component_best.pt`, `models/defect_best.pt`, plus experiments `component_yolo11/`, `defect_yolo11/`, `mini_defect/` (20 epochs, plots present).
- Scripts: `scripts/dataset/validate_dataset.py`, `remap_roboflow.py`, `tile_images.py`, `process_deeppcb.py`, `inspect_dataset.py`.
- Tests: 4 files in `tests/`, 9 tests total, all 9 passed on 2026-09-23.
- Config: `requirements.txt`, `.env.example`, `docker-compose.yml`, `.trae-spec-mode/skill.

**Confirmed BROKEN/MISSING/QUESTIONABLE**:
1. **README.md claims mAP50 97.6% / 98.2% — UNVERIFIED**. Actual `results.csv`: `component_yolo11` epoch1 mAP50=0.01769, `defect_yolo11` epoch2 mAP50=0.456, `mini_defect` epoch1 mAP50=0.0.
2. **PROJECT_AUDIT.md and DATASET_REPORT.md are stale Phase-0 docs** claiming empty frontend/backend/models/datasets — directly contradicted by actual files.
3. **XAI Grad-CAM invalid**: `gradcam.py` line 65 `with torch.no_grad()` + line 70 `cam = mean(|activations|)` — no backward pass, no gradient weighting, no alpha weighting → this is activation-energy visualization, not authentic Grad-CAM++.
4. **Board-level leakage check incomplete**: `validate_dataset.py` only cross-checks filenames by exact-basename equality. Does not extract board IDs from `fics_s<N>_*` / `robo_*` / `<number>_*` prefixes to guarantee same-board tiles are not split across train/test.
5. **Class-name inconsistency**: components dataset uses `ICs`, `capacitors`, ... but inference code aliases vary. Severity engine uses both `ic`/`ics`, `transistor`/`transistors`, etc. (KB normalizes but canonical mapping not centralized).
6. **Dockerfiles missing**: `docker-compose.yml` references `Dockerfile.ai`, `backend/Dockerfile`, `frontend/Dockerfile` — none exist.
7. **Backend test placeholder**: `package.json` test script prints fake success message without running any test.
8. **info.txt / project-info.txt / aboutproject-info.txt**: Likely contain stale/fabricated numbers. Need audit.
9. **FastAPI `/health` does not report actual model load status / device / real version**. Hardcodes strings.
10. **Quality-score summary line in `severity_engine.py`**: says "meets IPC-A-610 Class 3 acceptance standards" when zero defects — this overclaims; must be labeled as project interpretation.
11. **Backend `server.js` line 19**: JWT_SECRET hardcoded fallback in source code. Should warn that `.env` must override for production.
12. **No dataset hash/dedup check** for perceptual duplicates.
13. **No XAI sanity test** in existing unittest suite (9 tests cover inference/severity/reports but not XAI).

## Functional Requirements
- **FR-1 Audit**: Write PROJECT_AUDIT.md with 8-category status (implemented/partial/broken/missing/claimed-not-reproducible/scientifically-questionable/technically-unnecessary/requires-user-data).
- **FR-2 Dataset report**: Write DATASET_REPORT.md covering original→mapped classes, ignored, rules, per-split counts, class imbalance, corruption, zero-area/OOB boxes, cross-split leakage.
- **FR-3 Leakage validation**: Create/upgrade `scripts/dataset/validate_dataset.py` (or new companion) to check board IDs, produce JSON. Must group `fics_s<N>`, `robo_*`, `<numbered>` DeepPCB groups.
- **FR-4 XAI repair / honest labeling**: Either (a) fix Grad-CAM to perform real backward pass with gradient weights + alpha and return structured metadata, OR (b) clearly rename class/docs to "Activation Energy Attribution (Grad-CAM heuristic approximation)" and add tests that prove output shape and no crash; include disclaimer.
- **FR-5 Inference robustness**: Engine must not crash on invalid image, huge image, missing model, low conf. Must return CPU/GPU-safe fallback.
- **FR-6 Severity / Quality deterministic**: Document formula. Never cite IPC-A-610 as defining a 0-100 math score. Label the score explicitly as project-defined.
- **FR-7 Repair KB honest**: Label it rule-based (not AI-trained). Do not mandate exact IPC sections unless cross-reference is plausible contextually.
- **FR-8 AI service**: `/health` returns actual model availability, device, real version. `/inspect` uses real engine.
- **FR-9 Backend + DB health-checkable**: Start-up check must not crash if MongoDB is down (already has warn-based fallback). Env example present.
- **FR-10 Tests (10 minimum required for Part 1)**:
  1. dataset validation runs + JSON output
  2. label validation (zero area, OOB, class range)
  3. inference engine (synthetic + real image) → already exist (2)
  4. severity (2) → already exist
  5. quality score → exists
  6. recommendation KB → exists
  7. PDF report generation → exists
  8. Excel report generation → exists
  9. XAI smoke (output shape, no crash) — NEW
  10. FastAPI import + TestClient health — NEW
- **FR-11 Builds**:
  - Python syntax/import checks pass
  - Python unittest suite (≥9 tests) passes
  - FastAPI startup import + health via TestClient passes
  - Backend `node --check` (syntax) passes
  - Frontend `npm run build` succeeds (with npm install if required)
- **FR-12 Documentation**: README, PROJECT_AUDIT, DATASET_REPORT, info.txt, project-info.txt, aboutproject-info.txt updated; "Verified vs Unverified Claims" section added to README.
- **FR-13 Phase1 Verification doc**: PHASE1_VERIFICATION.md table with Component / Status / Evidence / Command / Notes and status ∈ {PASS, PARTIAL, FAIL, UNVERIFIED, BLOCKED}.

## Non-Functional Requirements
- **NFR-1 Research honesty**: All performance numbers must be actually reproducible from artifacts or marked UNVERIFIED. Fabricated values → corrected.
- **NFR-2 Graceful degradation**: No subsystem crashes because CUDA / MongoDB / browser / model file unavailable.
- **NFR-3 Centralized config**: Confidence/IoU thresholds not scattered; severity weights in one class.
- **NFR-4 Determinism**: Severity and quality scoring must be pure math (no RNG) for identical inputs.
- **NFR-5 CPU-safe by default**: All inference calls that run during tests use `device=cpu` explicitly.

## Constraints
- **Technical**: Must preserve existing layered architecture (React → Express → FastAPI → YOLO → MongoDB). Cannot move inference to frontend. Must keep canonical classes (components: ICs/capacitors/diodes/inductors/resistors/transistors; defects: open/short/mousebite/spur/copper/pin-hole).
- **Business**: Cannot discard existing dataset files or trained .pt checkpoints. Cannot retrain from scratch on CPU due to TRAE session time budget.
- **Dependencies**: Python 3.11+ env with ultralytics, torch, fastapi, reportlab, pandas etc. Node 20+ for backend/frontend. Existing `requirements.txt` and package.json are authoritative.

## Assumptions
1. Python virtualenv `(TraeAI-3)` in terminal id 3 is active and already has required packages (9 tests pass).
2. Dataset zips referenced in remap scripts may not be present; scripts handle missing gracefully or we note BLOCKED.
3. MongoDB service may not be running during Part 1 test suite. Tests should not require it.
4. Docker daemon may not be available; docker-compose can be BLOCKED.
5. Frontend npm install is allowed if needed for production build.

## Acceptance Criteria

### AC-1: PROJECT_AUDIT.md accurately categorizes every subsystem
- **Type**: `rule`
- **Given**: Actual filesystem inspection on 2026-09-23.
- **When**: PROJECT_AUDIT.md is written with the 8 required status categories and references all modules: ai/, ai_service/, backend/, frontend/, datasets/, models/, experiments/, scripts/, tests/, docker/, docs.
- **Then**: Every module is categorized, broken/fabricated items are explicitly flagged, and claimed vs reproducible is separated.
- **Pass Condition**: File exists at `PROJECT_AUDIT.md` and contains all 8 status categories with concrete entries.
- **Evidence**: Manual diff against actual file tree; specific references to confirmed broken items (XAI no-grad, mAP numbers false, stale old audit overwritten).

### AC-2: DATASET_REPORT.md scientifically accurate
- **Type**: `rule`
- **Given**: validate_dataset.py run output (1013 comp, 1500 defect; zero corruption/leakage).
- **When**: DATASET_REPORT.md is updated with per-dataset tables, original/mapped classes for Roboflow, class-imbalance %, board-level split rationale, and leakage proof text.
- **Then**: It contains exact counts from the script run (33156 component boxes, 10013 defect boxes, 6+6 classes) and no fabricated numbers.
- **Pass Condition**: Script output counts match report counts exactly.
- **Evidence**: validate_dataset.py stdout + file content line-for-line match on totals.

### AC-3: Board-level leakage validation script produces machine-readable proof
- **Type**: `rule`
- **Given**: components_unified/, defects/ datasets.
- **When**: validation script runs with board-ID grouping logic (fics_s<N>, roboflow parent name, DeepPCB numeric board prefix).
- **Then**: JSON output field `cross_split_board_leakage_count` is integer 0; fields per_split_board_ids show disjoint board sets; exit code 0.
- **Pass Condition**: Script runs end-to-end, writes `reports/dataset/validation_report.json`, and leakage=0 (or documents real nonzero with locations).
- **Evidence**: JSON file contents + console output.

### AC-4: XAI either authentic or honestly labeled approximation
- **Type**: `rule`
- **Given**: Current gradcam.py with `torch.no_grad()` forward and activation-only heatmap.
- **When**: XAI module is modified and tested. If authentic path (A): the generate_heatmap method enables gradients, runs backward pass on a target score, applies alpha/weighting per Grad-CAM++ paper, and returns target_class/confidence/bbox metadata. If honest approximation path (B): class/docstrings renamed to ActivationEnergyAttribution, README and API response label disclaim it as heuristic, and it still returns metadata. Either path passes.
- **Then**: New XAI smoke test passes; overlay shape matches input image shape; no NaN in heatmap.
- **Pass Condition**: Smoke test `test_xai_smoke` in unittest suite passes and API xai dict contains at least {target_class, target_confidence, bbox, attribution_method, disclaimer_or_metadata}.
- **Evidence**: unittest stdout + test file.

### AC-5: No fabricated mAP numbers in README/paper docs
- **Type**: `rule`
- **Given**: README.md currently claims "97.6% mAP@50 component / 98.2% mAP@50 defect".
- **When**: README and info txts are re-edited.
- **Then**: Benchmark section moves numbers into "Verified vs Unverified Claims" section, each either tied to reproducible CSV epoch value (e.g., component_yolo11 epoch1 mAP50=0.018 — UNVERIFIED full run) or clearly labeled UNVERIFIED/CLAIMED-NOT-REPRODUCIBLE.
- **Pass Condition**: README contains "Verified vs Unverified Claims" section; standalone `97.6%` / `98.2%` are NOT top-level facts without provenance.
- **Evidence**: grep for bare `97.6%` returns 0 matches in README, or match is inside UNVERIFIED section.

### AC-6: 9+ Python unittest tests pass (including new XAI + FastAPI health)
- **Type**: `rule`
- **Given**: Existing 9 passing tests.
- **When**: `python -m unittest discover -s tests -p "test_*.py" -v` runs.
- **Then**: Exit code 0; count of passed tests ≥ 9; new test names (test_xai_smoke, test_fastapi_health) present in output.
- **Pass Condition**: Terminal exit 0 and ≥11 tests passed OK.
- **Evidence**: Terminal capture with test name lines and final "Ran X tests OK".

### AC-7: FastAPI startup + TestClient health check
- **Type**: `rule`
- **Given**: ai_service/main.py importable.
- **When**: TestClient import runs `GET /health` without a running server.
- **Then**: Response status 200; JSON contains {status, model_status.{component_model, defect_model, xai_engine, device, version}} where device is actually queried (torch/cuda avail) not hardcoded.
- **Pass Condition**: unittest passes and keys exist.
- **Evidence**: unittest output + updated /health source.

### AC-8: Backend syntax ok + package.json not fake-testing
- **Type**: `rule`
- **Given**: backend/server.js currently has no real test.
- **When**: (a) `node --check backend/server.js` runs; (b) Backend package.json test script is not a hardcoded success echo if possible — if tests can't run without Mongo, at minimum a syntax check via node --check is included and documented as PARTIAL with BLOCKED reason in PHASE1_VERIFICATION.
- **Then**: Syntax check exit code 0; PHASE1 table status accurately reflects reality.
- **Pass Condition**: node --check exit 0; and PHASE1_VERIFICATION explicitly says what was verified.
- **Evidence**: Node stdout + PHASE1 table row.

### AC-9: Frontend production build succeeds
- **Type**: `rule`
- **Given**: frontend/ with package.json, vite, tsconfig.
- **When**: npm install (if no node_modules) then npm run build.
- **Then**: dist/ rebuilt, exit code 0.
- **Pass Condition**: No TS errors; dist/assets/ generated.
- **Evidence**: Vite build stdout + dist folder listing.

### AC-10: Deterministic scoring + honest labels (no false IPC-A-610 score claim)
- **Type**: `rule`
- **Given**: severity_engine.py summary says "meets IPC-A-610 Class 3 acceptance standards".
- **When**: Summary strings and docs updated.
- **Then**: The 0–100 score formula is explicitly labeled "SmartPCB-XAI project-defined severity score" in docstrings and code comments. IPC-A-610 is only named as a reference standard for workmanship guidance, not as defining the numeric score.
- **Pass Condition**: grep for phrase "project-defined severity score" matches ≥2 locations; no "IPC-A-610 defines" claim.
- **Evidence**: Source file text + grep stdout.

### AC-11: Canonical component/defect class names consistent across data.yaml ↔ inference ↔ frontend
- **Type**: `rule`
- **Given**: 6+6 canonical classes defined.
- **When**: All data.yamls in {components, components_unified, components_curated, roboflow_remapped, fics_tiled, defects, defects_curated, defects_mini} are checked against canonical lists and the inference engine class names usage is reviewed.
- **Then**: No mismatches. Classes must be exactly: components 0-ICs 1-capacitors 2-diodes 3-inductors 4-resistors 5-transistors. Defects: 0-open 1-short 2-mousebite 3-spur 4-copper 5-pin-hole.
- **Pass Condition**: All 8+ data.yaml files read and confirmed; any mismatch fixed or reported in audit.
- **Evidence**: Read of each data.yaml + centralized CANONICAL dict in code if helpful alias map exists.

### AC-12: PHASE1_VERIFICATION.md table produced with correct status vocab
- **Type**: `rule`
- **Given**: All verification substeps A–J actually executed.
- **When**: File is written.
- **Then**: Rows exist for (A repo audit, B dataset validation, C Python syntax, D unit tests, E inference smoke, F XAI smoke, G reports, H FastAPI health, I backend health syntax, J frontend build) + extras; status ∈ {PASS,PARTIAL,FAIL,UNVERIFIED,BLOCKED}; each has Evidence / Command / Notes columns.
- **Pass Condition**: File exists with all rows populated.
- **Evidence**: File contents.

### AC-13: Repository fidelity — no working features removed, no secrets committed
- **Type**: `rubric`
- **Dimension**: Preservation of working functionality and security hygiene
- **Scale**: 1-5
- **Anchors**: 1 = critical features removed / secrets in source; 3 = minor feature loss or no new docs; 5 = every working subsystem preserved exactly where it was, only bugs fixed and docs added; JWT fallback secret is clearly labeled DEVELOPMENT-ONLY in server.js and .env.example; no keys written into spec/test artifacts.
- **Pass Threshold**: >= 4
- **Evidence**: Spot-check of source files and final file listing. Subsystems preserved: engine, xai, reports, fastapi, backend routes, frontend 5-tab layout, existing model .pt files, dataset images.

### AC-14: Code quality and auditability
- **Type**: `rubric`
- **Dimension**: Readability of fixes, centralization of magic numbers, separation of responsibilities
- **Scale**: 1-5
- **Anchors**: 1 = spaghetti patches all over; 3 = workable but scattered config; 5 = (i) CANONICAL_CLASSES/DEFECT_CLASSES constants in one location, (ii) thresholds read from one CONFIG dict, (iii) XAI disclaimer/authentic path clearly documented inline, (iv) spec tasks traceable to code changes.
- **Pass Threshold**: >= 4
- **Evidence**: Final code review of modified files.

## Open Questions
- [ ] Part 2 scope boundary: should any remaining frontend component deep-fixing (e.g., LiveInspection UX bugs) move into Part 1 or stay Part 2? (Default: stay Part 2 unless build is broken.)
- [ ] Are we allowed to overwrite stale PROJECT_AUDIT.md entirely with accurate new content, or preserve old audit as a reference? (Default: overwrite; old claims were directly false about existing files.)
