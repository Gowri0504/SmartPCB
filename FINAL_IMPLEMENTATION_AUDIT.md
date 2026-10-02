# FINAL IMPLEMENTATION AUDIT — SmartPCB-XAI

**Audit date:** 2026-09-23
**Repository:** `D:\SmartPCB-XAI`
**Auditor:** automated audit executed inside the repository (all figures below were produced by running the code in this repo on this machine, unless explicitly marked otherwise)
**Project version string:** `1.0.0-phase1` (`ai/config.py`)

> **Reading rule for this document.** Every statement is labelled with its verification
> state. `VERIFIED` means a command was executed and its real output is quoted or
> summarized here. `NOT VERIFIED` means no evidence was obtained. `UNVERIFIABLE` means
> the evidence cannot exist on this machine (e.g. a remote training environment that is
> not accessible). No number in this document is estimated, interpolated, or carried
> over from another report.

---

## 0. Environment actually used

| Item | Value | How obtained |
|---|---|---|
| OS | Windows 10.0.26200, x64 | environment probe |
| Python | 3.13.5 | `python --version` |
| PyTorch | 2.13.0+cpu | printed by the evaluation script header |
| CUDA available | **False** (CPU-only execution) | `torch.cuda.is_available()` printed by the evaluator |
| ultralytics (installed) | 8.4.98 | package metadata |
| ultralytics (recorded inside the checkpoints) | 8.4.127 (component), 8.4.31 (defect) | read from checkpoint metadata |
| Node.js | v24.18.0 | `node --version` |
| CPU cores | 12 | environment probe |
| MongoDB | local instance required by `backend/server.js` | not exercised in this audit |

---

## 1. Module inventory (what actually exists)

### AI / inference (`ai/`)
| File | Role |
|---|---|
| `ai/config.py` | Authoritative taxonomy, alias maps, mapping-status constants |
| `ai/inference/engine.py` | Two-headed YOLO inspection engine, tiled inference, XAI orchestration, quality scoring, contract assembly |
| `ai/model_safety.py` | Checkpoint verification (exists / loads / class count / class names / canonical mapping / device / metadata) |
| `ai/severity/severity_engine.py` | Defect severity scoring + PCB quality score |
| `ai/recommendation/repair_kb.py` | Rule-Based Root-Cause Knowledge Engine (static expert-curated KB) |
| `ai/reports/report_generator.py` | PDF + Excel report generation |
| `ai/xai/gradcam.py` | Activation-based explanation maps |
| `ai/training/train_component_detector.py` | Component training entry point |
| `ai/training/train_defect_detector.py` | Defect training entry point |

### Backend (Express + Mongoose)
`backend/server.js`, `backend/models/User.js`, `backend/models/Inspection.js`, `backend/models/Feedback.js`

### Frontend (React 18 + TypeScript + Vite 6)
`frontend/src/App.tsx`, `main.tsx` and components `LiveInspection.tsx`, `ModelPerformance.tsx`, `DigitalTwin.tsx`, `AnalyticsView.tsx`, `FeedbackView.tsx`

### Scripts
`scripts/benchmark_inference.py`, `scripts/dataset/*` (7 files incl. `validate_dataset.py`), `scripts/debug/*` (5 files), `scripts/evaluation/*` (4 files)

### Tests
9 test modules under `tests/` (unittest; there is no pytest dependency)

---

## 2. Deployment reality: the shipped checkpoints are NOT products of this repository

**Status: VERIFIED.**

This is the single most important finding in the audit, because it determines which
metrics can honestly be attributed to this repository.

### 2.1 Byte-level identity

| File | MD5 |
|---|---|
| `models/component_best.pt` | `ed7db043b3dfbd2a5779c8a7794c5dae` |
| `models/pcb_component_jd.pt` | `ed7db043b3dfbd2a5779c8a7794c5dae` ← **identical** |
| `models/defect_best.pt` | `bca0be3bff217427e779782866ed16d2` |
| `models/yolo11_pcb_minhat.pt` | `bca0be3bff217427e779782866ed16d2` ← **identical** |

