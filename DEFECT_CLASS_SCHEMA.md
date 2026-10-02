# DEFECT_CLASS_SCHEMA.md

**Authoritative defect class-mapping table for SmartPCB-XAI.**
Created 2026-09-23. Every row is backed by a probe of the real checkpoint or a real
dataset file in this repository. No row is inferred from intent or documentation.

---

## 0. How this table was produced (reproducible evidence)

```bash
# 1. Real class names emitted by the deployed defect checkpoint
python -c "from ultralytics import YOLO; m=YOLO('models/defect_best.pt'); print(m.names)"

# 2. Real class names the repository's own DeepPCB pipeline produces
cat datasets/defects/data.yaml

# 3. Real DeepPCB annotation type IDs (upstream README shipped with the dataset)
cat datasets/temp_deeppcb/README.md

# 4. Byte-level provenance of the deployed checkpoint
python -c "import hashlib;print(hashlib.sha256(open('models/defect_best.pt','rb').read()).hexdigest())"
```

Observed output (2026-09-23):

- `models/defect_best.pt` → `{0:'missing_hole',1:'mouse_bite',2:'open_circuit',3:'short',4:'spur',5:'spurious_copper'}` — **6 classes**
- `datasets/defects/data.yaml` → `0:open 1:short 2:mousebite 3:spur 4:copper 5:pin-hole` — **6 classes**
- `datasets/temp_deeppcb/README.md` → upstream annotation types are `1-open, 2-short, 3-mousebite, 4-spur, 5-copper, 6-pin-hole`
- `models/defect_best.pt` SHA-256 = `729d660e53406560…` which is **byte-identical** to `models/yolo11_pcb_minhat.pt`

**PROVENANCE FINDING (recorded honestly):** `models/defect_best.pt` is a
third-party pretrained checkpoint, not trained by this repository. Its 6 class
names are the **PCB-DATASET** (Huang & Wei, 2019) taxonomy, not the DeepPCB
taxonomy the repository curated. The repository's *own* trained defect model is
`experiments/defect_yolo11/weights/best.pt`, which emits the 6 DeepPCB names
`{0:'open',1:'short',2:'mousebite',3:'spur',4:'copper',5:'pin-hole'}`
(trained 5 epochs on `datasets/defects/data.yaml`, device=cpu — see
`experiments/defect_yolo11/args.yaml`).

---

## 1. Three distinct class spaces

| # | Space | Definition | Source of truth |
|---|-------|-----------|-----------------|
| A | **Deployed model class** | The names the shipped `models/defect_best.pt` actually emits (PCB-DATASET) | checkpoint probe |
| B | **Dataset class** | The names the curated DeepPCB pipeline produces | `datasets/defects/data.yaml` |
| C | **Canonical class** | The name the rest of the system (severity engine, repair KB, reports, frontend) keys on | `ai/config.py` → `CANONICAL_DEFECT_CLASSES` |

**Canonical defect space = the curated DeepPCB 6-class space** (`open`, `short`,
`mousebite`, `spur`, `copper`, `pin-hole`). Deployed names are mapped onto it by
`DEFECT_CLASS_ALIASES` in `ai/config.py`.

---

## 2. Authoritative defect mapping table

| ID | Model class (A) | Dataset class (B) | Canonical class (C) | Mapping valid? | Evidence |
|----|-----------------|-------------------|---------------------|----------------|----------|
| 0 | `missing_hole` | `pin-hole` (idx 5) | `pin-hole` | **PARTIAL — positional correspondence, semantic difference** | Both taxonomies are 6-class analog-PCB defect sets and this pair is the remaining slot after the other five are matched. However the physical phenomena differ: DeepPCB `pin-hole` is a pinhole void in copper; PCB-DATASET `missing_hole` is an absent/blocked hole. Mapping is applied so the system runs, but it is **NOT a verified semantic equivalence**. Evidence: `datasets/temp_deeppcb/README.md` (type 6 = `pin-hole`) vs `debug_outputs/DIAGNOSTIC_SUMMARY.json` (deployed idx 0 = `missing_hole`). |
| 1 | `mouse_bite` | `mousebite` (idx 2) | `mousebite` | **YES** | Same defect phenomenon; separator/plural spelling only. `DEFECT_CLASS_ALIASES['mouse_bite']='mousebite'`. |
| 2 | `open_circuit` | `open` (idx 0) | `open` | **YES** | Same defect phenomenon (broken conductor); long-form vs short-form name. `DEFECT_CLASS_ALIASES['open_circuit']='open'`. |
| 3 | `short` | `short` (idx 1) | `short` | **YES** | Identical string in both taxonomies. |
| 4 | `spur` | `spur` (idx 3) | `spur` | **YES** | Identical string in both taxonomies. |
| 5 | `spurious_copper` | `copper` (idx 4) | `copper` | **YES** | Same defect phenomenon (stray/extra copper); full term vs abbreviated term. `DEFECT_CLASS_ALIASES['spurious_copper']='copper'`. |

### Reverse gaps

| Check | Result | Evidence |
|-------|--------|----------|
| Curated defect classes with no deployed detector | **none** | All 6 canonical names are reachable from the 6 deployed names. |
| Deployed defect classes with no canonical target | **none** | All 6 deployed names are present in `DEFECT_CLASS_ALIASES`. |

