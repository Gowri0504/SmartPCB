"""
Model safety & checkpoint verification layer for SmartPCB-XAI.

Validates every model checkpoint BEFORE it is treated as production-ready:
  1. checkpoint file exists on disk
  2. checkpoint loads without exception using ultralytics YOLO()
  3. model.names (class names) match expected canonical class set (case-insensitive,
     alias-aware lookup via ai/config aliases if loaded)
  4. number of classes matches expected count
  5. device inference works (CUDA if requested, CPU fallback otherwise)
  6. architecture is reported as the YOLO variant string

Returns a dict with the following schema:
{
    "checkpoint_path": str,
    "exists": bool,
    "loads": bool,
    "architecture": str | None,
    "class_count_loaded": int | None,
    "class_count_expected": int,
    "class_names_match": bool,
    "class_names_loaded": list[str] | None,
    "class_names_expected": list[str],
    "unmapped_loaded_classes": list[str],
    "unmapped_canonical_classes": list[str],
    "canonical_mapping_status": "FULL" | "PARTIAL" | "FAIL" | "UNKNOWN",
    "device": str,
    "device_works": bool,
    "load_error": str | None,
    "status": "PASS" | "FAIL" | "BLOCKED" | "UNVERIFIED"
}

The status vocabulary is intentionally restricted to the same PASS/FAIL/BLOCKED/UNVERIFIED
vocabulary used by PHASE2_VERIFICATION.md for consistency with scientific honesty labeling.
"""

import os
from typing import List, Optional

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _canonical_lookup_alias(name: str, canonical_list: List[str]) -> Optional[str]:
    """Case-insensitive direct match. Intentionally conservative (no aliases yet)."""
    lowered = name.strip().lower()
    for c in canonical_list:
        if c.lower() == lowered:
            return c
    return None


