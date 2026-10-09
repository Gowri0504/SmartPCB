import unittest
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.model_safety import verify_checkpoint, taxonomy_alignment_report
from ai.config import (
    CANONICAL_COMPONENT_CLASSES,
    CANONICAL_DEFECT_CLASSES,
    COMPONENT_CLASS_ALIASES,
    DEFECT_CLASS_ALIASES,
    DEFECT_ALIGNMENT_MODE,
    DEFECT_MODEL_INDEX_TO_CANONICAL,
    canonical_defect_class_by_index,
    normalize_defect_class,
)

ALLOWED_STATUS = {"PASS", "FAIL", "BLOCKED", "UNVERIFIED"}


class TestModelSafety(unittest.TestCase):
    def test_nonexistent_checkpoint_is_BLOCKED(self):
        r = verify_checkpoint(os.path.join(ROOT, "does_not_exist_xyz_2026.pt"),
                              ["a", "b", "c"])
        self.assertIn("status", r)
        self.assertEqual(r["status"], "BLOCKED")
        self.assertFalse(r.get("exists", True))
        self.assertFalse(r.get("loads", True))

    def test_yolo11n_COCO_vs_canonical_component6_FAIL(self):
        yolo11n = os.path.join(ROOT, "yolo11n.pt")
        if not os.path.exists(yolo11n):
            self.skipTest("yolo11n.pt baseline checkpoint not present on disk; cannot run FAIL test")
        r = verify_checkpoint(yolo11n, CANONICAL_COMPONENT_CLASSES, device="cpu")
        self.assertIn(r["status"], {"FAIL", "BLOCKED", "UNVERIFIED"})
        if r["status"] == "FAIL":
            self.assertFalse(r["class_names_match"])
            self.assertNotEqual(r["class_count_loaded"], len(CANONICAL_COMPONENT_CLASSES))

    def test_component_best_pt_schema_returns_valid_status_vocab(self):
        cp = os.path.join(ROOT, "models", "component_best.pt")
        if not os.path.exists(cp):
            self.skipTest("models/component_best.pt missing")
        r = verify_checkpoint(cp, CANONICAL_COMPONENT_CLASSES, device="cpu")
        allowed = {"PASS", "FAIL", "BLOCKED", "UNVERIFIED"}
        self.assertIn(r["status"], allowed, f"Invalid status vocab: {r['status']}")
        self.assertIn("class_names_match", r)
        self.assertIn("class_count_loaded", r)
        self.assertIn("class_count_expected", r)
        self.assertIn("device_works", r)
        self.assertTrue(r.get("exists"), f"verify_checkpoint says file does not exist for {cp}")

    def test_defect_best_pt_schema_returns_valid_status_vocab(self):
        dp = os.path.join(ROOT, "models", "defect_best.pt")
        if not os.path.exists(dp):
            self.skipTest("models/defect_best.pt missing")
        r = verify_checkpoint(dp, CANONICAL_DEFECT_CLASSES, device="cpu")
        allowed = {"PASS", "FAIL", "BLOCKED", "UNVERIFIED"}
        self.assertIn(r["status"], allowed)
        self.assertIn("class_names_match", r)
        self.assertIn("load_error", r)
        self.assertIn("checkpoint_resolved", r)

    def test_yolo11n_COCO_vs_canonical_defect6_FAIL(self):
        yolo11n = os.path.join(ROOT, "yolo11n.pt")
        if not os.path.exists(yolo11n):
            self.skipTest("yolo11n.pt baseline checkpoint not present on disk")
        r = verify_checkpoint(yolo11n, CANONICAL_DEFECT_CLASSES, device="cpu")
        self.assertIn(r["status"], {"FAIL", "BLOCKED", "UNVERIFIED"})


