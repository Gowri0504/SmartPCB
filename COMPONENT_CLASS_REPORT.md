# COMPONENT CLASS REPORT — 2026-09-23

Deployed model classes (10, from checkpoint `models/component_best.pt`):
relay, buzzer, ic, switch, battery, transistor, capacitor, resistor, led,
diode.

Curated dataset classes (6): ICs, capacitors, diodes, inductors, resistors,
transistors.

## Taxonomy reconciliation status: PARTIAL (name-based)

- Alignment mode: name-based via `COMPONENT_CLASS_ALIASES`
  (ic/ICs→ic, capacitor/capacitors→capacitor, etc.).
- Unmapped model classes (emit predictions with no curated equivalent):
  relay, buzzer, switch, battery, led (5).
- Undetectable curated classes: inductors (0 predictions in evaluation).
- This status is published via `/health` (`class_taxonomy.components`) and
  asserted by tests; it is honest and current.

## Verified class count

`/health` reports `class_count_loaded = 10` from the checkpoint itself
(`model.names`). An earlier test revision asserted 6 — corrected 2026-09-23
(see tests/test_fastapi_health.py note); the deployed checkpoint verifiably
emits 10 classes.

## Measured behavior

See FINAL_COMPONENT_MODEL_EVALUATION.md: test mAP50 0.09335 @0.25; recall
≤ 0.39 per class; inductors never detected; 34 predictions fall in the 5
classes that have no curated GT. Component detection is low-reliability and
must be labeled as such in any UI or report copy.