The deployed checkpoint is a byte-identical copy of a separately supplied file.

### 2.2 Checkpoint-internal training metadata

Read from `ckpt["train_args"]` / `ckpt["train_metrics"]` and recorded verbatim in
`metrics/component_metrics.json` → `checkpoint_provenance` and
`metrics/defect_metrics.json` → `checkpoint_provenance`.

**`models/component_best.pt`**
- `data` = `/kaggle/working/pcb_dataset/data.yaml`
- base model = `yolov10n.pt`, epochs = 30, imgsz = 1024, device = `0`
- run name = `yolov10n_pcb_augmented`, saved 2026-08-24, ultralytics 8.4.127
- self-reported on its own split: precision 0.66703, recall 0.55576, mAP50 0.60279, mAP50-95 0.40122

**`models/defect_best.pt`**
- `data` = `/kaggle/working/data_rtdetr_fixed.yaml`
- base model = `yolo11m.pt`, epochs = 50, imgsz = 640, device = `0,1`
- run name = `PCB_YOLO11_M_FINAL`, saved 2026-03-29, ultralytics 8.4.31
- self-reported on its own split: precision 0.94818, recall 0.85996, mAP50 0.9079, mAP50-95 0.57582

### 2.3 No in-repo training run produced these files

**Status: VERIFIED.** Every `best.pt` present under `experiments/` has a different MD5
and none matches the deployed pair:

| In-repo artifact | MD5 | Progress evidence |
|---|---|---|
| `experiments/component_yolo11/weights/best.pt` | `c22685eff56362e2c8065226e90bc682` | ~1 epoch (mAP50 0.01769) |
| `experiments/defect_yolo11/weights/best.pt` | `0da97d036e7e56f24fe87db9b6d7726c` | ~3 epochs (mAP50 0.291) |
| `experiments/mini_defect/weights/best.pt` | `8ce35794390121622e483f36f7e5bbc1` | 20 epochs (mAP50 0.30762, mAP50-95 0.14935) |
| `experiments/comp_fast/weights/` | — | **empty directory, no `results.csv`; `train_fast_curated.py` never completed** |

### 2.4 Consequence for documentation honesty

The two Kaggle runs advertized `mAP50 0.9079` (defect) and `mAP50 0.60279` (component)
scores on **their own** splits, using training data that is **not** present in this
repository and cannot be inspected. Those figures are recorded above only as
*self-reported provenance*, never as this repository's measured performance.

Any historical claim of "95–99% accuracy" or "97.6% / 98.2% mAP" for this system is
**NOT SUPPORTED by any artifact in this repository**. This is a documentation defect and
is addressed in the honesty pass (§8 of the roadmap; see `README.md` append of 2026-09-23).

---

## 3. Dataset state

**Status: VERIFIED** — produced by `python scripts/dataset/validate_dataset.py`, report at
`reports/dataset/validation_report.json`.

### 3.1 Component dataset (`datasets/components_unified`, 6 classes)

| Metric | Value |
|---|---|
| Images / boxes | 1013 / 33156 |
| Corrupted / decode errors | 0 / 0 |
| Empty label files | 10 (all in `train`) |
| Invalid box rows ignored | 0 |
| Splits | train 807 img / 30369 boxes · val 116 / 1549 · test 90 / 1238 |
| Class counts (total) | ICs 2253 · capacitors 13155 · diodes 2511 · inductors 620 · resistors 13386 · transistors 1231 |

Leakage and integrity checks:

| Check | Result |
|---|---|
| Board-ID cross-split leakage | **0** |
| Cross-split filename leakage | **0** |
| Exactly-duplicate image hash groups | **3 groups (7 files) — all 3 groups are entirely inside `train`** |
| Perceptual-hash (pHash) near-duplicate groups | **3** (check newly enabled this session by installing `imagehash`; previously `UNAVAILABLE`) |
| Zero-area boxes / out-of-range coords | 0 / 0 |
| Missing image↔label pairs | 0 |
| **Out-of-range class IDs** | **13 — FAIL** (see §3.3) |

