# SmartPCB-XAI Phase 2 — Implementation Plan

## Task 1: Documentation APPEND-only Corrections — PROJECT_AUDIT.md
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  1. Read full existing PROJECT_AUDIT.md.
  2. At the VERY END of the file, append a horizontal rule separator.
  3. Append heading `NEW UPDATE — 2026-09-23`.
  4. Append subsection `HISTORICAL CONTENT RECOVERY STATUS`: State repository has no git commits; the 2026-09-22 Phase-0 audit content above is preserved verbatim; corrections below are the verified state on 2026-09-23.
  5. Append subsection `CORRECTION / CLARIFICATION — 2026-09-23` listing each stale claim and actual verified state:
     - "Existing Architecture Overview → Skeleton state" → CORRECTION: Actual modules verified implemented: ai/inference, ai/xai, ai/severity, ai/reports, ai/recommendation, ai_service, backend (full routes), frontend (5-tab React TS, dist/ built), models (component_best.pt + defect_best.pt 94.9MB each), datasets (components_unified 1013, defects 1500), tests (16 passing).
     - "Existing Frontend → EMPTY" → CORRECTION: frontend/ contains React 18 TS project with 5 components (LiveInspection, DigitalTwin, AnalyticsView, FeedbackView, ModelPerformance). dist/ has built artifacts.
     - "Existing Backend → EMPTY" → CORRECTION: backend/ contains Express server with auth, inspection upload proxy, analytics, feedback, report proxies, JWT, MongoDB models (User.js, Inspection.js, Feedback.js). package.json exists.
     - "Existing AI Pipeline → Partially scaffolded NOT functional" → CORRECTION: Engine actually runs. 16 tests pass including 2 inference tests. Engine loads both .pt checkpoints successfully on CPU.
     - "Existing Datasets → Defects COMPLETELY EMPTY" → CORRECTION: datasets/defects/ contains DeepPCB with train/val/test = 850/150/500 images, 10,013 boxes total (per validate_dataset.py counts), and 6 canonical classes.
     - "Existing Trained Models → NONE" → CORRECTION: models/component_best.pt (94.9 MB) and models/defect_best.pt (94.9 MB) exist and load via YOLO(). experiments/ has 3 experiment folders with args.yaml + results.csv + plots.
     - "97.6% / 98.2% mAP claims" → CORRECTION: UNVERIFIED. No evaluation output reproduces this. Actual CSV values: component_yolo11 epoch1 mAP50=0.01769, defect_yolo11 epoch2 mAP50=0.456, mini_defect epoch4 plots available only. Full training not run.
     - Any other stale claim found.
- **Acceptance Criteria Addressed**: AC-1, AC-14
- **Test Requirements**:
  - `rule` TR-1.1: File PROJECT_AUDIT.md ends with line(s) containing "NEW UPDATE — 2026-09-23". Evidence: grep.
  - `rule` TR-1.2: Original stale claim strings still present unchanged in the file (e.g. "EMPTY" inside Frontend section AND separately inside the correction below). Evidence: grep -c "EMPTY" count ≥ 4 (original occurrences still there plus mention inside correction).

---

## Task 2: Documentation APPEND-only Corrections — DATASET_REPORT.md
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  1. Read full existing DATASET_REPORT.md.
  2. Append at bottom: horizontal rule.
  3. Append `NEW UPDATE — 2026-09-23`.
  4. Append `HISTORICAL CONTENT RECOVERY STATUS`: Same no-git note.
  5. Append `CORRECTION / CLARIFICATION — 2026-09-23` with:
     - Executive Summary actual updated table: Component Datasets Found = 8 variants (components_unified 1013 images 33156 boxes, components_curated, components, components_zip 1013 total + roboflow_remapped + fics_tiled). Defect Datasets Found = 5 variants (defects 1500 images 10013 boxes DeepPCB canonical 6 classes; defects_curated; defects_mini; temp_deeppcb raw).
     - Dataset 1 FICS: Append "Post-tiling combined distribution: fics_tiled/ has tiles; components_unified merges FICS tiles + Roboflow remapped. Total boxes 33,156 across 1,013 images."
     - Dataset 2 Roboflow: Append "Remapped via scripts/dataset/remap_roboflow.py 4,495→6 generic classes. Kept usable images only. Component classes mapped using keyword matching: capacitor→capacitors, resistor→resistors, IC/chip/microcontroller→ICs, diode/LED→diodes, inductor/transformer→inductors, transistor/MOSFET/BJT→transistors. Unmapped: battery, buzzer, connector, text labels discarded (explicitly ignored)."
     - Dataset 3 Defects (was ABSENT): CORRECTION: Present via DeepPCB at datasets/defects/. 1,500 images, 10,013 boxes. Classes: open (85), short (?), mousebite (?), spur (?), copper (?), pin-hole (?). Exact per-class counts from validate_dataset.py run referenced in Task 4 (fill in after Task 4).
     - Combined Dataset Statistics: Append "Actual components_unified splits (from validate_dataset.py): train=807 images, val=116, test=90. Defects splits: train=850, val=150, test=500."
     - Data Leakage Prevention: Append "Board-level leakage status: AWAITING Task 4 validate_dataset.py run."
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `rule` TR-2.1: "NEW UPDATE — 2026-09-23" present in DATASET_REPORT.md. Evidence: grep.
  - `rule` TR-2.2: Original "COMPLETELY ABSENT" phrase for Dataset 3 still exists above. Evidence: grep.

