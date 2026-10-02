# SEVERITY & QUALITY SCORING — VERBATIM FORMULAS — 2026-09-23

Source of truth: `ai/severity/severity_engine.py` (transcribed verbatim below).
These are SmartPCB-XAI **project-defined deterministic** scores. They are NOT
the numeric scores of IPC-A-610; that standard is cited for workmanship
guidance and defect naming only.

## 1. Per-defect severity (0–100)

```
base        = DEFECT_BASE_WEIGHTS[defect_class]      # default 50.0 if unknown
crit_mult   = COMPONENT_CRITICALITY[near_component]  # default 1.0 if none/unknown
size_mult   = 1.0 + min(1.0, bbox_area_norm * 10.0)  # bbox_area_norm = bbox area / image area
raw_score   = base * crit_mult * size_mult * (0.7 + 0.3 * confidence)
score       = round(clamp(raw_score, 5.0, 100.0), 1)
```

DEFECT_BASE_WEIGHTS: short 90, open 85, pin-hole 60, mousebite 55, spur 45,
copper 35 (plus model-alias keys open_circuit 85, missing_hole 60,
mouse_bite 55, spurious_copper 35).

COMPONENT_CRITICALITY: ic(s) 1.5, transistor(s) 1.3, diode(s) 1.2,
relay 1.2, battery 1.4, switch 1.1, inductor(s) 1.1, capacitor(s) 1.0,
resistor(s) 1.0, led 1.0, buzzer 1.0.

Level bands: score >= 75 → CRITICAL; >= 50 → HIGH; >= 25 → MEDIUM; else LOW.

## 2. Board quality score (0–100)

```
penalty_sum       = Σ over defects of (severity_score / 5.0 * confidence)
overall_score     = round(clamp(100.0 - penalty_sum, 0.0, 100.0), 1)
component_integrity = round(clamp(100.0 - 4.5 * n_defects, 0.0, 100.0), 1)
```

Grade/status bands (note: code comment says 75–90 rework, <75 or any CRITICAL
fail; the implementation is authoritative):

- any CRITICAL defect OR overall < 50 → grade REJECT, status FAIL, risk CRITICAL
- overall < 75 → grade MARGINAL, status REWORK REQUIRED, risk HIGH
- overall < 90 → grade ACCEPTABLE, status PASS (ADVISORY), risk MODERATE
- else → grade EXCELLENT, status PASS, risk LOW
- zero defects → overall 100.0, EXCELLENT/PASS (early return)

## 3. Verified behavior

- 11 unit tests in tests/test_severity_engine.py cover the formulas, bands,
  KB safety notes, and fallback provenance (47/47 suite green, 2026-09-23).
- Withheld scores (REVIEW_REQUIRED / ERROR) are never fed into averages: the
  analytics route excludes non-numeric scores explicitly.
