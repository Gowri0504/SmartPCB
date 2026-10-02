# COMPONENT_CLASS_SCHEMA.md

**Authoritative component class-mapping table for SmartPCB-XAI.**
Created 2026-09-23. Every row is backed by a probe of the real checkpoint or a real
dataset file in this repository. No row is inferred from intent or documentation.

---

## 0. How this table was produced (reproducible evidence)

```bash
# 1. Real class names emitted by the deployed checkpoint
python -c "from ultralytics import YOLO; m=YOLO('models/component_best.pt'); print(m.names)"

# 2. Real class names declared by the curated dataset
cat datasets/components_curated/data.yaml

# 3. Byte-level provenance of the deployed checkpoint
python -c "import hashlib;print(hashlib.sha256(open('models/component_best.pt','rb').read()).hexdigest())"
```

Observed output (2026-09-23):

- `models/component_best.pt` → `{0:'relay',1:'buzzer',2:'ic',3:'switch',4:'battery',5:'transistor',6:'capacitor',7:'resistor',8:'led',9:'diode'}` — **10 classes**
- `datasets/components_curated/data.yaml` → `0:ICs 1:capacitors 2:diodes 3:inductors 4:resistors 5:transistors` — **6 classes**
- `models/component_best.pt` SHA-256 = `551287ef4f1e2687…` which is **byte-identical** to `models/pcb_component_jd.pt`

**PROVENANCE FINDING (recorded honestly):** `models/component_best.pt` is a
third-party pretrained checkpoint, not a model trained by this repository.
The repository's *own* trained component model is
`experiments/component_yolo11/weights/best.pt`, which emits the 6 curated classes
`{0:'ICs',1:'capacitors',2:'diodes',3:'inductors',4:'resistors',5:'transistors'}`
(trained 5 epochs on `datasets/components_unified/data.yaml`, device=cpu — see
`experiments/component_yolo11/args.yaml`). The two models are therefore *not
interchangeable* and their class spaces are different.

---

## 1. Three distinct class spaces

| # | Space | Definition | Source of truth |
|---|-------|-----------|-----------------|
| A | **Deployed model class** | The names the shipped `models/component_best.pt` actually emits | checkpoint probe |
| B | **Dataset class** | The names declared in the curated dataset yaml | `datasets/components_curated/data.yaml` |
| C | **Canonical class** | The name the rest of the system (severity engine, repair KB, reports, frontend) keys on | `ai/config.py` → `CANONICAL_COMPONENT_CLASSES` |

**Canonical component space = the deployed 10-class space** (identity, no coercion).
This is a deliberate decision: an unverified rename of a detected class would be a
fabrication, so the system preserves what the model actually said.

---

## 2. Authoritative component mapping table

| ID | Model class (A) | Dataset class (B) | Canonical class (C) | Mapping valid? | Evidence |
|----|-----------------|-------------------|---------------------|----------------|----------|
| 0 | `relay` | *(none)* | `relay` | **NO — unmapped** | No relay class exists in `components_curated/data.yaml`. Preserved as raw label. |
| 1 | `buzzer` | *(none)* | `buzzer` | **NO — unmapped** | No buzzer class in `components_curated/data.yaml`. Preserved as raw label. |
| 2 | `ic` | `ICs` (idx 0) | `ic` | **YES** | Same physical device (integrated circuit); case/spelling only. `COMPONENT_CLASS_ALIASES['ics']='ic'`. |
| 3 | `switch` | *(none)* | `switch` | **NO — unmapped** | No switch class in `components_curated/data.yaml`. Preserved as raw label. |
| 4 | `battery` | *(none)* | `battery` | **NO — unmapped** | No battery class in `components_curated/data.yaml`. Preserved as raw label. |
| 5 | `transistor` | `transistors` (idx 5) | `transistor` | **YES** | Same device family; plural→singular only. `COMPONENT_CLASS_ALIASES['transistors']='transistor'`. |
| 6 | `capacitor` | `capacitors` (idx 1) | `capacitor` | **YES** | Same device family; plural→singular only. `COMPONENT_CLASS_ALIASES['capacitors']='capacitor'`. |
| 7 | `resistor` | `resistors` (idx 4) | `resistor` | **YES** | Same device family; plural→singular only. `COMPONENT_CLASS_ALIASES['resistors']='resistor'`. |
| 8 | `led` | *(none — nearest curated class is `diodes`)* | `led` | **NO — unmapped** | An LED *is* a diode physically, but the curated model has no LED class and collapsing LED→`diode` would silently overstate what the curated taxonomy can express. The earlier `led → capacitors` alias was a **mislabel and was removed 2026-09-23**. Preserved as raw label. |
| 9 | `diode` | `diodes` (idx 2) | `diode` | **YES** | Same device family; plural→singular only. `COMPONENT_CLASS_ALIASES['diodes']='diode'`. |

### Dataset classes with NO deployed detector (reverse gap)