---

## Task 3: Documentation APPEND-only Corrections — README.md
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  1. Read full existing README.md.
  2. Append at end: horizontal rule.
  3. Append `NEW UPDATE — 2026-09-23`.
  4. Append `CORRECTION / CLARIFICATION — 2026-09-23 (Benchmark Section)`.
  5. Append a new section `## Verified vs Unverified Claims` with table:
     | Claim | Status | Verified Value / Provenance | Command / Evidence |
     |-------|--------|------------------------------|--------------------|
     | Component Detection mAP@50: 97.6% | UNVERIFIED / CLAIMED-NOT-REPRODUCIBLE | No reproducible evaluation. experiments/component_yolo11/results.csv epoch1 mAP50=0.01769 only (training not completed). | `cat experiments/component_yolo11/results.csv \| tail` |
     | Defect Detection mAP@50: 98.2% | UNVERIFIED / CLAIMED-NOT-REPRODUCIBLE | experiments/defect_yolo11/ epoch2 mAP50=0.456; mini_defect has plots but no full eval. | `cat experiments/defect_yolo11/results.csv \| tail` |
     | Inference Latency 16.1 ms | UNVERIFIED | No benchmark output. Will measure via Task 14 benchmark_inference.py. | Pending Task 14. |
     | Data Leakage 0.0% | UNVERIFIED | validate_dataset.py board-level check PENDING Task 4 execution. | Pending Task 4. |
     | Component dataset size (1013 images 33156 boxes) | VERIFIED | Task 4 validate_dataset.py counts. | Pending Task 4 fill-in. |
     | Defect dataset size (1500 images 10013 boxes) | VERIFIED | Task 4 counts. | Pending Task 4 fill-in. |
     | Python tests passing | VERIFIED | 16 tests pass in 18.4 s (CPU) on 2026-09-23. | `python -m unittest discover -s tests -v` |
     | FastAPI /health truthful | VERIFIED | TestClient returns model_loaded booleans + actual device (cpu/cuda). | tests/test_fastapi_health.py |
  6. Append subsection `SCIENTIFIC HONESTY NOTES`:
     - XAI: honestly labeled "activation_energy_approximation", not true gradient Grad-CAM++.
     - Severity/Quality scores: "SmartPCB-XAI project-defined severity score"; IPC-A-610 workmanship guidance reference only.
     - Repair KB: "Rule-Based Root-Cause Recommendation Engine"; recommendations are possible causes, not proven.
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-15
- **Test Requirements**:
  - `rule` TR-3.1: README contains "Verified vs Unverified Claims" section heading. Evidence: grep.
  - `rule` TR-3.2: README still contains original "97.6%" and "98.2%" strings in the original Benchmark section (above the append). Evidence: grep -c "97.6%" returns ≥ 1 (occurrence in old Benchmark heading preserved; correction below clarifies it).

---