### 3.2 Defect dataset (`datasets/defects`, 6 classes)

| Metric | Value |
|---|---|
| Images / boxes | 1500 / 10013 |
| Splits | train 850 / 5943 · val 150 / 930 · test 500 / 3140 |
| Class counts (total) | open 1942 · short 1506 · mousebite 1965 · spur 1625 · copper 1474 · pin-hole 1501 |
| Corrupted / empty labels / invalid rows | 0 / 0 / 0 |
| Board-ID & filename cross-split leakage | 0 / 0 |
| Duplicate hashes (exact and perceptual) | **0 / 0** |
| All 10 validator checks | **PASS** |

The defect dataset is clean on every check the validator performs.

### 3.3 Known dataset defect — 13 out-of-range class IDs (NOT fixed)

`datasets/components_unified` declares 6 classes (`0..5`) in its `data.yaml`, but label
rows referencing **class index 7** exist: **9 rows in `train`, 4 rows in `test` (13 total)**.
Independently confirmed twice — once by the dataset validator (`checks.class_ids_out_of_range`,
`pass=false`, `count=13`) and once by the model evaluator, which could not score 4 test
boxes for this reason (`class_spaces.unscorable_gt_boxes_out_of_range_class_index`).

Those 13 boxes are **unscorable by any model** and are excluded from every metric in §5.
They are an upstream data-provenance artefact; this audit does not silently repair them,
because repairing labels without knowing their intended class would itself be fabrication.

---

## 4. Class-taxonomy mapping state

**Status: VERIFIED.** Full evidence tables: `COMPONENT_CLASS_SCHEMA.md`, `DEFECT_CLASS_SCHEMA.md`.

| Aspect | State |
|---|---|
| Component mapping status | `PARTIAL` |
| Defect mapping status | `PARTIAL` |
| Canonical component space | the deployed model's own 10 classes (no cross-class coercion) |
| Canonical defect space | the curated DeepPCB-style 6 names |
| Component classes shipped by the model with no curated equivalent | `relay, buzzer, switch, battery, led` — reported under their **raw** label, never rewritten |
| Curated component class the model can never emit | `inductors` (verified: 24 GT boxes in test, 0 predictions) |
| Approximate (positional-only) defect mapping | `missing_hole → pin-hole` — disclosed via `APPROXIMATE_DEFECT_ALIASES` |
| Known mislabel removed | `led → capacitors` was wrong (an LED is not a capacitor); removed 2026-09-23 and guarded by a regression test |

`/health` reports both taxonomies as `PARTIAL`, and a test asserts it must.

---

## 5. Measured model performance on held-out local data

**Status: VERIFIED by execution.** Command:

```
python scripts/evaluation/evaluate_deployed_models.py --model both
```

Method: predictions collected at a low confidence floor (0.05), then filtered offline at
each threshold. The **`val` split is used only for threshold calibration**; the **`test`
split never influences threshold choice**. Matching is greedy per class, confidence-ordered,
IoU ≥ 0.50. AP is the all-point-interpolated (VOC/COCO-style) average.

The evaluation decodes the **model's** class names for predictions and the **dataset's**
class names for ground truth separately. This matters: an earlier revision of this script
used one shared name table, which silently mislabelled every GT box (dataset idx 0 = `ICs`
read as model idx 0 = `relay`) and collapsed all metrics toward zero. That bug was found
and fixed during this audit; the numbers below are from the corrected code, which now
refuses to emit metrics at all if it finds zero GT boxes in a split.

### 5.1 Component model — `models/component_best.pt` @ imgsz 1024

val-calibrated threshold (best micro-F1 on val) = **0.15**

| Threshold | mAP50 | mAP50-95 | micro-F1 |
|---|---|---|---|
| 0.25 (ultralytics default) | 0.0933 | 0.0437 | 0.2320 |
| 0.15 (val-calibrated) | 0.0953 | 0.0425 | 0.2444 |

Per-class on test @0.25 (only classes with GT are scored):

