# DEFECT CLASS REPORT — 2026-09-23

Canonical defect space (6 classes): open, short, mousebite, spur, copper,
pin-hole.

## Taxonomy reconciliation status: FULL (positional)

- Alignment mode: positional (`DEFECT_ALIGNMENT_MODE = "positional"`).
- Checkpoint name strings are unreliable; class identity is decoded from the
  class INDEX via `DEFECT_MODEL_INDEX_TO_CANONICAL`:
  `{0:open, 1:short, 2:mousebite, 3:spur, 4:copper, 5:pin-hole}`.
- Verification: class-agnostic geometric matching on val produced 921/923
  diagonal index pairs (mean IoU 0.899) — index order confirmed.
- `missing_hole → pin-hole` is NOT a mapping. The earlier PARTIAL status with
  this "approximate" pair was a disproven premise (see CORRECTION note in
  DEFECT_CLASS_SCHEMA.md append, 2026-09-23); the two names denote different
  physical phenomena and the deployed checkpoint does not emit `missing_hole`.
- Unmapped model classes: none. Undetectable curated classes: none.
- Raw-to-canonical table: 6 entries, all mapped.

## Evidence sources

- Runtime decode: `ai/config.py` (`normalize_defect_class` index precedence),
  `ai/inference/engine.py::_normalize_class_name`.
- Published via `/health` (`class_taxonomy.defects`), asserted by
  `tests/test_fastapi_health.py` and `tests/test_model_safety.py`.
- Measured quality of the decoded outputs: FINAL_DEFECT_MODEL_EVALUATION.md
  (test mAP50 0.91473 @0.25; all 6 classes present in GT; zero predicted
  classes absent from GT).

## Component counterpart

See COMPONENT_CLASS_REPORT.md — components remain PARTIAL (name-based, 5
unmapped model classes, inductors undetectable); only defects are FULL.