## Task 4: Enhance validate_dataset.py + Run it
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  1. In `scripts/dataset/validate_dataset.py`, ADD checks WITHOUT removing existing 8:
     a. Track "empty_label_files": label file parsed with 0 valid boxes.
     b. Track "image_decode_errors": PIL Image.verify() passed but cv2.imdecode fails? Just count total "corrupted_images" field already exists → rename/add "decode_errors" if different; also add per image that opens but all zeros / wrong dtype? Skip, stick to PIL.verify + cv2 decode.
     c. Add pHash perceptual near-duplicate detection using imagehash library (if installed; else fall back to "UNAVAILABLE" with count 0 and warning in notes). For each pair of images in same dataset, pHash hamming <= 5 → near-duplicate. Implement efficient dict-based: compute pHash for each image, bucket by hash prefix 4 MSB.
     d. Track "box_count_per_image" list, compute min/max/mean/median, add to per_split JSON under box_count_per_image_stats.
  2. Add empty_label_count to per_split.
  3. Actually RUN `python scripts/dataset/validate_dataset.py`.
  4. Record actual values in memory: components board_level_cross_split_leak_count = X, defects board_level_cross_split_leak_count = Y.
  5. Go back to Task 2 DATASET_REPORT.md append section and REPLACE the "AWAITING Task 4" placeholder sentences with actual numbers. (This is APPEND-only-safe because the CORRECTION section already exists; we edit the appended correction text, not the historical original.)
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `rule` TR-4.1: validate_dataset.py exits 0. reports/dataset/validation_report.json exists.
  - `rule` TR-4.2: JSON contains checks.empty_label_files, checks.perceptual_hash_near_duplicates (or unavailable), per_split.*.empty_label_count, per_split.*.box_count_per_image_stats with min/max/mean/median.
  - `rule` TR-4.3: JSON has integer components.board_level_cross_split_leak_count (≥0) and defects.board_level_cross_split_leak_count (≥0).

---

## Task 5: Class-name consistency audit across all 8 data.yamls + check label files for invalid class IDs (class 7 etc.)
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 4 (uses validate_dataset class_id_out_of_range counts)
- **Description**:
  1. Read each of 8 data.yamls: components/, components_unified/, components_curated/, roboflow_remapped/, fics_tiled/, defects/, defects_curated/, defects_mini/.
  2. For component-type datasets, assert names matches CANONICAL_COMPONENT_CLASSES exactly.
  3. For defect-type datasets, assert names matches CANONICAL_DEFECT_CLASSES exactly.
  4. Report any mismatch in a new markdown table inside PHASE2_VERIFICATION section.
  5. Add grep-based search across all label .txt files in datasets/ for class_id values >= 6 (since canonical only 0-5). Validate_dataset.py already tracks class_ids_out_of_range; use that count plus scan for unusual class IDs (e.g. 7, 4495 etc.) in components_unified and defects label directories. Report counts, but do NOT delete or modify any labels.
- **Acceptance Criteria Addressed**: AC-11 (from Phase 1), AC-15
- **Test Requirements**:
  - `rule` TR-5.1: Python one-liner opens all 8 yamls and prints report; canonical names present exactly in 6-class datasets. Evidence: stdout.
  - `rule` TR-5.2: Class ID range scan returns integer count (could be 0) for "labels with class_id >= 6" across components_unified + defects. Actual count reported, not hardcoded.

---

## Task 6: Implement model safety / checkpoint verification layer
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  1. Create function `verify_checkpoint(checkpoint_path, expected_class_names, device="cpu")` in `ai/model_safety.py` (new file).
  2. Returns dict:
     - `path`: absolute path
     - `exists`: bool (os.path.exists)
     - `file_size_bytes`: int or None
     - `loads`: bool (YOLO() constructor succeeded)
     - `arch_name`: str (e.g. "YOLOv11n" or model.overrides['model'] if available; fallback to type(yolo.model).__name__)
     - `checkpoint_class_count`: int (len(model.names))
     - `checkpoint_class_names`: list (from model.names)
     - `expected_class_count`: int (len(expected_class_names))
     - `class_names_match`: bool (set equality case-insensitive)
     - `device_worked`: bool (inference on 1 dummy tensor succeeded on given device; CPU fallback if CUDA failed)
     - `error`: str or None
     - `status`: "PASS" if all OK; "FAIL" if any error; "BLOCKED" if file missing; "UNVERIFIED" if cannot determine
  3. In `ai_service/main.py`, import verify_checkpoint; call it for both component + defect paths during engine init.
  4. In /health response, add keys `model_status.component_model.verification = verify_dict` (same for defect).
  5. Add unit test `tests/test_model_safety.py` with:
     - verify nonexistent path → BLOCKED.
     - verify yolo11n.pt with expected COCO 80 classes → PASS.
     - verify yolo11n.pt with expected 6 canonical components classes → FAIL class_names_match False.
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `rule` TR-6.1: verify_checkpoint exists, callable. Evidence: import + call.
  - `rule` TR-6.2: /health TestClient response contains verification dict with exists, loads, status keys under both models.
  - `rule` TR-6.3: tests/test_model_safety.py 3 tests pass OK.