| Dataset class (B) | Canonical class (C) | Detectable by deployed model? | Evidence |
|-------------------|---------------------|-------------------------------|----------|
| `inductors` (idx 3) | *(none)* | **NO** | `models/component_best.pt` emits 10 classes, none of which is `inductor`/`inductors`. An inductor on the board cannot be detected or counted by the deployed component model. |

---

## 3. Machine-readable status

| Field | Value | Where it is exposed |
|-------|-------|---------------------|
| `COMPONENT_MAPPING_STATUS` | `PARTIAL` | `ai/config.py`, `/health` → `class_taxonomy.components.mapping_status` |
| `UNMAPPED_COMPONENT_CLASSES` | `["relay","buzzer","switch","battery","led"]` | `ai/config.py`, `/health` → `class_taxonomy.components.unmapped_model_classes` |
| `UNDETECTABLE_CURATED_COMPONENT_CLASSES` | `["inductors"]` | `ai/config.py`, `/health` → `class_taxonomy.components.undetectable_curated_classes` |
| Per-detection flag | `class_mapped: true/false` + `raw_class` | Every `components[]` entry of `/api/v1/inspect` |

**Status is `PARTIAL`, not `FULL`.** 5 of 10 deployed component classes cannot be
expressed in the curated 6-class dataset taxonomy, and 1 of 6 curated classes
cannot be detected at all by the deployed model.

---

## 4. Consequences that downstream consumers must accept

1. **Component counts are counts of the 10 deployed classes**, not of the curated 6. A board reported as "0 inductors" means *the model has no inductor class*, not *the board has no inductors*.
2. **Unmapped detections are not re-labelled.** `relay`, `buzzer`, `switch`, `battery`, `led` reach the API, reports and frontend under their own raw names with `class_mapped=false`.
3. **Severity criticality weights** (`ai/severity/severity_engine.py` → `COMPONENT_CRITICALITY`) contain entries for both spaces (`ics` and `ic`, `transistors` and `transistor`, …) so neither normalization path silently falls back to the 1.0 default.
4. **`relay`, `switch`, `battery`, `buzzer`, `led` criticality multipliers are project-defined choices by this project, not values taken from any published standard.**

---

## 5. What is NOT claimed

- NOT claimed: that the deployed 10-class model is equivalent to the curated 6-class model.
- NOT claimed: that `led` is a capacitor (that mapping was removed as a mislabel).
- NOT claimed: that the deployed component model was trained on this repository's curated dataset.
- NOT claimed: any accuracy, mAP, precision or recall figure. None has been measured for the component model in this session.
- NOT claimed: that `inductors` can be detected. It cannot, with the deployed checkpoint.

---

## 6. UPDATE — 2026-09-23 (evaluation now measured; supersedes the mAP NOT-claimed line above)

**Measured 2026-09-23** by `scripts/evaluation/evaluate_deployed_models.py
--model component` on the components_curated split (val 30 / test 50),
CPU: test mAP50 = 0.093346 @ conf 0.25 (0.09528 @ val-calibrated 0.15);
mAP50-95 = 0.04371; micro-F1 = 0.23196. Per-class recall ≤ 0.39; inductors
AP50 = 0.0 (never detected — the NOT-claimed line above still holds); the 5
unmapped classes (relay, buzzer, switch, battery, led) have zero curated GT
and 34 unevaluated predictions on this split. Numbers reproduced identically
by two evaluator revisions. Honest label: the deployed component detector is
LOW-RELIABILITY on the curated dataset; see FINAL_COMPONENT_MODEL_EVALUATION.md
and COMPONENT_CLASS_REPORT.md for full tables. Historical content recovery:
not applicable — this section is a pure append; nothing above was edited.

---

## 7. UPDATE — 2026-09-23 (dataset audit found systematic FICS label corruption)

**Measured 2026-09-23** by `scripts/dataset/audit_components_final.py`
(CSV-to-label box-coordinate join, all 9 FICS boards): the label files in
`datasets/processed/labels/` were generated with a WRONG class map —
resistors written as class 1 ("capacitors"), capacitors as class 2
("diodes"), diodes as class 3 ("inductors"), inductors as class 7 (out of
schema), transistors silently dropped; only ICs (class 0) is correct.
517 of 581 FICS ground-truth boxes are mislabeled and 6 are missing. The
converter on disk (`ai-model/convert_csv_to_yolo.py`) contains the correct
CLASS_MAP but was never re-run after being fixed. Consequence: every
FICS-derived annotation except ICs is wrong in `fics_tiled`,
`components_unified`, and `components_curated`, which explains the
historically failed component training runs. Full evidence and per-class
tables: `COMPONENT_DATASET_AUDIT_FINAL.md` (audit date 2026-09-23).
Remediation: regenerate FICS labels from the authoritative CSVs in the
canonical dataset build (P1-B). Pure append; nothing above was edited.
