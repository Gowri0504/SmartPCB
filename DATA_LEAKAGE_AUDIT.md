# DATA LEAKAGE AUDIT — SmartPCB-XAI

**Audit date:** 2026-09-23
**Scope:** `datasets/components_unified`, `datasets/defects`, the deployed checkpoints in
`models/`, and the relationship between them.
**Method:** all figures produced by running `scripts/dataset/validate_dataset.py` on this
machine; raw output in `reports/dataset/validation_report.json`.

---

## 1. Headline verdict

| Question | Answer |
|---|---|
| Is there split leakage **inside** the local datasets? | **No** — board-ID and filename cross-split leakage are both **0** for both datasets, and every duplicate-image group is confined within `train`. |
| Can leakage **between the deployed checkpoints and the local datasets** be ruled out? | **No — UNVERIFIABLE.** The checkpoints were trained in a remote Kaggle environment whose datasets are not present in this repository. |
| Are the model metrics in `metrics/*.json` therefore "clean" test metrics? | They are honest metrics **on this repository's test splits**, but they are **generalization metrics across an unknown domain boundary**, not same-distribution held-out metrics. See §4. |

---

## 2. Local dataset leakage checks — components (`datasets/components_unified`)

1013 images / 33156 boxes. Splits: train 807 / val 116 / test 90.

| Check | Count | Pass | Note |
|---|---|---|---|
| Board-ID cross-split leakage | **0** | ✅ | train-val 0, train-test 0 |
| Cross-split filename leakage | **0** | ✅ | train-val 0, train-test 0 |
| Exactly-duplicate image hashes (MD5) | 7 files in 3 groups | ❌ reported | **All 3 groups lie entirely within `train`** — see §2.1 |
| Perceptual-hash (pHash) near-duplicates | 3 groups | ❌ reported | `imagehash` installed 2026-09-23; check ran for the first time |
| Zero-area boxes | 0 | ✅ | |
| Normalized coords out of range | 0 | ✅ | |
| Missing image↔label pairs | 0 | ✅ | |
| **Out-of-range class IDs** | **13** | ❌ | 9 in `train`, 4 in `test`; index 7 against a 6-class yaml — see §2.2 |
| Corrupted / undecodable images | 0 | ✅ | |
| Empty label files | 10 | ✅ (reported as informational) | all in `train` |

### 2.1 Duplicate groups are intra-train only (this is the leakage-relevant fact)

Every duplicate group was resolved to its file paths and its splits extracted:

| Group | Members | Splits involved |
|---|---|---|
| 1 | 6 FICS tile images (`fics_s4_s4_*`, `fics_s5_s5_*`) | **train only** |
| 2 | `robo_ACM-109_Top_jpg.rf.339cb65b…` + `…35b7f6bc…` | **train only** |
| 3 | `robo_Arty_Bottom_jpg.rf.5989b38b…` + `…b4f6314c…` | **train only** |

Because no group spans a split boundary, duplicate content **does not** leak validation or
test images into training. Impact on reported metrics: none attributable to duplication.

Context worth recording: the FICS group consists of windowed tiles cut from larger board
photographs. Tiles from the *same physical board* being mutually near-identical is expected
behaviour of the tiling pipeline (`scripts/dataset/tile_images.py`), and board-ID leakage —
the check that would catch a whole board straddling splits — is **0**.

### 2.2 The 13 out-of-range class IDs (a real data defect, not leakage)

`datasets/components_unified/data.yaml` declares exactly 6 classes (`0..5`). However:

| Split | Rows with class index 7 | Total boxes in split |
|---|---|---|
| train | 9 | 30369 |
| val | 0 | 1549 |
| test | 4 | 1238 |
| **total** | **13** | — |

Detected independently twice:
1. `validate_dataset.py` → `checks.class_ids_out_of_range = {pass: false, count: 13}`
2. `evaluate_deployed_models.py` → could not score 4 test boxes and reported them under
   `class_spaces.unscorable_gt_boxes_out_of_range_class_index`

**Why this is not leakage:** these boxes cannot be matched by any model, so they inflate the
*denominator* of recall (they are permanent false negatives) rather than leaking training
information into test. Their effect on the component model's measured recall is therefore
**pessimistic**, not optimistic — the true recall is very slightly *better* than reported.

**Why it is left unfixed:** index 7 has no defined meaning in a 6-class taxonomy. Assigning
them to a class would be inventing ground truth. They are disclosed instead.

**Root-cause note:** 7 is a plausible residue of a 10-class Roboflow export being merged into
a 6-class schema by `scripts/dataset/merge_component_datasets.py`. This is a hypothesis about
provenance, **NOT VERIFIED**.

---

## 3. Local dataset leakage checks — defects (`datasets/defects`)

1500 images / 10013 boxes. Splits: train 850 / val 150 / test 500.