---

## Task 7: Add model_version + inference_timing to engine output
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: None
- **Description**:
  1. In `SmartPCBInspectionEngine.inspect()`, add `time.perf_counter()` calls around:
     - preprocess (CLAHE)
     - component inference
     - defect inference
     - xai
     - postprocess (NMS + annotations)
     - total
  2. Add to result dict: `model_version = { component: os.path.basename(component_model_path), defect: os.path.basename(defect_model_path), engine_version: PROJECT_VERSION }`
  3. Add `inference_timing = { preprocess_ms, component_inference_ms, defect_inference_ms, xai_ms, postprocess_ms, total_ms }` all floats (ms).
  4. Modify test_inference_engine.py to assert these 2 keys exist and are correct dtype.
- **Acceptance Criteria Addressed**: AC-8
- **Test Requirements**:
  - `rule` TR-7.1: synthetic inspection returns model_version (dict) and inference_timing (dict). Total > 0.
  - `rule` TR-7.2: total_ms >= component_inference_ms (approx, allow for float jitter).

---

## Task 8: Report generator ADDITIONS (old content preserved)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 7 (needs model_version + timing)
- **Description**:
  1. In `ai/reports/report_generator.py`, ADD (do not remove existing flowables):
     PDF AFTER existing recommendations section:
     a. Story.append Paragraph("4. XAI Attribution & Interpretability", section_heading). If xai in insp data → method, disclaimer, target_class, target_confidence as table. Else "No XAI computed this inspection."
     b. Story.append Paragraph("5. Inference Timing & Model Metadata", section_heading). Model versions (component/defect checkpoint names), engine version, inference_timing as formatted table.
     c. Story.append Paragraph("6. Confidence Distribution", section_heading). Defect confidences as simple bullet if ≤ 10; otherwise table of mean/median/max defect confidence.
     d. Story.append PageBreak (if reportlab available) or Spacer(12) then Paragraph("7. Limitations & Scientific Disclaimers", section_heading). Bullet list:
        - Scores: SmartPCB-XAI project-defined severity score. Not IPC-A-610 numeric score.
        - XAI: activation_energy_approximation heuristic, not true gradient Grad-CAM++.
        - Repair KB: Rule-Based Root-Cause Recommendation Engine; recommendations = possible causes, not proven.
        - Model performance: mAP figures UNVERIFIED; no full evaluation has been run.
        - Results are for AI-assisted QC review only; not a substitute for human inspector judgment.
     Excel ADD NEW SHEETS (do not delete existing 4):
     a. Severity sheet: rows from each defect with severity score/level/color/base_weight/criticality_multiplier/explanation.
     b. Model_Metadata sheet: component_model_path, defect_model_path, engine_version, device, inspection_id, timestamp, inference_timing row.
     c. Limitations sheet: each bullet above as separate row.
     d. XAI sheet: xai dict fields if present.
  2. Keep existing 4 sheet names exactly as they are.
  3. Add tests in test_reports.py or new test_reports_additions.py to verify:
     - PDF page count increased vs old (if measurable); otherwise verify PDF file size larger than test reference without sections.
     - Excel writer outputs sheets: 8 sheet names minimum, existing names still present (Inspection_Summary, Defects, Components, Repair_Procedures).
- **Acceptance Criteria Addressed**: AC-7
- **Test Requirements**:
  - `rule` TR-8.1: Excel writer produces workbook with ≥ 8 sheets; names include all 4 old + Severity, Model_Metadata, Limitations, XAI.
  - `rule` TR-8.2: Old report generation tests still pass (4 tests: PDF + Excel).
  - `rule` TR-8.3: New test assertions in reports test → ≥ 1 new test.

---

