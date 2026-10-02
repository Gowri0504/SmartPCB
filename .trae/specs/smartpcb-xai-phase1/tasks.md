# SmartPCB-XAI Phase 1 — Implementation Plan

## Task 1: Write accurate PROJECT_AUDIT.md (replace stale Phase-0 audit)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - Rewrite entire `PROJECT_AUDIT.md` with 8 required status categories per user spec.
  - Categorize every module: ai/, ai_service/, backend/, frontend/, datasets/, models/, experiments/, scripts/, tests/, docker/, docs.
  - Explicitly flag broken/fabricated items (XAI-noGrad, 97.6/98.2 mAP false, stale old claims, missing Dockerfiles).
  - Reference actual counts (1013 comp images, 1500 defect images, 9 passing tests) rather than old "EMPTY" claims.
- **Acceptance Criteria Addressed**: AC-1, AC-13
- **Test Requirements**:
  - `rule` TR-1.1: `PROJECT_AUDIT.md` exists and contains the 8 status categories (implemented, partial, broken, missing, claimed-not-reproducible, scientifically-questionable, technically-unnecessary, requires-user-data) as section headers or sub-headers. Evidence: grep stdout listing category names.
  - `rule` TR-1.2: Audit contains ≥1 entries under "claimed but not reproducible" that references 97.6% / 98.2% mAP claims. Evidence: grep for `97.6%` or `98.2%` inside the audit UNVERIFIED section.
