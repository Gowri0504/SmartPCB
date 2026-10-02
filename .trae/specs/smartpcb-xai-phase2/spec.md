# SmartPCB-XAI Phase 2 — Product Requirements Document

## Overview
- **Summary**: Continue the end-to-end SmartPCB-XAI repository from its CURRENT VERIFIED STATE (16/16 Python tests passing, dual YOLOv11 inference engine CPU-safe, XAI honestly-labeled activation-energy approximation, deterministic severity/quality scoring, FastAPI microservice with truthful /health, Express backend with JWT + MongoDB, React 5-tab dashboard skeleton, component_unified + DeepPCB defect datasets). Focus on: APPEND-only documentation corrections (PROJECT_AUDIT.md, DATASET_REPORT.md, README.md, info.txts are STALE/contradictory to actual filesystem), dataset validation enhancements, model safety/verification layer, report generator section additions, benchmarking script, Dockerfiles, test suite expansion, frontend API integration repair, and PHASE2_VERIFICATION.md evidence table.
- **Purpose**: Turn the existing defensible skeleton into a reproducibly-verified end-to-end system with honest documentation, no fabricated claims, and a clean Part-2 handoff for deep UI polish and final research evaluation.
- **Target Users**: Academic advisor audit, final-year student defense, Part-2 continuation engineers.

## Background & Context
Repository root: `d:\SmartPCB-XAI`.

**VERIFIED STATE via 2026-09-23 filesystem+test inspection**:
- ✅ 16/16 Python unit tests pass (18.4s, CPU device). Tests cover: FastAPI health, inference engine synthetic+real, PDF, Excel, severity×5, repair KB, XAI×3.
- ✅ ai/config.py centralizes: CANONICAL_COMPONENT_CLASSES (6), CANONICAL_DEFECT_CLASSES (6), aliases, DEFAULT_INFERENCE_CONFIG, XAI_ATTRIBUTION_METHOD="activation_energy_approximation", XAI_DISCLAIMER, PROJECT_VERSION="1.0.0-phase1".
- ✅ ai/inference/engine.py SmartPCBInspectionEngine: CPU/CUDA graceful fallback, tiled+global NMS, CLAHE preprocessing, severity attachment, XAI integration with disclaimer, zero-detection warning pipeline.
- ✅ ai/xai/gradcam.py: Honestly labeled "Activation Energy Attribution (APPROXIMATION, not true Grad-CAM++)" with backward hooks registered but torch.no_grad() forward pass. Returns structured metadata.
- ✅ ai/severity/severity_engine.py: Deterministic scoring with "SmartPCB-XAI project-defined severity score" labels, no false IPC-A-610 numeric score claim. DEFECT_BASE_WEIGHTS×, COMPONENT_CRITICALITY×, clamp(0-100), CRITICAL/HIGH/MEDIUM/LOW levels.
- ✅ ai/recommendation/repair_kb.py: 6-defect structured KB with title/probable_causes/inspection_steps/repair_actions/verification_steps/ipc_standard. Normalization map for aliases.
- ✅ ai/reports/report_generator.py: ReportLab PDF (header banner, metadata table, defects table, components table, recommendations table) + OpenPyXL Excel (Inspection_Summary, Defects, Components, Repair_Procedures sheets).
- ✅ ai_service/main.py FastAPI: /health (truthful status, model_status, device, version, canonical_classes), /api/v1/inspect (real engine + base64 preview/XAI overlay), /api/v1/report/pdf, /api/v1/report/excel. Pydantic ReportRequest.
- ✅ backend/server.js Express: Auth (register/login/demo), JWT authMiddleware with DEVELOPMENT-ONLY-INSECURE fallback label, multer uploads 25MB limit, MongoDB connection with console.warn graceful degradation, FastAPI proxy for /inspection/upload + report proxies, analytics aggregation, feedback recording.
- ✅ Models present: models/component_best.pt (94.9 MB), models/defect_best.pt (94.9 MB), yolo11n.pt baseline. experiments/: defect_yolo11 (results.csv epoch2 mAP50=0.456), component_yolo11 (epoch1 mAP50=0.01769), mini_defect (plots + epoch3 results).
- ✅ Datasets: components_unified (data.yaml 6 canonical classes, per train/val/test splits 807/116/90), defects/DeepPCB (6 canonical, 850/150/500), plus components_curated, defects_curated, roboflow_remapped, fics_tiled, defects_mini variants.
- ✅ scripts/dataset/validate_dataset.py: 8-check validation (duplicate hashes, duplicate filenames, board_id_overlap, split_overlap_by_filename, zero_area_boxes, normalized_coords_out_of_range, missing_image_label_pairs, class_ids_out_of_range) + MD5 dedup + machine-readable JSON + matplotlib distribution plots.
- ✅ Frontend: React 18+TS+Tailwind, App.tsx 5 tabs (Inspection Studio, Digital Twin, Analytics, Continuous Learning, Research & Benchmarks). dist/ build artifacts present (index-*.js, index-*.css).
- ✅ docker-compose.yml: mongodb:7, ai-service (Dockerfile.ai), backend (Dockerfile), frontend (Dockerfile). 5 services.
- ✅ .env.example: Mongo/FastAPI/Port env vars.

