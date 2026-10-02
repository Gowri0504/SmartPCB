"""
SmartPCB-XAI — Canonical configuration, class definitions, and threshold constants.
Centralized so that ai/, ai_service/, tests/, and scripts can share one source of truth.

CLASS-TAXONOMY HONESTY (read before changing any list below)
-----------------------------------------------------------
There are two DISTINCT taxonomies in this project and they do NOT fully agree:

  1. CURATED_DATASET_*  — the taxonomies written in the on-disk dataset
     `data.yaml` files under datasets/*_curated, datasets/components,
     datasets/components_unified, datasets/defects, ...
       components : ICs, capacitors, diodes, inductors, resistors, transistors   (6)
       defects    : open, short, mousebite, spur, copper, pin-hole               (6)

  2. DEPLOYED_MODEL_*   — the class lists actually baked into the .pt
     checkpoints that this system runs (verified by reading `model.names`
     from the checkpoint, see scripts/debug/model_diagnostics.py):
       models/component_best.pt : relay, buzzer, ic, switch, battery,
                                  transistor, capacitor, resistor, led, diode  (10)
       models/defect_best.pt    : missing_hole, mouse_bite, open_circuit,
                                  short, spur, spurious_copper                 (6)

The operational (authoritative) class space is the DEPLOYED model space,
because that is what the system can actually detect and report. The curated
6-class component taxonomy is retained for dataset/training tooling only.

Component mapping status  : PARTIAL — relay, buzzer, switch, battery and led
                            have NO equivalent in the curated 6-class component
                            taxonomy, and `inductors` exists in the curated
                            taxonomy but is NOT detectable by the deployed
                            component model. Those raw labels are preserved
                            verbatim (never coerced into another class).
Defect mapping status     : FULL (by INDEX) — corrected 2026-09-23. The deployed
                            defect checkpoint emits PCB-DATASET name strings but
                            its INDEX ORDER is DeepPCB's, verified by
                            class-agnostic geometric matching on the validation
                            split (921/923 matched pairs on the diagonal, mean
                            IoU 0.899). The earlier claim that this was a
                            name-based mapping with one approximate pairing was
                            an artifact of trusting the checkpoint's name
                            strings; see DEFECT_MODEL_INDEX_TO_CANONICAL and
                            DEFECT_MAPPING_NOTE below, and the CORRECTION
                            section in DEFECT_CLASS_SCHEMA.md.

Full evidence table: COMPONENT_CLASS_SCHEMA.md / DEFECT_CLASS_SCHEMA.md.
"""

import os

PROJECT_VERSION = "1.0.0-phase1"

# ---------------------------------------------------------------------------
# 1. Curated dataset taxonomies (datasets/*/data.yaml) — dataset/training only
# ---------------------------------------------------------------------------
CURATED_COMPONENT_CLASSES = [
    "ICs",
    "capacitors",
    "diodes",
    "inductors",
    "resistors",
    "transistors",
]

CURATED_DEFECT_CLASSES = [
    "open",
    "short",
    "mousebite",
    "spur",
    "copper",
    "pin-hole",
]

# ---------------------------------------------------------------------------
# 2. Deployed model taxonomies (read from the .pt checkpoints) — operational
# ---------------------------------------------------------------------------
DEPLOYED_COMPONENT_CLASSES = [
    "relay",
    "buzzer",
    "ic",
    "switch",
    "battery",
    "transistor",
    "capacitor",
    "resistor",
    "led",
    "diode",
]

DEPLOYED_DEFECT_CLASSES = [
    "open",
    "short",
    "mousebite",
    "spur",
    "copper",
    "pin-hole",
]

# ---------------------------------------------------------------------------
# 3. Authoritative (canonical) class space used by the running system
#    Components: identity on the deployed model space — NO cross-class coercion.
#    Defects: the model's names normalized to the curated DeepPCB-style names.
# ---------------------------------------------------------------------------
CANONICAL_COMPONENT_CLASSES = list(DEPLOYED_COMPONENT_CLASSES)
CANONICAL_DEFECT_CLASSES = list(CURATED_DEFECT_CLASSES)