def verify_checkpoint(
    checkpoint_path: str,
    expected_class_names: List[str],
    device: Optional[str] = None,
    alias_map: Optional[dict] = None,
) -> dict:
    """
    Verify a single YOLO checkpoint against the expected canonical class space.

    Parameters
    ----------
    checkpoint_path : str
        Absolute or relative path to the .pt file.
    expected_class_names : list[str]
        Canonical class names. Without `alias_map` these are compared
        positionally (strict). With `alias_map` they are compared as SETS of
        canonical names, because the alias layer remaps class IDs by name.
    device : str or None
        "cuda", "cpu", or None (auto-detect). If CUDA is requested but unavailable,
        fallback to CPU for device_works test (still reports actual device used).
    alias_map : dict or None
        Optional raw-class -> canonical-class mapping (see ai.config). When
        supplied, a class is "mapped" only if its raw name appears in the map,
        so genuinely unmapped labels are still reported as such.
    """
    import torch

    actual_device_input = device
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        device = "cpu"

    result = {
        "checkpoint_path": checkpoint_path,
        "exists": False,
        "loads": False,
        "architecture": None,
        "class_count_loaded": None,
        "class_count_expected": len(expected_class_names),
        "class_names_match": False,
        "class_names_loaded": None,
        "class_names_expected": list(expected_class_names),
        "unmapped_loaded_classes": [],
        "unmapped_canonical_classes": list(expected_class_names),
        "canonical_mapping_status": "UNKNOWN",
        "device_requested": actual_device_input,
        "device_used": device,
        "device_works": False,
        "load_error": None,
        "status": "UNVERIFIED",
    }

    resolved = checkpoint_path
    if not os.path.isabs(resolved):
        resolved = os.path.join(ROOT, resolved)
    result["checkpoint_resolved"] = resolved

    if not os.path.isfile(resolved):
        result["exists"] = False
        result["load_error"] = f"Checkpoint file does not exist: {resolved}"
        result["status"] = "BLOCKED"
        return result
    result["exists"] = True

    try:
        from ultralytics import YOLO
        import numpy as np
    except Exception as e:
        result["load_error"] = f"Failed to import YOLO/numpy: {e}"
        result["status"] = "BLOCKED"
        return result

    model = None
    try:
        model = YOLO(resolved)
        result["loads"] = True
    except Exception as e:
        result["loads"] = False
        result["load_error"] = f"YOLO checkpoint load exception: {e}"
        result["status"] = "FAIL"
        return result

    try:
        names_dict = model.names if hasattr(model, "names") else {}
        if isinstance(names_dict, dict):
            loaded_names = [str(names_dict.get(k, f"cls{k}")) for k in sorted(names_dict.keys())]
        else:
            loaded_names = [str(x) for x in list(names_dict)]
        result["class_names_loaded"] = loaded_names
        result["class_count_loaded"] = len(loaded_names)
    except Exception as e:
        result["load_error"] = f"Exception reading model.names: {e}"
        result["status"] = "FAIL"
        return result

    try:
        arch_str = ""
        for attr in ("ckpt_path", "task", "model_name"):
            if hasattr(model, attr):
                v = getattr(model, attr)
                if isinstance(v, str):
                    arch_str += f" {v}"
        result["architecture"] = (arch_str.strip() if arch_str.strip() else "YOLO(ultralytics)") or "YOLO(ultralytics)"
    except Exception:
        result["architecture"] = "YOLO(ultralytics)"

    expected_n = len(expected_class_names)
    loaded_n = result["class_count_loaded"] or 0
    lowered_alias = None
    if alias_map:
        lowered_alias = {str(k).strip().lower(): str(v).strip().lower()
                         for k, v in alias_map.items()}

    if lowered_alias is not None:
        # Alias-aware (set) comparison: class IDs are remapped by name at
        # inference time, so positional ordering is not meaningful here.
        mapped_loaded = [lowered_alias.get(str(n).strip().lower(), str(n).strip().lower())
                         for n in loaded_names]
        expected_lower_set = {str(c).strip().lower() for c in expected_class_names}
        result["class_names_match"] = (
            set(mapped_loaded) == expected_lower_set and len(loaded_names) > 0
        )
        result["mapped_loaded_classes"] = sorted(set(mapped_loaded))
        result["unmapped_loaded_classes"] = sorted(
            {str(n).strip().lower() for n in loaded_names
             if str(n).strip().lower() not in lowered_alias}
        )
        result["unmapped_canonical_classes"] = sorted(
            {c for c in expected_lower_set if c not in set(mapped_loaded)}
        )
    else:
        if loaded_n == expected_n:
            matches_all = True
            for idx, loaded_name in enumerate(loaded_names):
                expected_this = expected_class_names[idx] if idx < expected_n else None
                if expected_this is None:
                    matches_all = False
                    break
                matched = _canonical_lookup_alias(loaded_name, [expected_this])
                if matched is None:
                    matches_all = False
                    break
            result["class_names_match"] = matches_all
        else:
            result["class_names_match"] = False

        # Canonical-mapping audit: which loaded classes have no canonical
        # equivalent, and which canonical classes the checkpoint cannot emit.
        try:
            expected_lower = {str(c).strip().lower() for c in expected_class_names}
            loaded_lower = [str(n).strip().lower() for n in loaded_names]
            result["unmapped_loaded_classes"] = sorted(
                {n for n in loaded_lower if n not in expected_lower}
            )
            loaded_set = set(loaded_lower)
            result["unmapped_canonical_classes"] = sorted(
                {c for c in expected_lower if c not in loaded_set}
            )
        except Exception as e:
            result["load_error"] = (result["load_error"] or "") + f" mapping-audit exception: {e}"

    if not loaded_names:
        result["canonical_mapping_status"] = "FAIL"
        result["status"] = "FAIL"
        return result
    mapped_set = {str(n).strip().lower() for n in loaded_names}
    if alias_map:
        mapped_set = {lowered_alias.get(n, n) for n in mapped_set}
    expected_set = {str(c).strip().lower() for c in expected_class_names}
    if not (mapped_set & expected_set):
        # The checkpoint shares no class with the expected canonical space at
        # all — this is a wrong checkpoint, not a partially-mapped one.
        result["canonical_mapping_status"] = "FAIL"
    elif not result["unmapped_loaded_classes"] and not result["unmapped_canonical_classes"]:
        result["canonical_mapping_status"] = "FULL"
    else:
        result["canonical_mapping_status"] = "PARTIAL"

    try:
        import numpy as np
        dummy = np.zeros((64, 64, 3), dtype=np.uint8)
        _ = model.predict(source=dummy, conf=0.01, verbose=False, device=device, max_det=1)
        result["device_works"] = True
    except Exception as e:
        try:
            import numpy as np
            dummy = np.zeros((64, 64, 3), dtype=np.uint8)
            _ = model.predict(source=dummy, conf=0.01, verbose=False, device="cpu", max_det=1)
            result["device_works"] = True
            result["device_used"] = "cpu"
        except Exception as e2:
            result["device_works"] = False
            result["load_error"] = f"Device inference failed (CUDA/CPU both): primary={e}, fallback={e2}"

    if not result["device_works"]:
        result["status"] = "FAIL"
        return result
    if not result["class_names_match"]:
        result["status"] = "FAIL"
        return result
    if result["loads"] and result["exists"] and result["class_names_match"] and result["device_works"]:
        result["status"] = "PASS"
        return result
    result["status"] = "UNVERIFIED"
    return result