class TestModelSafetyAliasAware(unittest.TestCase):
    """STEP 4 — valid / missing / class-mismatch coverage with the alias layer."""

    def test_valid_component_checkpoint_passes_with_alias_map(self):
        cp = os.path.join(ROOT, "models", "component_best.pt")
        if not os.path.exists(cp):
            self.skipTest("models/component_best.pt missing")
        r = verify_checkpoint(cp, CANONICAL_COMPONENT_CLASSES, device="cpu",
                              alias_map=COMPONENT_CLASS_ALIASES)
        self.assertEqual(r["status"], "PASS", r)
        self.assertTrue(r["class_names_match"])
        self.assertEqual(r["canonical_mapping_status"], "FULL")
        self.assertEqual(r["unmapped_loaded_classes"], [])
        self.assertEqual(r["unmapped_canonical_classes"], [])
        self.assertEqual(r["class_count_loaded"], 10)
        self.assertEqual(r["class_count_expected"], 10)
        self.assertTrue(r["device_works"])

    def test_valid_defect_checkpoint_passes_with_alias_map(self):
        """Set-level check only: it proves the checkpoint's classes can be
        reconciled to the canonical space, NOT that index order is correct.
        Positional correctness is pinned by
        test_defect_positional_index_map_matches_dataset_yaml and the val
        diagnostic (921/923 diagonal pairs)."""
        cp = os.path.join(ROOT, "models", "defect_best.pt")
        if not os.path.exists(cp):
            self.skipTest("models/defect_best.pt missing")
        r = verify_checkpoint(cp, CANONICAL_DEFECT_CLASSES, device="cpu",
                              alias_map=DEFECT_CLASS_ALIASES)
        self.assertEqual(r["status"], "PASS", r)
        self.assertTrue(r["class_names_match"])
        self.assertEqual(r["canonical_mapping_status"], "FULL")
        self.assertEqual(r["unmapped_loaded_classes"], [])
        self.assertEqual(r["mapped_loaded_classes"],
                         ["copper", "mousebite", "open", "pin-hole", "short", "spur"])

    def test_coco_checkpoint_fails_class_match_under_alias_map(self):
        """A genuinely wrong checkpoint must still FAIL when an alias map is supplied."""
        yolo11n = os.path.join(ROOT, "yolo11n.pt")
        if not os.path.exists(yolo11n):
            self.skipTest("yolo11n.pt baseline not present")
        r = verify_checkpoint(yolo11n, CANONICAL_DEFECT_CLASSES, device="cpu",
                              alias_map=DEFECT_CLASS_ALIASES)
        self.assertEqual(r["status"], "FAIL", r)
        self.assertFalse(r["class_names_match"])
        self.assertEqual(r["canonical_mapping_status"], "FAIL")
        self.assertTrue(len(r["unmapped_canonical_classes"]) > 0)

    def test_missing_checkpoint_is_BLOCKED_and_never_raises(self):
        r = verify_checkpoint(
            os.path.join(ROOT, "models", "definitely_absent_2026_09_23.pt"),
            CANONICAL_DEFECT_CLASSES, device="cpu", alias_map=DEFECT_CLASS_ALIASES)
        self.assertEqual(r["status"], "BLOCKED")
        self.assertFalse(r["exists"])
        self.assertFalse(r["loads"])
        self.assertIn("does not exist", r["load_error"])

    def test_corrupt_checkpoint_fails_safely_without_raising(self):
        """A non-checkpoint file must produce FAIL/BLOCKED, never an exception."""
        bogus = os.path.join(ROOT, "tests", "_corrupt_checkpoint_probe.pt")
        try:
            with open(bogus, "wb") as f:
                f.write(b"this is not a torch checkpoint at all\x00\x01\x02")
            r = verify_checkpoint(bogus, CANONICAL_DEFECT_CLASSES, device="cpu",
                                  alias_map=DEFECT_CLASS_ALIASES)
            self.assertIn(r["status"], {"FAIL", "BLOCKED"}, r)
            self.assertFalse(r["loads"])
            self.assertIsNotNone(r["load_error"])
            self.assertNotEqual(r.get("class_names_match"), True)
        finally:
            if os.path.exists(bogus):
                os.remove(bogus)

    def test_directory_path_is_BLOCKED_not_crashed(self):
        r = verify_checkpoint(os.path.join(ROOT, "models"), ["a"])
        self.assertEqual(r["status"], "BLOCKED")
        self.assertFalse(r["exists"])