| Check | Count | Pass |
|---|---|---|
| Board-ID cross-split leakage | **0** | ✅ |
| Cross-split filename leakage | **0** | ✅ |
| Exactly-duplicate image hashes | **0** | ✅ |
| Perceptual-hash near-duplicates | **0** | ✅ |
| Zero-area boxes | 0 | ✅ |
| Normalized coords out of range | 0 | ✅ |
| Missing image↔label pairs | 0 | ✅ |
| Out-of-range class IDs | 0 | ✅ |
| Corrupted / undecodable images | 0 | ✅ |
| Empty label files | 0 | ✅ |

**All ten checks pass.** This dataset is clean. Every PCB in this dataset is a distinct board
(850 / 150 / 500 unique board IDs per split), so the split is board-disjoint by construction.

---

## 4. The leakage that CANNOT be ruled out: checkpoint ↔ local data overlap

**Status: UNVERIFIABLE on this machine.** This is the most consequential limitation in the
entire audit and it must not be glossed over.

### 4.1 What is known (VERIFIED)

The deployed checkpoints were trained outside this repository, against datasets that are not
present here:

| Checkpoint | `train_args.data` |
|---|---|
| `models/component_best.pt` | `/kaggle/working/pcb_dataset/data.yaml` |
| `models/defect_best.pt` | `/kaggle/working/data_rtdetr_fixed.yaml` |

Both paths point into a Kaggle working directory. Neither file exists in this repository.
`checkpoint_provenance.trained_in_this_repository = false` is now written into both metrics
artifacts so the fact travels with the numbers.

The local datasets are visually and taxonomically related to those Kaggle datasets:

- `datasets/defects` is derived from **DeepPCB** (`scripts/dataset/process_deeppcb.py`).
- The defect checkpoint emits **PCB-DATASET** class names
  (`missing_hole, mouse_bite, open_circuit, spur, spurious_copper, short`).
- DeepPCB and the PCB-DATASET family are both public analog-PCB defect sets that are known
  to share imagery in the wild.

### 4.2 What is therefore unknown

If the checkpoint's Kaggle training set contained any of the images that appear in this
repository's `val` or `test` splits, then the metrics in `metrics/defect_metrics.json` and
`metrics/component_metrics.json` are **train-contaminated** and overstate generalization.

**This cannot be tested here.** It would require the Kaggle training manifests, which are
absent. It is recorded as an open, unresolvable limitation, not as a passed check.

### 4.3 How the reported numbers are therefore framed

Being precise about what the §5 numbers in `FINAL_IMPLEMENTATION_AUDIT.md` mean:

- They are **honest measurements of what the deployed checkpoint does to this repository's
  images.** The measurement itself is not in doubt.
- They are **NOT** clean same-distribution held-out metrics, because the training corpus is
  unknown. They should be read as an **approximate cross-dataset generalization evaluation**.
- Since the measured component mAP50 (≈ 0.09) is *far below* the checkpoint's self-reported
  0.603, contamination is unlikely to be inflating the component number. For the defect
  model the same argument is weaker, and the reader should treat its numbers as an upper
  bound on generalization rather than a clean estimate.

---

## 5. Leakage risk in the evaluation code path

The evaluator itself was audited for the classic leakage mistakes:

| Risk | Status |
|---|---|
| Threshold tuned on test | **Avoided by construction.** The sweep iterates only over val records; the test set is then scored at both the ultralytics default (0.25) and the val-calibrated value. |
| Test images influencing class space | **Avoided.** `eval_space` derives from the taxonomy constants and the dataset yaml only. |
| Labels decoded with model class names | **Was a real bug, now fixed** — see `FINAL_IMPLEMENTATION_AUDIT.md` §8 item 3. |
| Metrics computed from an empty GT set | **Now impossible:** the evaluator raises `SystemExit` if a split yields zero GT boxes. |

---

## 6. Summary

| Datum | Value |
|---|---|
| Local split leakage (components) | **0** — clean |
| Local split leakage (defects) | **0** — clean |
| Duplicate-image leakage across splits | **0** — all groups intra-`train` |
| Component dataset defects found | 13 out-of-range class IDs; 10 empty labels; 3 duplicate groups (train-internal) |
| Defect dataset defects found | none — all 10 checks pass |
| **Checkpoint ↔ local data overlap** | **UNVERIFIABLE** — remote Kaggle training data absent |
| Metrics contamination risk | Cannot be excluded for the defect model; recorded as an open limitation |
| pHash check | Now **executing** (previously UNAVAILABLE); 3 groups components, 0 defects |

## UPDATE — 2026-09-23 (final continuation pass)

Split-disjointness verification reproduced with ASCII-safe tooling:

- Board-ID / filename cross-split overlap: **0** for both datasets (train/val/test filename sets are mutually disjoint).
- pHash near-duplicate groups: 3 groups in components, all intra-`train`; 0 in defects — no cross-split duplicate leakage.
- Known calibration bias (disclosed; not classic leakage): the local 150-image validation split is drawn from the official DeepPCB **train** pool, so threshold calibration on val is optimistic relative to a fresh-distribution test set. Headline test metrics are computed on the official held-out 500-image test split.