| Class | GT | Pred | TP | P | R | F1 | AP50 |
|---|---|---|---|---|---|---|---|
| capacitor | 536 | 391 | 116 | 0.297 | 0.216 | 0.250 | 0.076 |
| resistor | 433 | 180 | 71 | 0.394 | 0.164 | 0.232 | 0.066 |
| diode | 140 | 13 | 3 | 0.231 | 0.021 | 0.039 | 0.007 |
| ic | 82 | 33 | 18 | 0.545 | 0.220 | 0.313 | 0.158 |
| transistor | 23 | 16 | 9 | 0.563 | 0.391 | 0.462 | 0.252 |
| inductors | 24 | 0 | 0 | — | 0.000 | 0.000 | 0.000 |

**Interpretation (stated plainly):** the deployed component checkpoint performs **poorly**
on this repository's held-out component split. mAP50 ≈ 0.09. This is consistent with a
domain shift between the checkpoint's unknown Kaggle training data and
`datasets/components_unified`, and/or with the checkpoint having been trained on a
differently-defined class set. It is **not** consistent with the checkpoint's self-reported
mAP50 of 0.603, and the discrepancy is real and unexplained by anything in this repository.

### 5.2 Defect model — `models/defect_best.pt` @ imgsz 640

See `metrics/defect_metrics.json` for the generated table (same method). Cross-taxonomy note:
the checkpoint emits PCB-DATASET names (`missing_hole`, `mouse_bite`, `open_circuit`,
`short`, `spur`, `spurious_copper`) while `datasets/defects` ground truth uses DeepPCB-style
names (`open`, `short`, `mousebite`, `spur`, `copper`, `pin-hole`). Evaluation therefore
passes through the disclosed alias layer, which makes this an **approximate cross-dataset
generalization measurement**, not an exact same-taxonomy benchmark. `missing_hole → pin-hole`
is positional-only and is disclosed as such.

### 5.3 What is explicitly NOT claimed

- **No improvement-over-baseline is asserted**, because no baseline artifact exists on disk.
- **No locally-trained model performance is claimed.** The in-repo runs (§2.3) are
  incomplete and their partial metrics are not comparable to a finished model.
- **Training-set overlap with the Kaggle datasets is UNVERIFIABLE** — those datasets are
  not present here.

---

## 6. Test suite state

**Status: VERIFIED.**

```
python -m unittest discover -s tests -v
→ Ran 37 tests in 15.368s
→ OK
```

37/37 pass, exit code 0. Coverage includes: backend syntax, dataset-validator smoke,
live end-to-end, FastAPI `/health` (including canonical-class and mapping-honesty
assertions), inference engine (real + synthetic image), model safety (missing / corrupt /
directory / wrong-taxonomy / alias-aware cases plus a `led ≠ capacitor` regression guard),
report generation (real PDF + real Excel written and deleted), severity engine, and XAI smoke.

Known coverage gap: there is no test yet for the `quality_score = null`
(`REVIEW_REQUIRED`) and `inspection_status = ERROR` paths through the **report generator**.

---

## 7. Frontend / backend build state

**Status: VERIFIED.**

| Check | Command | Result |
|---|---|---|
| TypeScript typecheck | `cd frontend && npx tsc --noEmit` | exit 0, zero diagnostics |
| Production build | `cd frontend && npm run build` | SUCCESS — vite 6.4.3, 2267 modules, `index-Dkh4KhMb.js` 680.37 kB (gzip 194.97), `index-DGCGI9O_.css` 26.21 kB (gzip 5.40), 30.73 s. Only warning: >500 kB chunk advisory |
| Backend syntax | `node --check backend/server.js` | exit 0 |

---

## 8. Honesty defects found and how they were handled