def taxonomy_alignment_report() -> dict:
    """
    Reconcile the DEPLOYED model class space against the CURATED dataset
    taxonomies declared in ai.config. Reported verbatim by /health and by
    COMPONENT_CLASS_SCHEMA.md / DEFECT_CLASS_SCHEMA.md.

    This does NOT load any checkpoint — it reports the declared reconciliation
    that a loaded checkpoint is then checked against.
    """
    from ai.config import (
        CURATED_COMPONENT_CLASSES, CURATED_DEFECT_CLASSES,
        DEPLOYED_COMPONENT_CLASSES, DEPLOYED_DEFECT_CLASSES,
        COMPONENT_MAPPING_STATUS, DEFECT_MAPPING_STATUS,
        COMPONENT_MAPPING_NOTE, DEFECT_MAPPING_NOTE,
        UNMAPPED_COMPONENT_CLASSES, UNDETECTABLE_CURATED_COMPONENT_CLASSES,
        DEFECT_CLASS_ALIASES, APPROXIMATE_DEFECT_ALIASES,
        DEFECT_ALIGNMENT_MODE, DEFECT_MODEL_INDEX_TO_CANONICAL,
        canonical_defect_class_by_index,
    )

    # Index decoding is authoritative: the name-level alias table also carries
    # the legacy checkpoint's raw strings, whose 'short'/'spur' entries collide
    # with canonical names and must not be applied to the deployed declaration.
    defect_mapped = {}
    for _idx, raw in enumerate(DEPLOYED_DEFECT_CLASSES):
        canon, _mapped, _ = canonical_defect_class_by_index(_idx)
        defect_mapped[raw] = canon if canon is not None else raw
    return {
        "components": {
            "deployed_model_classes": list(DEPLOYED_COMPONENT_CLASSES),
            "curated_dataset_classes": list(CURATED_COMPONENT_CLASSES),
            "mapping_status": COMPONENT_MAPPING_STATUS,
            "unmapped_model_classes": list(UNMAPPED_COMPONENT_CLASSES),
            "undetectable_curated_classes": list(UNDETECTABLE_CURATED_COMPONENT_CLASSES),
            "approximate_mappings": {},
            "note": COMPONENT_MAPPING_NOTE,
        },
        "defects": {
            "deployed_model_classes": list(DEPLOYED_DEFECT_CLASSES),
            "curated_dataset_classes": list(CURATED_DEFECT_CLASSES),
            "mapping_status": DEFECT_MAPPING_STATUS,
            "alignment_mode": DEFECT_ALIGNMENT_MODE,
            "checkpoint_name_strings_authoritative": False,
            "model_index_to_canonical": dict(DEFECT_MODEL_INDEX_TO_CANONICAL),
            "raw_to_canonical": defect_mapped,
            "approximate_mappings": dict(APPROXIMATE_DEFECT_ALIASES),
            "unmapped_model_classes": [
                raw for raw, canon in defect_mapped.items()
                if canon not in CURATED_DEFECT_CLASSES
            ],
            "undetectable_curated_classes": [
                c for c in CURATED_DEFECT_CLASSES
                if c not in set(defect_mapped.values())
            ],
            "note": DEFECT_MAPPING_NOTE,
        },
    }