class TestTaxonomyAlignmentReport(unittest.TestCase):
    """The declared reconciliation must be internally consistent."""

    def test_report_is_json_serializable_and_consistent(self):
        import json
        rep = taxonomy_alignment_report()
        json.dumps(rep)  # must not raise
        comp, defects = rep["components"], rep["defects"]
        self.assertEqual(comp["mapping_status"], "PARTIAL")
        self.assertEqual(len(comp["deployed_model_classes"]), 10)
        self.assertEqual(len(comp["curated_dataset_classes"]), 6)
        # Defect alignment is POSITIONAL (verified 2026-09-23 on val:
        # 921/923 matched pairs on the diagonal, mean IoU 0.899). The earlier
        # name-based report claimed PARTIAL with an approximate
        # {"missing_hole": "pin-hole"} mapping — that premise was falsified.
        # With from-scratch deployment (2026-09-26), alignment is now canonical
        # names directly, but we retain the legacy alignment_mode for compatibility.
        self.assertEqual(defects["mapping_status"], "FULL")
        self.assertEqual(defects["alignment_mode"], "positional")
        self.assertIs(defects["checkpoint_name_strings_authoritative"], False)
        self.assertEqual(defects["model_index_to_canonical"],
                         {0: "open", 1: "short", 2: "mousebite",
                          3: "spur", 4: "copper", 5: "pin-hole"})
        self.assertEqual(defects["approximate_mappings"], {})
        self.assertEqual(len(defects["raw_to_canonical"]), 6)
        for canon in defects["raw_to_canonical"].values():
            self.assertIn(canon, defects["curated_dataset_classes"])
        self.assertEqual(defects["unmapped_model_classes"], [])
        self.assertEqual(defects["undetectable_curated_classes"], [])

    def test_defect_positional_index_map_matches_dataset_yaml(self):
        """Regression pin: the positional table must agree, index for index,
        with the dataset's own data.yaml ordering. If a future edit reorders
        either side, every defect metric silently re-maps — this catches it."""
        import yaml
        yaml_path = os.path.join(ROOT, "datasets", "defects", "data.yaml")
        with open(yaml_path, "r") as f:
            names = yaml.safe_load(f)["names"]
        if isinstance(names, list):
            names = {i: n for i, n in enumerate(names)}
        for idx, name in names.items():
            self.assertEqual(DEFECT_MODEL_INDEX_TO_CANONICAL.get(int(idx)), name,
                             f"positional table disagrees with data.yaml at index {idx}")
        self.assertEqual(sorted(DEFECT_MODEL_INDEX_TO_CANONICAL.keys()),
                         sorted(int(k) for k in names.keys()))

    def test_canonical_defect_class_by_index_prefers_index_over_name(self):
        # Index decoding wins even when the raw string would map elsewhere.
        self.assertEqual(canonical_defect_class_by_index(0), ("open", True, "idx0"))
        self.assertEqual(canonical_defect_class_by_index(3), ("spur", True, "idx3"))
        # Out-of-range index is surfaced verbatim, never scored silently.
        canon, mapped, raw = canonical_defect_class_by_index(17)
        self.assertEqual(canon, "unknown_defect_17")
        self.assertFalse(mapped)
        self.assertEqual(raw, "idx17")
        # None input stays a clean None.
        self.assertEqual(canonical_defect_class_by_index(None), (None, True, None))

    def test_normalize_defect_class_index_precedence(self):
        # With a class_id, the positional table decides even if the string
        # would alias to a different class ('short' in the name table is 'spur',
        # but index 1 is the dataset's 'short').
        self.assertEqual(normalize_defect_class("open", class_id=1),
                         ("short", True, "open"))
        # Index decoding is authoritative for the colliding strings too.
        self.assertEqual(normalize_defect_class("short", class_id=1),
                         ("short", True, "short"))
        self.assertEqual(normalize_defect_class("spur", class_id=3),
                         ("spur", True, "spur"))
        # String-only fallback with non-colliding canonical names is identity.
        self.assertEqual(normalize_defect_class("pin-hole"), ("pin-hole", True, "pin-hole"))
        self.assertEqual(normalize_defect_class("open"), ("open", True, "open"))
        # Canonical strings 'short'/'spur' resolve to themselves directly in the updated alias table.
        self.assertEqual(normalize_defect_class("short"), ("short", True, "short"))
        self.assertEqual(normalize_defect_class("spur"), ("spur", True, "spur"))
        # Legacy raw strings decode to their verified index-decoded canonicals.
        self.assertEqual(normalize_defect_class("missing_hole"), ("open", True, "missing_hole"))
        self.assertEqual(normalize_defect_class("mouse_bite"), ("short", True, "mouse_bite"))
        self.assertEqual(normalize_defect_class("open_circuit"), ("mousebite", True, "open_circuit"))
        self.assertEqual(normalize_defect_class("spurious_copper"), ("pin-hole", True, "spurious_copper"))

    def test_every_deployed_component_class_has_alias_entry(self):
        """No deployed component name may fall through to the raw-label path
        unnoticed: each must be an explicit key in COMPONENT_CLASS_ALIASES."""
        from ai.config import DEPLOYED_COMPONENT_CLASSES
        for name in DEPLOYED_COMPONENT_CLASSES:
            self.assertIn(name, COMPONENT_CLASS_ALIASES,
                          f"{name} missing from COMPONENT_CLASS_ALIASES")

    def test_led_is_not_mislabeled_as_capacitor(self):
        """Regression guard: `led -> capacitors` was a genuine mislabel."""
        self.assertEqual(COMPONENT_CLASS_ALIASES.get("led"), "led")
        self.assertNotEqual(COMPONENT_CLASS_ALIASES.get("led"), "capacitors")


if __name__ == "__main__":
    unittest.main()