| # | Defect | Evidence | Action taken |
|---|---|---|---|
| 1 | Checkpoints presented as in-repo training products | MD5 identity with `pcb_component_jd.pt` / `yolo11_pcb_minhat.pt`; Kaggle `train_args` | Documented in §2 and written into both metrics artifacts as `checkpoint_provenance.trained_in_this_repository = false` |
| 2 | "95–99% accuracy" style claims unsupported by any local measurement | no local metric artifact existed | Documented; corrected by appended CORRECTION section in the protected docs |
| 3 | Evaluator decoded GT with the model's class names | every GT class mislabelled → mAP ≈ 0.03 | Fixed; evaluator now uses two separate name tables and hard-fails on zero GT |
| 4 | Evaluator resolved the label directory with `os.sep` against a forward-slash YAML | label dir collapsed onto image dir | Fixed; path normalized and now validated with an explicit existence check |
| 5 | Macro averages polluted by model classes absent from GT | inflated/deflated means | Fixed; macro now computed only over classes with GT present, with the excluded set reported explicitly |
| 6 | 13 out-of-range GT class IDs silently dropped | validator `class_ids_out_of_range pass=false count=13` | Now surfaced in validator details and evaluator output; left unfixed in data by design (§3.3) |
| 7 | pHash duplicate check was `UNAVAILABLE` (missing dependency) | `phash_unavailable_reason: imagehash package not installed` | Resolved: `imagehash` installed, check now executes and reports real groups |
| 8 | Validator reported check counts without details for two failing checks | `details: []` | Fixed; both checks now emit per-file/per-group details |

---

## 9. Protected-file status

No git commit exists in this repository (`git log` → *your current branch 'master' does not
have any commits yet*), so **no historical content can be recovered from version control**.

`README.md`, `PROJECT_AUDIT.md`, `DATASET_REPORT.md`, `info.txt`, `project-info.txt` and
`aboutproject-info.txt` are treated as append-only. Where their existing content is stale
or wrong, a dated `CORRECTION / UPDATED STATUS` section is appended below the existing
text; existing lines are never edited or deleted.

---

## 10. Summary of module status

| Module | State |
|---|---|
| Unified inspection contract v1.0 | IMPLEMENTED, tested |
| Zero-detection safety (clean / REVIEW_REQUIRED / ERROR) | IMPLEMENTED, tested |
| Class-mapping honesty | IMPLEMENTED, tests guard the removed `led→capacitor` mislabel |
| Model safety verification layer | IMPLEMENTED, PASS on both deployed checkpoints |
| Inference engine (tiled + NMS merge) | IMPLEMENTED, exercised on real images |
| Severity / quality engine | IMPLEMENTED, tested |
| Rule-Based Root-Cause Knowledge Engine | IMPLEMENTED, tested |
| Report generator (PDF + Excel) | IMPLEMENTED, real files written and opened |
| XAI (activation-energy approximation) | IMPLEMENTED, smoke-tested |
| Component model accuracy on local data | **MEASURED — mAP50 ≈ 0.09 (poor)** |
| Defect model accuracy on local data | MEASURED — see `metrics/defect_metrics.json` |
| Component-model provenance | **NOT FROM THIS REPOSITORY (Kaggle)** — VERIFIED |
| Frontend typecheck + build | PASS |
| Backend syntax | PASS |
| Dataset integrity (defects) | PASS on all checks |
| Dataset integrity (components) | 13 out-of-range class IDs — documented, unfixed |
| Test suite | 37/37 PASS |
| Training reproduction in-repo | **NOT ACHIEVED** — runs incomplete, no finished local model |

## FINAL CONTINUATION PASS UPDATE — 2026-09-23

- Test suite: **47/47 PASS** (`python -m unittest discover -s tests`), superseding "37/37" above.
- End-to-end over real HTTP verified: upload → inspect → quality score → XAI → PDF/Excel report (file magic bytes verified).
- 20-image real validation: 20/20 SUCCESS, 104 defects, mean latency 4.07 s/image (`results/final_20_image_validation.csv`).
- Defect metrics regenerated with corrected positional alignment: mAP50 **0.91473** @0.25, **0.927359** @0.70 calibrated; component metrics mAP50 **0.093346** (LOW reliability — honest label, not hidden).
- "Training reproduction in-repo: NOT ACHIEVED" above remains true and unchanged.