## Task 9: Repair KB honest labeling + safety_notes field (no deletions)
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: None
- **Description**:
  1. Add repair_kb.py MODULE-LEVEL DOCSTRING header: "Rule-Based Root-Cause Recommendation Engine. All recommendations are POSSIBLE CAUSES based on engineering domain knowledge, not proven causal inference. IPC-A-610 references are workmanship guidance citations only and do not assert IPC mandates numeric scores."
  2. For each of the 6 defect entries (short, open, mousebite, spur, copper, pin-hole), ADD a new key `safety_notes` with a 1-3 item list of appropriate cautions (e.g. "Always perform ESD-safe handling before rework.", "Wear safety goggles during soldering rework.", "Ensure board is powered off and discharged before any repair procedure.", "High-voltage sections: verify zero-energy state per LOTO procedure."). Assign appropriate safety notes per defect type (high-voltage concern for short more than mousebite etc.).
  3. Do NOT remove or change any existing keys in the KB entries.
  4. Add assertion test in test_severity_engine.py: RepairKnowledgeBase.get_recommendation("short") has key "safety_notes" with len > 0; all old keys still present.
- **Acceptance Criteria Addressed**: AC-9
- **Test Requirements**:
  - `rule` TR-9.1: grep "Rule-Based Root-Cause Recommendation Engine" in repair_kb.py docstring returns 1 match.
  - `rule` TR-9.2: Iterating 6 defect entries → each has "safety_notes" list, plus all 6 original keys.

---

## Task 10: Documentation APPEND — info.txt, project-info.txt, aboutproject-info.txt
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 1,2,3 (same pattern)
- **Description**:
  1. Read each file FULLY (info.txt was already partially read; read entire project-info.txt and aboutproject-info.txt).
  2. For EACH file, at the VERY END append:
     - Horizontal rule (==== or ---)
     - Heading `CORRECTION / CLARIFICATION — 2026-09-23`
     - `HISTORICAL CONTENT RECOVERY STATUS`: No git history. Original content preserved above. Below are corrections.
     - Scan each file for any occurrence of: 97.6%, 98.2%, "fully verified", "100% accuracy", "zero leakage", "official IPC score", "9/9 tests", "16ms latency" — any unverified metric claim. For each found, write a line: "Line claim: 'X' → STATUS: UNVERIFIED. Actual verified status per 2026-09-23 audit: Y."
     - Add line: "All numeric claims not independently reproduced in this 2026-09-23 audit are marked UNVERIFIED; treat as aspirational targets only."
  3. No original lines removed or modified. Only append.
- **Acceptance Criteria Addressed**: AC-1, AC-14
- **Test Requirements**:
  - `rule` TR-10.1: Each of 3 info*.txt files ends with "CORRECTION / CLARIFICATION — 2026-09-23" heading. Evidence: grep -r.
  - `rule` TR-10.2: First N lines of each file (first 50) are unchanged. Evidence: manual spot check on opening title still there.

---