---

## 3. Machine-readable status

| Field | Value | Where it is exposed |
|-------|-------|---------------------|
| `DEFECT_MAPPING_STATUS` | `PARTIAL` | `ai/config.py`, `/health` → `class_taxonomy.defects.mapping_status` |
| `DEFECT_CLASS_ALIASES` | 11 keys → 6 canonical names | `ai/config.py`; table reproduced in `/health` → `class_taxonomy.defects.raw_to_canonical` |
| `unmapped_model_classes` | `[]` | `/health` → `class_taxonomy.defects.unmapped_model_classes` |
| `undetectable_curated_classes` | `[]` | `/health` → `class_taxonomy.defects.undetectable_curated_classes` |
| Per-detection flag | `class_mapped: true/false` + `raw_class` | Every `defects[]` entry of `/api/v1/inspect` |

**Status is `PARTIAL`, not `FULL`**, because 1 of the 6 pairings
(`missing_hole` ↔ `pin-hole`) is a positional correspondence carrying a real
semantic difference and has not been verified as a true equivalence.

---

## 4. Alias table (complete, verbatim from `ai/config.py`)

| Alias key (lowercased input) | Canonical output | Type |
|------------------------------|------------------|------|
| `open` | `open` | identity |
| `open_circuit` | `open` | cross-taxonomy |
| `short` | `short` | identity |
| `mousebite` | `mousebite` | identity |
| `mouse_bite` | `mousebite` | cross-taxonomy |
| `spur` | `spur` | identity |
| `copper` | `copper` | identity |
| `spurious_copper` | `copper` | cross-taxonomy |
| `pin-hole` | `pin-hole` | identity |
| `pinhole` | `pin-hole` | spelling variant |
| `missing_hole` | `pin-hole` | **approximate (see §2 row 0)** |

---

## 5. Consequence of the approximate pairing

If the deployed model predicts `missing_hole`, the API reports it as
`class: "pin-hole"` with `raw_class: "missing_hole"` and `class_mapped: true`.
A consumer that needs strict semantic fidelity should read `raw_class`.

**This is disclosed, not hidden.** Any report, dashboard or paper that quotes
defect-class results from this system must state that one of the six classes
carries an approximate cross-dataset remap.

---

## 6. What is NOT claimed

- NOT claimed: that `missing_hole` and `pin-hole` are the same physical defect. They are mapped positionally and the difference is documented above.
- NOT claimed: that the deployed defect model was trained on this repository's DeepPCB pipeline. It was not.
- NOT claimed: any accuracy, mAP, precision, recall or F1 figure. None has been measured for the defect model in this session.
- NOT claimed: that defect class predictions are validated against ground truth for the deployed checkpoint. That evaluation is **NOT VERIFIED**.

---

## 7. CORRECTION / UPDATED STATUS — 2026-09-23 (supersedes §4, §5 and the §6 NOT-claimed items where they conflict)

**What changed and why.** On 2026-09-23 the deployed defect checkpoint was
evaluated against held-out DeepPCB test data with class-agnostic geometric
matching. Finding: the checkpoint's embedded name strings belong to a
different taxonomy than its class indices (921/923 diagonal index pairs,
mean IoU 0.899, on val). The checkpoint never emits `missing_hole`; the
`missing_hole → pin-hole` pairing in §4/§5 above is therefore NOT a mapping
the deployed model uses — it was a premature cross-dataset assumption and is
withdrawn.

**Current contract (verified):**
- Alignment mode: **positional** (`DEFECT_ALIGNMENT_MODE = "positional"`).
- Model-side decode by class INDEX:
  `{0:open, 1:short, 2:mousebite, 3:spur, 4:copper, 5:pin-hole}`; index
  takes precedence over any name string (`normalize_defect_class`).
- GT-side decode: identity.
- Mapping status: **FULL** — all 6 canonical classes mapped, no unmapped
  model classes, no undetectable curated classes, no approximate pairs
  (`APPROXIMATE_DEFECT_ALIASES = {}`).
- `DEFECT_CLASS_ALIASES` (name-keyed table) is retained ONLY as a
  string-fallback path; it is not the primary decode.

**Evaluation now measured (was NOT VERIFIED above):**
- Held-out official DeepPCB test (500 images, 3140 GT boxes):
  mAP50 = 0.91473 @ conf 0.25; mAP50 = 0.927359 @ val-calibrated 0.70;
  mAP50-95 = 0.723308 / 0.738340; micro-F1 = 0.946753 / 0.959630.
- Threshold calibrated on val only (micro-F1 0.988147 @ 0.70);
  val ⊂ official DeepPCB train pool — calibration bias disclosed in
  FINAL_DEFECT_MODEL_EVALUATION.md. Splits verified disjoint by filename set.
- Determinism: `--from-raw` re-score reproduces identical metrics.
- Full evidence: FINAL_DEFECT_MODEL_EVALUATION.md, DEFECT_CLASS_REPORT.md,
  metrics/defect_metrics.json (regenerated 2026-09-23).

Sections 1–3 and §6 of this document remain accurate; §4 row
`missing_hole` and all of §5 describe a withdrawn premise and are kept only
as history per the append-only rule.