- **Notes**: Overwrite (don't preserve old false audit).

## Task 2: Write accurate DATASET_REPORT.md with exact counts
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - Rewrite `DATASET_REPORT.md` with: per-dataset original/mapped classes, mapping rules from remap_roboflow.py, ignored classes, split tables (807/116/90 for components; 850/150/500 for defects), class imbalance %, corruption status, zero-area/OOB boxes, board-level split strategy (FICS s3/s4/s5 → train, s2 → val, s1 → test), and leakage proof summary.
  - Use the 2026-09-23 validate_dataset.py run output as the source of truth for counts.
- **Acceptance Criteria Addressed**: AC-2, AC-3
- **Test Requirements**:
  - `rule` TR-2.1: Component train/val/test image counts (807/116/90) appear in DATASET_REPORT.md exactly (not "approximately"). Evidence: grep.
  - `rule` TR-2.2: Defect train/val/test image counts (850/150/500) and box counts (5943/930/3140) appear exactly. Evidence: grep.
  - `rule` TR-2.3: Report documents Roboflow 4495→6 class mapping rules with keyword lists and designator regex (R-prefix for resistors etc.). Evidence: section in report matching remap_roboflow.py logic.
- **Notes**: Do NOT invent "verified 0 leakage" beyond what the script actually proves.

## Task 3: Add board-ID-level leakage validation + machine-readable JSON
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - Upgrade `scripts/dataset/validate_dataset.py` to:
    1. Extract board IDs from filenames:
       - FICS: `fics_s<N>_<name>_tile_*` → board_id = `fics_s<N>_<name>`
       - Roboflow: `robo_<PCBA_id>_*` → board_id = `robo_<PCBA_id>`
       - DeepPCB numeric prefix `<N>_test` / `<N>_temp` → board_id = `<N>`
    2. Check board IDs do not appear across train/val/test (set intersections).
    3. Add per-image md5 hash dedup check.
    4. Add machine-readable `reports/dataset/validation_report.json` with all counts, zero area, OOB boxes, class_id-range-fail, cross-split filename leaks, cross-split board leaks, image-hash-dupes.
    5. Keep existing text output + plots working.
- **Acceptance Criteria Addressed**: AC-3, AC-14
- **Test Requirements**:
  - `rule` TR-3.1: `python scripts/dataset/validate_dataset.py` exits 0 and writes a JSON file at `reports/dataset/validation_report.json`. Evidence: file exists, stdout "JSON report written".
  - `rule` TR-3.2: JSON fields: `"components.total_images":1013`, `"defects.total_boxes":10013`, `"components.board_level_cross_split_leak_count":0`, `"defects.board_level_cross_split_leak_count":0`, `"components.hash_duplicates":<int>`, `"defects.hash_duplicates":<int>`. Evidence: `jq`/python one-liner stdout.
  - `rule` TR-3.3: JSON includes check results for all 8 user-enumerated checks: duplicate_image_hashes, duplicate_filenames, board_id_overlap, split_overlap_by_filename, zero_area_boxes, normalized_coords_out_of_range, missing_image_label_pairs, class_ids_out_of_range — each as `{pass: bool, count: int, details:[...]}`. Evidence: JSON keys list.
- **Notes**: If hash dedup discovers real duplicates, keep them and report nonzero rather than silently deleting.

## Task 4: XAI — honest relabeling to approximation + sanity test + API metadata
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - Chose HONEST APPROXIMATION path (not rewrite to true gradient Grad-CAM) for Part 1, because true Grad-CAM on YOLO heads requires more research-time than Part 1 budget allows.
  - Actions:
    1. Rename `YOLOGradCAM` docstring, `gradcam.py` module docstring, and FastAPI `/inspect` response xai.attribution_method field to clearly say: `method: "activation_energy_approximation"` with `disclaimer: "Not authentic gradient-based Grad-CAM++; this is a feature-map energy visualization for interpretability."`
    2. Ensure generate_heatmap() returns structured metadata: {target_class, target_confidence, target_bbox, attribution_method, disclaimer, overlay_shape}.
    3. Add `test_xai_smoke` to unittest suite: synthetic PCB image, run engine, verify xai dict has all fields, overlay is H×W×3 uint8 with no NaN, no crash on CPU.
- **Acceptance Criteria Addressed**: AC-4, AC-10
- **Test Requirements**:
  - `rule` TR-4.1: `test_xai_smoke` test file exists and runs OK. Evidence: unittest stdout line "test_xai_smoke ... ok".
  - `rule` TR-4.2: Engine inspection xai output dict contains keys `attribution_method` and `disclaimer`, and `attribution_method != "gradcam++"` (must honestly say approximation). Evidence: Python one-liner asserting the keys.
- **Notes**: Keep the visualization code working; only the labeling and metadata need be correct.

## Task 5: Fix severity/quality claims + centralize constants
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: None
- **Description**:
  - In `severity_engine.py`, replace overclaiming strings:
    - "meets IPC-A-610 Class 3 acceptance standards" → remove sentence or rewrite to "no defects detected; refer to IPC-A-610 for workmanship acceptance guidance."
    - Add module-level docstring label: `SmartPCB-XAI project-defined severity score` (string).
    - For canonical consistency, add a `CANONICAL_COMPONENT_CLASSES` / `DEFECT_CLASSES` dict importable from a small central location (e.g. new `ai/config.py`) so engine / xai / severity / reports all read same class names.
    - Keep scoring math exactly as-is (deterministic); only docs/strings.
  - Add DEVELOPMENT-ONLY label in `backend/server.js` line ~19 JWT_SECRET hardcoded fallback.
- **Acceptance Criteria Addressed**: AC-10, AC-11, AC-14
- **Test Requirements**:
  - `rule` TR-5.1: `grep -r "project-defined severity score" ai/` returns ≥2 matches (docstring + code comment or string). Evidence: grep stdout.
  - `rule` TR-5.2: String `meets IPC-A-610 Class 3 acceptance standards` no longer appears literally in severity_engine.py (or anywhere as a score mandate). Evidence: grep count=0.
  - `rule` TR-5.3: New `ai/config.py` exports CANONICAL_COMPONENT_CLASSES list and CANONICAL_DEFECT_CLASSES list of length 6 each. Evidence: Python import assert.

## Task 6: FastAPI /health truthful reporting + TestClient health test
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 4 (optional, but nice to show XAI status in health)
- **Description**:
  - In `ai_service/main.py`:
    1. Rewrite `/health` to actually query:
       - `status` = "ok" if both models and engine loaded else "degraded"
       - `model_status.component_model` = {path, loaded: bool, classes: list}
       - `model_status.defect_model` = same
       - `model_status.xai_engine` = {method: str, disclaimer: str}
       - `device` = actual `torch.device` str, not hardcoded "cpu"
       - `version` = actual package/source version (e.g. from app version constant)
    2. Add test file `tests/test_fastapi_health.py` using `fastapi.testclient.TestClient` that calls GET /health and asserts status 200 + contains the above keys.
- **Acceptance Criteria Addressed**: AC-6, AC-7, AC-14
- **Test Requirements**:
  - `rule` TR-6.1: `test_fastapi_health.py` runs OK. Evidence: unittest stdout "test_health_endpoint ... ok".
  - `rule` TR-6.2: /health JSON response has top-level keys `status`, `model_status`, `device`, `version`, and `model_status.component_model.loaded` is bool. Evidence: TestClient json dump.
  - `rule` TR-6.3: Device value is either `cpu` or `cuda:0` (actual) — never a hardcoded string from constants independent of `torch.cuda.is_available()`. Evidence: source code inspection shows `device` = actual engine device attribute.

## Task 7: Correct README + info txt docs (fix fabricated mAP + Verified/Unverified section)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1, Task 2
- **Description**:
  - Rewrite `README.md` lines that claim "Component Detection mAP@50: 97.6%", "Defect Detection mAP@50: 98.2%", "Inference Latency: 16.1ms". Replace with inline references to the new section "Verified vs Unverified Claims".
  - Add new README section "Verified vs Unverified Claims" listing:
    - Verified: 1013 component images/33156 boxes, 1500 defect images/10013 boxes, 9/9 tests pass (now growing), models load.
    - UNVERIFIED/CLAIMED: 97.6% and 98.2% mAP50, 16.1ms latency, "0.0% Data Leakage" filename-only.
    - KNOWN-LIMITED: existing component detector epoch1 mAP50=0.018, defect epoch2 mAP50=0.456 (mini_defect has plots but results.csv only shows first 4 epochs).
  - Audit/update `info.txt`, `project-info.txt`, `aboutproject-info.txt` for same claims, or at minimum mark fabricated numbers as UNVERIFIED inline.
- **Acceptance Criteria Addressed**: AC-5, AC-1, FR-12
- **Test Requirements**:
  - `rule` TR-7.1: README contains "Verified vs Unverified Claims" section header. Evidence: grep.
  - `rule` TR-7.2: No bare (unqualified) `97.6%` or `98.2%` standalone numeric claims outside of the UNVERIFIED section. Evidence: grep with context showing any occurrence is inside the UNVERIFIED list.

## Task 8: Backend syntax check + honest test setup
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: None
- **Description**:
  - Run `node --check backend/server.js` for pure syntax verification.
  - Keep `backend/package.json` test script honest: either remove the console.log fake pass or replace with a node -c syntax check that returns nonzero on failure. Minimum: set test script to `node --check server.js` (from backend dir) so `npm test` returns 0/1 based on syntax. Document BLOCKED in PHASE1 table if MongoDB connectivity cannot be tested (expected).
- **Acceptance Criteria Addressed**: AC-8, AC-13
- **Test Requirements**:
  - `rule` TR-8.1: `node --check backend/server.js` exits 0. Evidence: terminal stdout with no errors.
  - `rule` TR-8.2: `backend/package.json` test script does not unconditionally print "All tests passed". Evidence: cat package.json.

## Task 9: Run frontend production build (npm install + npm run build)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - If `frontend/node_modules/` missing, run `npm ci` or `npm install` inside d:\SmartPCB-XAI\frontend.
  - Then run `npm run build`. Expect dist/ to be regenerated with no TS errors.
- **Acceptance Criteria Addressed**: AC-9
- **Test Requirements**:
  - `rule` TR-9.1: `npm run build` exits 0. Evidence: vite stdout lines "✓ X modules transformed", "built in ...".
  - `rule` TR-9.2: `frontend/dist/assets/` contains ≥2 files (js bundle + css). Evidence: ls stdout.

## Task 10: Run Python full syntax+import checks on entire ai/ + ai_service/
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 5 (imports ai/config)
- **Description**:
  - For all .py files under ai/, ai_service/, tests/, scripts/dataset/ run `python -m py_compile <file>` one-shot via discover equivalent (or `python -m compileall`).
  - Also run full `python -m unittest discover -s tests -p "test_*.py" -v` and record final count.
- **Acceptance Criteria Addressed**: AC-6, FR-11
- **Test Requirements**:
  - `rule` TR-10.1: `python -m compileall -q ai ai_service tests scripts/dataset` exits 0. Evidence: no output to stderr.
  - `rule` TR-10.2: Full unittest discover runs exit 0 with ≥11 tests passing (original 9 + Task 4 xai + Task 6 fastapi). Evidence: final line "Ran N tests in ...s\nOK".

## Task 11: Write PHASE1_VERIFICATION.md with A–J table
- **Status**: `pending`
- **Priority**: high (final)
- **Depends On**: Tasks 1–10 (at least attempted)
- **Description**:
  - Execute or re-execute each of the 10 required verification substeps (A repo audit, B dataset validation, C Python syntax, D unit tests, E inference smoke, F XAI smoke, G reports, H FastAPI health, I backend health syntax, J frontend build).
  - Create file `PHASE1_VERIFICATION.md` with one markdown table with columns: Component, Status, Evidence, Command/Test, Notes.
  - Status vocabulary ONLY from {PASS, PARTIAL, FAIL, UNVERIFIED, BLOCKED}.
  - Add notes column explaining BLOCKED reasons (e.g. "MongoDB not running" or "Docker daemon unavailable" if docker build attempted).
- **Acceptance Criteria Addressed**: AC-12, FR-13
- **Test Requirements**:
  - `rule` TR-11.1: `PHASE1_VERIFICATION.md` exists and has a single markdown table containing rows for all 10 verifications (A–J per user spec 22 Final Verification). Evidence: file listing + md table parse showing ≥10 rows.
  - `rule` TR-11.2: Every row's Status field exactly matches one of the 5 allowed words (case-insensitive ok but prefer all-caps). Evidence: manual reading; grep for disallowed words fails.

## Task 12: Class-name consistency audit + fixes
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 5 (for ai/config centralization)
- **Description**:
  - Read all 8+ data.yamls and compare against canonical lists. Confirm class names and order. Report any mismatch in audit, or actually rename if mismatch is non-breaking. (Expected: names already canonical per earlier read.)
  - Ensure inference engine `.names` references align (engine.py may currently rely on model.names — add fallback canonical list via ai/config so if model.names is wrong we still use expected canonical in output JSON).
- **Acceptance Criteria Addressed**: AC-11, AC-14
- **Test Requirements**:
  - `rule` TR-12.1: Python one-liner that opens each data.yaml and asserts component class list equals ["ICs","capacitors","diodes","inductors","resistors","transistors"] (for component datasets), and defect class list equals ["open","short","mousebite","spur","copper","pin-hole"]. Evidence: stdout OK.
  - `rule` TR-12.2: Engine fallback canonical_name() function exists (or equivalent) so that even if a model checkpoint has wrong .names, the inspection output JSON uses canonical names. Evidence: source + test on synthetic using COCO fallback to check mapping triggers if mismatch.