## Task 11: Create 3 Dockerfiles (additive; do not modify compose)
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: None
- **Description**:
  1. Create `d:\SmartPCB-XAI\Dockerfile.ai`:
     - FROM python:3.11-slim
     - WORKDIR /app
     - COPY requirements.txt .
     - RUN pip install --no-cache-dir -r requirements.txt
     - COPY ai/ ai/
     - COPY ai_service/ ai_service/
     - COPY models/ models/
     - COPY datasets/ datasets/
     - EXPOSE 8000
     - CMD ["uvicorn", "ai_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
  2. Create `d:\SmartPCB-XAI\backend\Dockerfile`:
     - FROM node:20-alpine
     - WORKDIR /app
     - COPY package*.json ./
     - RUN npm ci --omit=dev 2>/dev/null || npm install --omit=dev
     - COPY . .
     - EXPOSE 5000
     - ENV PORT=5000 FASTAPI_URL=http://ai-service:8000 MONGO_URI=mongodb://mongodb:27017/smartpcb_xai
     - CMD ["npm", "start"]
  3. Create `d:\SmartPCB-XAI\frontend\Dockerfile`:
     - Stage 1 build: node:20-alpine, WORKDIR /app, COPY package*.json, npm ci, COPY ., npm run build.
     - Stage 2 serve: nginx:alpine, COPY dist /usr/share/nginx/html, COPY nginx.conf (optional, skip if can use default; actually create minimal nginx.conf with port 80 and try_files SPA fallback) OR comment nginx.conf needed. Actually: COPY --from=builder /app/dist /usr/share/nginx/html, EXPOSE 80, CMD ["nginx","-g","daemon off;"]. SPA fallback: optionally write a nginx.conf too. Simplify: no custom nginx.conf for now.
- **Acceptance Criteria Addressed**: AC-6
- **Test Requirements**:
  - `rule` TR-11.1: 3 Dockerfiles exist at exact paths. Each has FROM command.
  - `rule` TR-11.2: Dockerfile.ai has uvicorn CMD; backend Dockerfile has npm start; frontend Dockerfile has multi-stage.

---

## Task 12: Backend syntax check + honest package.json test script
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: None
- **Description**:
  1. Run `node --check backend/server.js`. Record exit.
  2. Read backend/package.json. Check "test" script. If it is unconditional fake success echo → change to: `"test": "node --check server.js && echo Syntax OK"` or equivalent honest script.
  3. Run `npm test --prefix backend` to ensure exit nonzero on syntax failure scenario cannot test but the command should match node --check semantics.
  4. Add test in new `tests/test_backend_syntax.py` which subprocess calls `node --check backend/server.js` and asserts returncode 0 (skip if node not found).
- **Acceptance Criteria Addressed**: AC-11
- **Test Requirements**:
  - `rule` TR-12.1: `node --check backend/server.js` exit 0.
  - `rule` TR-12.2: backend/package.json test script is not unconditionally passing.
  - `rule` TR-12.3: test_backend_syntax runs OK (or skips if node not installed).

---

## Task 13: Frontend inspection & build; API integration repair
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  1. Read frontend/src/components/LiveInspection.tsx. Check for: file upload, backend API URL, fetch/axios calls, state management (loading/error), result rendering (components/defects/severity/quality/XAI/recommendations), report download buttons.
  2. Read other 4 components briefly for obvious issues.
  3. Fix common bugs: (a) hardcoded URL localhost:5000 vs VITE_BACKEND_URL env var fallback (add import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000'). (b) Accessing result.quality_score.overall_score without optional chaining (use ?.). (c) Missing loading indicator while uploading. (d) Preview image base64 rendering. (e) PDF/Excel download report formData axios config responseType blob.
  4. Run `npm install --prefix frontend` (if no node_modules; check if exists first).
  5. Run `npm run build --prefix frontend`. Confirm vite exits 0 and dist/ regenerated.
- **Acceptance Criteria Addressed**: AC-12
- **Test Requirements**:
  - `rule` TR-13.1: npm run build exit 0.
  - `rule` TR-13.2: dist/assets contains new .js and .css files after build (hashes different if rebuild happened).
  - `rule` TR-13.3: LiveInspection.tsx uses VITE_BACKEND_URL || fallback.

---

## Task 14: Create benchmark_inference.py and run baseline
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 7 (uses timing fields; or uses its own timing)
- **Description**:
  1. Create `scripts/benchmark_inference.py`:
     - argparse: --image (str default None uses synthetic), --iterations (int default 10), --device (cpu/cuda default cpu), --conf default 0.25.
     - Creates synthetic 640x640 PCB-looking image if --image not provided (green substrate, copper shapes via numpy).
     - Instantiates SmartPCBInspectionEngine(device=args.device).
     - Warm-up run: engine.inspect(synthetic) once, discard.
     - For i in range(N): t0=perf_counter; result = engine.inspect(img); t1=perf_counter; record: (preprocess_ms if available in result else NA, component_inference_ms, defect_inference_ms, xai_ms, postprocess_ms, total_ms from result or compute). If result has no timing keys, compute external timings.
     - After iterations: compute per-field arrays → mean, median, min, max, std.
     - Print formatted table to stdout.
     - Write JSON to `reports/benchmark/inference_benchmark.json` with: device_info (cpu_brand: psutil if available, cuda_available: bool, cuda_device_name: torch.cuda.get_device_name if any), iterations, image_size, per_iteration arrays, aggregates.
     - If models cannot be loaded: print "BLOCKED: engine failed to load both models", write status BLOCKED in JSON, exit 0 (no crash).
  2. Run `python scripts/benchmark_inference.py --iterations 3 --device cpu`.
  3. Go back to README.md NEW UPDATE section and fill in the "Inference Latency 16.1 ms" row with actual measured numbers under Verified Value column.
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `rule` TR-14.1: Script exists, runs with --iterations 3, exit 0.
  - `rule` TR-14.2: reports/benchmark/inference_benchmark.json exists with mean/median/min/max/std keys and device_info dict.

---

## Task 15: Test suite expansion (dataset_val_smoke + model_safety + backend_syntax + report_additions)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Tasks 6, 8, 12
- **Description**:
  1. Create tests/test_dataset_val_smoke.py: Use tempfile.TemporaryDirectory. Build a fake dataset: train/images/synth.jpg (write a 640x640 numpy green image via cv2.imwrite), train/labels/synth.txt (0 0.5 0.5 0.1 0.1 — valid box), val/images/bad.txt invalid path case: val/images/corrupt.jpg (write a 0-byte file to trigger PIL verify fail? Actually write wrong magic bytes so PIL.verify fails). Also val/labels/oob.txt for val/images/oob.jpg: write label with w > 1.0 (2.0). Then call a modularized subset of validate_dataset (extract core validation into validate_dataset_directory() function) or directly run validate_dataset.py via subprocess on temp dir. Assertion: script returns JSON with zero_area count, class_out_of_range count, oob detection count, corrupt count correctly.
  2. Tests 6 (model safety), 8 (report additions), 12 (backend syntax) — should each add ≥1 new test file entry.
  3. Ensure total ≥ 20 tests. Run full suite.
- **Acceptance Criteria Addressed**: AC-10
- **Test Requirements**:
  - `rule` TR-15.1: discover runs ≥ 20 tests passing, 0 failures.
  - `rule` TR-15.2: test_dataset_val_smoke present and runs OK.

---

## Task 16: Run all verifications and create PHASE2_VERIFICATION.md
- **Status**: `pending`
- **Priority**: high (final)
- **Depends On**: Tasks 1-15 complete (or at least attempted)
- **Description**:
  Execute each verification step, record results:
  A. Repository audit → PASS (PROJECT_AUDIT.md corrections appended)
  B. Dataset validation → PASS/PARTIAL/FAIL based on actual validate_dataset exit
  C. Python syntax → `python -m compileall -q ai ai_service tests scripts/dataset` exit 0 → PASS
  D. Unit tests → PASS if >= 20 OK
  E. Inference smoke → PASS (result.inspection_status == "SUCCESS")
  F. XAI smoke → PASS (overlay shape correct, disclaimer present)
  G. Reports → PASS (PDF+Excel+≥8 sheets OK)
  H. FastAPI health → PASS (TestClient 200 + verification fields)
  I. Backend startup syntax → PASS (node --check exit 0)
  J. Frontend build → PASS (vite build 0)
  K. Docker → BLOCKED if daemon not running (cannot docker build); UNVERIFIED if files only
  L. Benchmark → PASS if reports/benchmark JSON exists
  M. Research Evaluation → UNVERIFIED (no evaluate.py run)
  Create file PHASE2_VERIFICATION.md with markdown table Area | Status | Evidence | Command/Test | Notes.
- **Acceptance Criteria Addressed**: AC-13
- **Test Requirements**:
  - `rule` TR-16.1: PHASE2_VERIFICATION.md exists, 12 rows minimum.
  - `rule` TR-16.2: Every Status strictly 1 of PASS/PARTIAL/FAIL/UNVERIFIED/BLOCKED.

---

## Summary of All Tasks by Priority
| ID | Task | Priority | AC |
|----|------|----------|----|
| 1 | PROJECT_AUDIT.md APPEND corrections | H | 1,14 |
| 2 | DATASET_REPORT.md APPEND corrections | H | 1 |
| 3 | README.md APPEND + Verified/Unverified section | H | 1,2,15 |
| 4 | validate_dataset.py enhancements + RUN | H | 3 |
| 5 | 8 data.yaml class-name audit + invalid ID scan | M | 11,15 |
| 6 | Model safety verifier + health exposure | H | 4 |
| 7 | Engine timing + model_version metadata | M | 8 |
| 8 | Report generator new sections/sheets | H | 7 |
| 9 | Repair KB honest label + safety_notes | M | 9 |
| 10 | info*.txt APPEND corrections | M | 1,14 |
| 11 | 3 Dockerfiles creation | M | 6 |
| 12 | Backend node syntax + honest test | M | 11 |
| 13 | Frontend API integration fix + scratch build | H | 12 |
| 14 | benchmark_inference.py + run baseline | H | 5 |
| 15 | Test suite expansion ≥20 total | H | 10 |
| 16 | Run all verifications → PHASE2_VERIFICATION table | H | 13 |