**KNOWN STALE/FALSE DOCUMENTATION (MUST APPEND CORRECTIONS, NOT DELETE):**
1. ❌ PROJECT_AUDIT.md (generated 2026-09-22, Phase 0): Claims frontend/backend/models/datasets EMPTY. Contradicted by every actual file.
2. ❌ DATASET_REPORT.md (2026-09-22, Phase 0): Claims NO defect dataset, FICS only 9 DSLR images before tiling, Roboflow not extracted, components_unified does not exist.
3. ❌ README.md: Benchmark section top-level claims "97.6% mAP@50 component / 98.2% defect / 16.1ms / 0.0% Data Leakage" with NO provenance. UNVERIFIED per actual experiments results.csv (component_yolo11 epoch1 mAP50=0.01769, defect_yolo11 epoch2 mAP50=0.456, mini_defect best only 4 epochs).
4. ❌ info.txt, project-info.txt, aboutproject-info.txt: Expected to contain stale/fabricated metric claims from earlier drafts.

**KNOWN MISSING ITEMS (Phase 2 scope):**
1. No benchmark_inference.py script.
2. No Dockerfiles: Dockerfile.ai, backend/Dockerfile, frontend/Dockerfile referenced by compose but absent.
3. Reports missing sections: PDF lacks Limitations page / XAI info / inference timing / model metadata disclaimer / severity sheet. Excel lacks Severity / Model_Metadata / Limitations sheets.
4. No model safety validation layer (verify checkpoint exists, loads, class count matches, class names match, arch matches).
5. No tiny deterministic test fixtures for dataset / model smoke tests (rely on real dataset images currently; OK but expand coverage with synthetic fixtures).
6. No evaluate.py inspection.
7. Frontend LiveInspection.tsx and other components: API integration state unknown (need to read and repair if broken).
8. Backend package.json test script: currently unknown if fake echo or real test.
9. PHASE2_VERIFICATION.md does not exist. Must be created with 12+ rows PASS/PARTIAL/FAIL/UNVERIFIED/BLOCKED table.
10. No near-duplicate image detection (perceptual hashing - pHash/dHash - in validate_dataset.py; MD5 only catches exact duplicates).
11. No empty-label image count or annotation-per-image distribution stats in validate_dataset JSON.
12. Class-name consistency check not yet RUN (need to open all 8 data.yamls + verify model.names vs canonical).
13. Board-level leakage: validate_dataset.py has extract_board_id with FICS/Robo/DeepPCB patterns but never been run to produce JSON evidence. Must run, verify counts, report.
14. Backend node --check never run.
15. Frontend npm run build never re-run (dist/ exists from prior session; need to verify reproducibility).
16. No model_version / inference_time fields in engine inspect() output / reports.
17. Knowledge base missing explicit "Rule-Based Root-Cause Recommendation Engine" labeling in docstring, and entries lack `safety_note` field per user spec 15.
18. FastAPI error handling: /inspect catches exception + returns payload, but HTTP status is 200 even on ERROR state. Should return structured error but keep 200 for client graceful handling (or 500? Keep 200 for user-friendliness and inspect inspection_status field - that's already fine, but /report routes raise HTTPException(500) - keep as-is since errors are server-only).
19. evaluate.py not inspected.

## Goals (Phase 2)
1. Fix documentation SCIENTIFIC INTEGRITY: APPEND corrections to all stale info files preserving every original line. Add "Verified vs Unverified Claims" section in README.
2. Enhance dataset validation: add perceptual near-duplicates, empty-label counts, annotation-per-image distribution, explicit board-ID verification run JSON evidence.
3. Add model safety/verification: validate checkpoint existence/load/class count/class names/arch before using. Add verification routine.
4. Add benchmark_inference.py measuring preprocess/inference/postprocess/total with mean/median/min/max/std + device info.
5. Add 3 Dockerfiles matching docker-compose.yml structure.
6. Expand report generators with Severity sheet/model metadata sheet/Limitations page/inference timing/XAI info/confidence distribution.
7. Enhance tests: add dataset validation smoke test, evaluate model safety, add fixtures, add backend node check.
8. Verify + repair frontend components API integration, loading/error states.
9. Run ALL verifications (A-J per user spec) and produce PHASE2_VERIFICATION.md evidence table.

## Non-Goals (Phase 2)
- Full model retraining (CPU infeasible within session budget). Will verify checkpoint load/class names only.
- Digital Twin interactive 3D layer polish (Part 2).
- Full analytics dashboard deep UX (Part 2).
- MongoDB actually running for persistence tests (will report BLOCKED if not available).
- Docker daemon actually running for docker-compose up (report BLOCKED if daemon absent).
- Final research evaluation with precision/recall/mAP on full test set (write evaluation scripts only; mark results "Evaluation pending").

## Functional Requirements
### FR-1 Documentation APPEND-only corrections (preserve original lines)
- For PROJECT_AUDIT.md: append "NEW UPDATE — 2026-09-23", then "CORRECTION / CLARIFICATION" for each stale claim (frontend empty→implemented, backend empty→implemented, etc.). Preserve original Phase-0 audit word-for-word.
- For DATASET_REPORT.md: append "NEW UPDATE — 2026-09-23" with actual component_unified counts, DeepPCB defect counts, Roboflow remap provenance, validate_dataset.py JSON output reference. Keep original text intact.
- For README.md: append "NEW UPDATE — 2026-09-23", add "Verified vs Unverified Claims" section, move 97.6%/98.2%/16.1ms into UNVERIFIED column. Keep original Benchmark section intact as-is but add CORRECTION below it.
- For info.txt / project-info.txt / aboutproject-info.txt: read full content, append "CORRECTION / CLARIFICATION — 2026-09-23" to each with actual verified status of any stale claims.
- For each file, add HISTORICAL CONTENT RECOVERY STATUS if git has no history (No commits yet - original content preserved in-place, corrections appended as new trailing text only).

### FR-2 Dataset validation enhancements
- In validate_dataset.py: add checks for (1) empty-label files (txt file exists but 0 boxes), (2) image file can be decoded + valid pixels, (3) perceptual-hash near-duplicate detection (pHash d=8 Hamming distance <= threshold 5), (4) per-image box count distribution stats. Output human-readable summary + JSON. Run on components_unified + defects and save validation_report.json with new fields.
- Actually RUN validate_dataset.py and report board_level_cross_split_leak_count for both datasets. If nonzero, report with exact board IDs.

### FR-3 Component class mapping traceability
- Read ALL 8 data.yamls. Verify canonical component class names = ["ICs", "capacitors", "diodes", "inductors", "resistors", "transistors"]. Verify defect = ["open", "short", "mousebite", "spur", "copper", "pin-hole"]. Read remap_roboflow.py logic. Check for invalid class IDs (e.g. class 7) anywhere in label files across all datasets. Log counts. Do not delete labels; report unmapped/ignored.

### FR-4 Model safety / checkpoint verification
- Add new file ai/model_safety.py (or add function to ai/inference/engine.py) `verify_checkpoint(path, expected_classes, device)` returning dict: {exists:bool, loads:bool, arch_name:str, class_count:int, class_names_match:bool, class_names:list, device_worked:bool, error:str|None, status:PASS/FAIL/UNVERIFIED/BLOCKED}.
- Run on models/component_best.pt + models/defect_best.pt. Store in ai_service /health response under `model_status.component_model.verification` etc.

### FR-5 Inference engine metadata (model_version + inference_time)
- Add to engine.inspect() return dict: `model_version` (component_model_path basename + defect basename), `inference_timing` {preprocess_ms, component_inference_ms, defect_inference_ms, xai_ms, postprocess_ms, total_ms}. Include timing in reports.

### FR-6 Report generator section additions
- PDF report (ADD new sections, don't remove existing):
  a. XAI Attribution Summary page with method name + disclaimer.
  b. Limitations & Scientific Disclaimers page (list all project-defined scores, XAI approximation, model unverified performance).
  c. Inference Timing section.
  d. Confidence Distribution bar (per-defect confidence list).
  e. Model Metadata section (checkpoint names, version, device).
- Excel report (ADD sheets, don't remove existing):
  a. Severity sheet.
  b. Model_Metadata sheet.
  c. Limitations sheet.
  d. XAI sheet.
- Keep existing sections/sheets EXACTLY as they are; append new flowables/pages.

### FR-7 Repair KB honest labeling + safety_notes field
- Add module docstring header: "Rule-Based Root-Cause Recommendation Engine".
- Add optional `safety_notes` list to each of the 6 defect entries. Do not remove any existing keys/entries; ADD only.

### FR-8 Benchmark inference script
- Create scripts/benchmark_inference.py. Accept optional --image path --iterations N default 10. If no image, use synthetic PCB 640x640 fixture. Measure: preprocess_ms, component_inference_ms, defect_inference_ms, xai_ms, postprocess_ms, total_ms for each iteration. Report mean, median, min, max, std. Include device info (torch.cuda.is_available, CUDA version if any, CPU brand if available). Exit 0. If models missing, output BLOCKED status to stdout + json to reports/benchmark/benchmark.json.

### FR-9 Dockerfiles (new additive files)
- Create root-level Dockerfile.ai: Python slim, pip install requirements, copy ai/ ai_service/ models/, uvicorn ai_service.main:app on port 8000.
- Create backend/Dockerfile: Node 20 slim, npm install, expose 5000, npm start.
- Create frontend/Dockerfile: multi-stage, npm ci, npm run build, nginx alpine serve dist on port 80.
- Do not modify existing docker-compose.yml.

### FR-10 FastAPI robustness
- Verify Pydantic schemas: ReportRequest exists, but inspect endpoint uses Form+File (no Pydantic body - OK).
- Add UploadFile content-type + file extension validation, max size enforcement (already use 25MB in backend, but FastAPI needs explicit max - optional via HTTPException 413).
- Ensure no internal stack traces leak to normal HTTP clients (/inspect already catches; /report routes raise HTTPException with message only - good).

### FR-11 Backend syntax + honest test script
- Run node --check backend/server.js.
- Read backend/package.json test script: if fake echo, replace with `node --check server.js` or similar honest syntax check that exits nonzero on failure.

### FR-12 Frontend verification + API integration repair
- Read each frontend component (LiveInspection.tsx, DigitalTwin.tsx, AnalyticsView.tsx, FeedbackView.tsx, ModelPerformance.tsx).
- Check for correct API URLs (http://localhost:5000 or env var), loading states, error states, result rendering.
- Fix broken fetch/axios calls, missing loading indicators, undefined result access crashes.
- Add env VITE_BACKEND_URL if not present. Preserve existing screens.
- Run frontend production build reproducibly: npm install --prefix frontend && npm run build --prefix frontend. Verify dist regenerated.

### FR-13 Test suite expansion
- Add tests/dataset_val_smoke.py: Run validate_dataset's core logic on a tiny temp fixture (synthetic dataset with 1 valid train image 1 empty label, 1 OOB box test image) to verify checks detect issues.
- Add tests/test_model_safety.py: Test verify_checkpoint on a nonexistent path (FAIL expected) and on yolo11n.pt (PASS expected with COCO class_count=80, class_names_match=False vs canonical 6).
- Add tests/test_backend_syntax.py: Subprocess call `node --check ../backend/server.js`, assert exit 0.
- Keep every existing test intact.

### FR-14 PHASE2_VERIFICATION.md evidence table
- Create file (or append NEW UPDATE — 2026-09-23 if it already exists; it doesn't yet) with rows: Dataset, Models, Inference, XAI, Severity, Quality, Reports, FastAPI, Backend, Frontend, Tests, Docker, Research Evaluation. Each row exactly 5 columns: Area, Status (∈{PASS,PARTIAL,FAIL,UNVERIFIED,BLOCKED}), Evidence, Command/Test, Notes.
- Run each of A-J (repository audit, dataset validation run, Python compileall, unittest discover, inference smoke, XAI smoke, reports test, FastAPI health via TestClient, backend node syntax, frontend build) and fill table rows with actual results. No fabricated statuses.

## Non-Functional Requirements
- **NFR-1 Documentation preservation**: Every existing line in README.md, PROJECT_AUDIT.md, DATASET_REPORT.md, info*.txt files MUST remain byte-for-byte identical to current state. Only APPEND operations allowed. If a markdown heading exists, the correction goes BELOW the existing content at the end of the file.
- **NFR-2 Honest labeling**: (i) XAI → activation_energy_approximation + disclaimer never claim gradcam++. (ii) Severity/Quality → "SmartPCB-XAI project-defined severity score" ≥3 locations. (iii) Repair KB → "Rule-Based Root-Cause Recommendation Engine" at module top. (iv) Never "IPC-A-610 score" — only workmanship guidance reference.
- **NFR-3 CPU-safe all tests**: Every new python test runs on CPU explicitly, no CUDA requirement, no crash if CUDA absent.
- **NFR-4 No secrets commit**: JWT fallback stays labeled DEVELOPMENT-ONLY. No real keys in any file.
- **NFR-5 Reproducibility**: benchmark_inference.py uses sys/time not hardcoded numbers. Report metrics are actual computed values.

## Constraints
- Technical: Preserve layered architecture (React→Express→FastAPI→YOLO→MongoDB). No inference on frontend. Canonical class names fixed 6+6.
- Business: Cannot delete existing .pt checkpoints, dataset images, or experiment artifacts. Cannot retrain on CPU due to time budget.
- Dependencies: Existing requirements.txt authoritative. ultralytics + torch + fastapi + reportlab + openpyxl + pandas all verified installed (16 tests pass).

## Assumptions
1. Python env (TraeAI-7) terminal id 7 active with all deps.
2. npm/node available for frontend build and backend --check.
3. MongoDB service may not be running (report BLOCKED for persistence tests).
4. Docker daemon may not be running (report BLOCKED for docker build).
5. User allows npm install for frontend build reproducibility check.

## Acceptance Criteria
### AC-1: All 4+ stale docs APPENDED with CORRECTION / NEW UPDATE sections (no lines deleted)
- **Type**: rule
- **Pass Condition**: Grep in each of {README.md, PROJECT_AUDIT.md, DATASET_REPORT.md, info*.txt} for literal "NEW UPDATE — 2026-09-23" → present; AND manual check: original stale content (PROJECT_AUDIT "EMPTY frontend", DATASET_REPORT "NO defect dataset", README top-level 97.6%) still present in the file unchanged ABOVE the append line.
- **Evidence**: grep stdout + file line-by-line before/after comparison.

### AC-2: README contains "Verified vs Unverified Claims" table/section
- **Type**: rule
- **Pass Condition**: README.md section exists with rows for 97.6%/98.2%/16.1ms marked UNVERIFIED or CLAIMED-NOT-REPRODUCIBLE; rows for test pass count (16), dataset counts (1013 comp, 1500 defect) marked VERIFIED with source command.
- **Evidence**: grep stdout for section heading + entries.

### AC-3: Dataset validation runs with enhanced checks, produces JSON with new fields
- **Type**: rule
- **Pass Condition**: `python scripts/dataset/validate_dataset.py` runs exit 0; validation_report.json contains keys: checks.empty_label_files, checks.image_decode_errors, checks.perceptual_hash_near_duplicates, per_split.*.empty_label_count, box_count_per_image_stats (min/max/median/mean); and actual board_level_cross_split_leak_count integer for both datasets is reported.
- **Evidence**: JSON file keys exist + script stdout.

### AC-4: Model safety verification implemented and health exposes it
- **Type**: rule
- **Pass Condition**: verify_checkpoint() callable; returns dict with {exists,loads,arch_name,class_count,class_names_match,status}; for yolo11n.pt class_names_match vs canonical is False; for component_best.pt and defect_best.pt status is PASS or FAIL but not UNVERIFIED; /health response includes verification field under model_status.*.verification.
- **Evidence**: Python REPL one-liner + /health TestClient JSON.

### AC-5: Benchmark script produces timing stats
- **Type**: rule
- **Pass Condition**: `python scripts/benchmark_inference.py --iterations 3` exits 0; stdout contains mean/median/min/max/std lines; reports/benchmark/benchmark.json has per-iteration arrays + aggregate stats + device_info dict.
- **Evidence**: terminal stdout + JSON file. If models absent → BLOCKED text appears in output + exit 0 (script handles it gracefully).

### AC-6: Three Dockerfiles exist with correct structure
- **Type**: rule
- **Pass Condition**: `Dockerfile.ai` in root, `backend/Dockerfile`, `frontend/Dockerfile` all exist; each FROM present; ai has uvicorn command; backend has npm start / expose 5000; frontend multi-stage build → nginx.
- **Evidence**: ls + file head of each Dockerfile. (docker build BLOCKED if no daemon, OK.)

### AC-7: Reports have new sections/sheets (old content preserved)
- **Type**: rule
- **Pass Condition**: Running generate_pdf/excel on sample data produces files that when inspected: PDF has ≥1 new page after old recommendations (XAI, Limitations, Timing, Metadata); Excel has sheets: Inspection_Summary, Defects, Components, Repair_Procedures, Severity, Model_Metadata, Limitations, XAI (8 sheets total minimum). Old section headers (Defect Analysis, Verified Components, Prescriptive Repair) still present.
- **Evidence**: test_reports.py modified test (existing test still passes) + new assertions on PDF page count / Excel sheet names in new test_reports_additions.py.

### AC-8: Engine inspect output includes timing + model_version keys
- **Type**: rule
- **Pass Condition**: synthetic image inspection returns inspection dict with keys model_version (str) and inference_timing (dict with preprocess_ms, component_inference_ms, defect_inference_ms, xai_ms, postprocess_ms, total_ms); all numeric and total_ms ≥ sum of others approximately.
- **Evidence**: python assertion.

### AC-9: Repair KB honestly labeled + safety_notes added without deletion
- **Type**: rule
- **Pass Condition**: `ai/recommendation/repair_kb.py` module docstring contains "Rule-Based Root-Cause Recommendation Engine"; each of 6 defect entries has "safety_notes" list key added; all old keys (title/probable_causes/inspection_steps/repair_actions/verification_steps/ipc_standard) still present for every entry.
- **Evidence**: grep + python dict iteration.

### AC-10: 20+ total tests pass
- **Type**: rule
- **Pass Condition**: `python -m unittest discover -s tests -p "test_*.py" -v` shows ≥20 tests with all OK, no failures, no errors; Ran N tests ≥ 20. New test names present: test_dataset_val_smoke, test_model_safety_*, test_backend_syntax.
- **Evidence**: terminal stdout.

### AC-11: Backend node --check passes + package.json honest tests
- **Type**: rule
- **Pass Condition**: `node --check backend/server.js` exit 0; backend/package.json "test" script is NOT `echo "All tests passed"` or other fake unconditional success.
- **Evidence**: terminal stdout + package.json content.

### AC-12: Frontend production build succeeds from scratch
- **Type**: rule
- **Pass Condition**: `npm install --prefix frontend` (if needed) then `npm run build --prefix frontend` exit 0; dist/assets contains new hash-named .js and .css files.
- **Evidence**: vite stdout + ls dist.

### AC-13: PHASE2_VERIFICATION.md table with correct vocabulary
- **Type**: rule
- **Pass Condition**: Exists with markdown table, rows: Dataset, Models, Inference, XAI, Severity, Quality, Reports, FastAPI, Backend, Frontend, Tests, Docker (12 minimum). Status column values strictly ∈ {PASS,PARTIAL,FAIL,UNVERIFIED,BLOCKED} (case-insensitive but prefer uppercase). Each row has Evidence, Command/Test, Notes columns populated.
- **Evidence**: File contents.

### AC-14: Documentation preservation fidelity (rubric)
- **Dimension**: Did the implementation preserve every original line in all protected documentation files?
- **Scale**: 1-5
- **Anchors**: 1 = large blocks of stale content deleted or replaced; 3 = some lines rewritten but most preserved; 5 = every original line in README/PROJECT_AUDIT/DATASET_REPORT/info* still present in the same file, unmodified, with CORRECTION / NEW UPDATE appended only.
- **Pass Threshold**: ≥ 4
- **Evidence**: Manual diff of before/after file content — but no git commits so rely on structural check: original first line of PROJECT_AUDIT still "# SmartPCB-XAI — Complete Project Audit"; original DATASET_REPORT "## Executive Summary" still present with same 839 / 587 DSLR numbers inside.

### AC-15: Scientific honesty / no fabricated claims (rubric)
- **Dimension**: Honesty of claims across all docs + code + responses
- **Scale**: 1-5
- **Anchors**: 1 = new fabricated numbers added; 3 = some claims without provenance still top-level; 5 = every measurable claim either (a) verified with command evidence or (b) explicitly labeled UNVERIFIED/CLAIMED. XAI → approx, severity→project-defined, KB→rule-based, mAP→clearly labeled unverified aspirational or CSV-derived epoch partial only.
- **Pass Threshold**: ≥ 4
- **Evidence**: grep for bare "97.6%" outside UNVERIFIED section returns 0; XAI disclaimer in 3+ locations; "project-defined severity score" in 3+ locations.

## Open Questions
- [ ] Should model safety verifier also validate YAML class_count vs checkpoint.names class count? (Will implement yes, returns class_names_match boolean.)
- [ ] Can frontend LiveInspection URL be hardcoded to http://localhost:5000 for dev + env var fallback (VITE_BACKEND_URL)? (Yes, implement with fallback.)