CANONICAL_COMPONENT_CLASS_TO_ID = {
    name: idx for idx, name in enumerate(CANONICAL_COMPONENT_CLASSES)
}

CANONICAL_DEFECT_CLASS_TO_ID = {
    name: idx for idx, name in enumerate(CANONICAL_DEFECT_CLASSES)
}

# Component classes emitted by the model that have NO equivalent in the curated
# 6-class dataset taxonomy. They are reported under their raw label and are
# explicitly flagged as unmapped — they are NEVER rewritten to another class.
UNMAPPED_COMPONENT_CLASSES = ["relay", "buzzer", "switch", "battery", "led"]

# Curated component classes that the deployed component model cannot detect.
UNDETECTABLE_CURATED_COMPONENT_CLASSES = ["inductors"]

# Curated component class -> deployed equivalent, ONLY where the mapping is
# genuinely valid (same physical device). Absent keys are intentionally unmapped.
# NOTE: `led` is deliberately NOT mapped to `capacitors` (that earlier alias was
# a mislabel and was removed 2026-09-23 — an LED is not a capacitor).
COMPONENT_CLASS_ALIASES = {
    "ics": "ic",
    "ic": "ic",
    "capacitor": "capacitor",
    "capacitors": "capacitor",
    "resistor": "resistor",
    "resistors": "resistor",
    "diode": "diode",
    "diodes": "diode",
    "transistor": "transistor",
    "transistors": "transistor",
    "relay": "relay",
    "buzzer": "buzzer",
    "switch": "switch",
    "battery": "battery",
    "led": "led",
}

# ---------------------------------------------------------------------------
# Defect model class -> canonical defect class. VERIFIED POSITIONAL ALIGNMENT.
# ---------------------------------------------------------------------------
# The deployed checkpoint models/defect_best.pt emits the class-name strings
# ['missing_hole','mouse_bite','open_circuit','short','spur','spurious_copper']
# (the PCB-DATASET taxonomy). Those strings DO NOT DESCRIBE ITS OWN INDICES.
#
# Evidence (all reproducible, 2026-09-23):
#  1. datasets/defects is a faithful conversion of DeepPCB. The upstream README
#     shipped in-tree (datasets/temp_deeppcb/README.md) defines the annotation
#     types as 1-open 2-short 3-mousebite 4-spur 5-copper 6-pin-hole, and
#     scripts/dataset/process_deeppcb.py maps type t -> index t-1. Spot-checked
#     box-for-box: upstream `77 315 110 373 1` -> local `0 0.146094 ...`, i.e.
#     type 1 (open) becomes index 0, matching data.yaml `0: open`.
#  2. Class-agnostic geometric matching (greedy by confidence, IoU>=0.5) of
#     checkpoint detections against dataset ground truth on the validation
#     split (150 images, 930 GT boxes, 923 matched pairs) puts 921/923 pairs
#     (99.8%) on the diagonal model_index == dataset_index, mean IoU 0.899.
#     Artifact: metrics/alignment/defect_val_alignment.json
#
# Consequence: the alignment is BY INDEX. Note that it cannot be expressed as a
# name->name table keyed on *dataset* names, because 'short' and 'spur' exist in
# both taxonomies at different indices. DEFECT_CLASS_ALIASES below is therefore
# keyed on the CHECKPOINT's raw strings and must never be applied to
# dataset/ground-truth names. Prefer index decoding via
# canonical_defect_class_by_index(); the name table is a fallback for callers
# that only have a string.
DEFECT_ALIGNMENT_MODE = "positional"

DEFECT_MODEL_INDEX_TO_CANONICAL = {
    0: "open",
    1: "short",
    2: "mousebite",
    3: "spur",
    4: "copper",
    5: "pin-hole",
}

DEFECT_CLASS_ALIASES = {
    "open": "open",
    "short": "short",
    "mousebite": "mousebite",
    "spur": "spur",
    "copper": "copper",
    "pin-hole": "pin-hole",
}

# No pairing is approximate any more: the pre-2026-09-23 entry
# missing_hole -> pin-hole was an artifact of name-based guessing and is now
# known to be simply wrong (the checkpoint's index 0 is DeepPCB `open`).
APPROXIMATE_DEFECT_ALIASES = {}

# Machine-readable mapping-status summary exposed through /health
COMPONENT_MAPPING_STATUS = "PARTIAL"
DEFECT_MAPPING_STATUS = "FULL"

COMPONENT_MAPPING_NOTE = (
    "Deployed component model emits 10 classes. relay/buzzer/switch/battery/led "
    "have no equivalent in the curated 6-class taxonomy and are preserved as raw "
    "labels (unmapped). 'inductors' exists in the curated taxonomy but is NOT "
    "detectable by the deployed component model."
)
DEFECT_MAPPING_NOTE = (
    "Deployed defect model (defect_best_scratch.pt) emits 6 classes with canonical "
    "DeepPCB-style names directly: open, short, mousebite, spur, copper, pin-hole. "
    "This model was trained from scratch on local data only (datasets/defects) and "
    "has no contamination ambiguity. Legacy checkpoint (defect_best_legacy.pt) used "
    "PCB-DATASET name strings with DeepPCB index order; its alignment was verified "
    "by geometric matching but is no longer in active use."
)

DEFAULT_INFERENCE_CONFIG = {
    "component_conf_threshold": 0.18,
    "defect_conf_threshold": 0.18,
    "iou_threshold": 0.45,
    "tile_size": 640,
    "tile_stride": 480,
    "large_image_downscale_max_px": 1920,
}

XAI_ATTRIBUTION_METHOD = "activation_energy_approximation"
XAI_DISCLAIMER = (
    "Not an authentic gradient-based Grad-CAM++. This visualization is a "
    "feature-map energy approximation (mean absolute channel activation) for "
    "qualitative interpretability and must not be cited as a gradient attribution proof. "
    "Part 2 will integrate true gradient-weighted Grad-CAM++."
)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def normalize_component_class(raw_name):
    """
    Map a component class name to its canonical form.

    Returns (canonical_name, is_mapped, raw_name).
    `is_mapped` is False when the raw label has no curated-taxonomy equivalent;
    in that case the raw label itself is returned unchanged (never coerced).
    """
    if raw_name is None:
        return None, True, raw_name
    lowered = str(raw_name).strip().lower()
    if lowered in COMPONENT_CLASS_ALIASES:
        return COMPONENT_CLASS_ALIASES[lowered], True, raw_name
    # Unknown label: keep verbatim, flag as unmapped.
    return raw_name, False, raw_name


def canonical_defect_class_by_index(class_id):
    """Canonical (DeepPCB) name for a defect class INDEX emitted by the deployed
    checkpoint. Alignment is positional and verified on the validation split —
    see DEFECT_MODEL_INDEX_TO_CANONICAL. Out-of-range indices are returned
    verbatim as `unknown_defect_<id>` so they can never be scored silently.
    """
    if class_id is None:
        return None, True, None
    canon = DEFECT_MODEL_INDEX_TO_CANONICAL.get(int(class_id))
    if canon is not None:
        return canon, True, f"idx{int(class_id)}"
    return f"unknown_defect_{class_id}", False, f"idx{int(class_id)}"


def normalize_defect_class(raw_name, class_id=None):
    """
    Map a defect class name to its canonical form.

    Returns (canonical_name, is_mapped, raw_name). Index decoding takes
    precedence whenever a class_id is supplied, because the deployed
    checkpoint's name strings are known to be unreliable (positional alignment,
    see DEFECT_MODEL_INDEX_TO_CANONICAL). The name-table path is a fallback for
    callers that only have a string; DEFECT_CLASS_ALIASES is keyed on the
    checkpoint's raw strings and must not be used with dataset/GT names.
    """
    if class_id is not None:
        canon, mapped, _ = canonical_defect_class_by_index(class_id)
        if mapped:
            return canon, True, raw_name
    if raw_name is None:
        return None, True, raw_name
    lowered = str(raw_name).strip().lower()
    if lowered in DEFECT_CLASS_ALIASES:
        return DEFECT_CLASS_ALIASES[lowered], True, raw_name
    return raw_name, False, raw_name
