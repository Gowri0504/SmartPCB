import unittest
from ai.severity.severity_engine import SeverityEngine
from ai.recommendation.repair_kb import RepairKnowledgeBase

class TestSeverityAndRepair(unittest.TestCase):
    def test_defect_severity_calculation(self):
        # High-risk defect (short) near critical component (IC)
        res = SeverityEngine.calculate_defect_severity(
            defect_class="short",
            confidence=0.95,
            bbox_area_norm=0.02,
            near_component="ICs"
        )
        self.assertIn("score", res)
        self.assertIn("level", res)
        self.assertEqual(res["level"], "CRITICAL")
        self.assertGreaterEqual(res["score"], 75.0)

    def test_low_risk_defect_severity(self):
        # Low-risk defect (copper) away from critical components
        res = SeverityEngine.calculate_defect_severity(
            defect_class="copper",
            confidence=0.60,
            bbox_area_norm=0.001,
            near_component=None
        )
        self.assertEqual(res["level"], "MEDIUM")
        self.assertLess(res["score"], 50.0)

    def test_pcb_quality_score_clean(self):
        # Zero defects -> perfect 100
        res = SeverityEngine.calculate_pcb_quality_score(defects=[], total_components=25)
        self.assertEqual(res["overall_score"], 100.0)
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["grade"], "EXCELLENT")

    def test_pcb_quality_score_defective(self):
        defects = [{
            "id": "D-1",
            "class": "short",
            "confidence": 0.95,
            "severity": {"score": 85.0, "level": "CRITICAL"}
        }]
        res = SeverityEngine.calculate_pcb_quality_score(defects=defects, total_components=10)
        self.assertLess(res["overall_score"], 90.0)
        self.assertEqual(res["status"], "FAIL")
        self.assertEqual(res["grade"], "REJECT")

    def test_repair_kb_lookup(self):
        rec = RepairKnowledgeBase.get_recommendation("short")
        self.assertIn("probable_causes", rec)
        self.assertIn("repair_actions", rec)
        self.assertIn("ipc_standard", rec)
        self.assertTrue(len(rec["repair_actions"]) > 0)


class TestRepairKBSafetyAndFallback(unittest.TestCase):
    """STEP 9 — every curated entry carries safety_notes; unknown classes get
    a labelled fallback (never a crash, never a silent pseudo-expert answer)."""

    CURATED = ["short", "open", "mousebite", "spur", "copper", "pin-hole"]

    def test_every_curated_class_has_safety_notes(self):
        for cls in self.CURATED:
            rec = RepairKnowledgeBase.get_recommendation(cls)
            self.assertTrue(rec["known_class"], f"{cls} unexpectedly fell through to fallback")
            self.assertIn("safety_notes", rec, f"{cls} missing safety_notes")
            self.assertTrue(len(rec["safety_notes"]) > 0, f"{cls} has empty safety_notes")

    def test_unknown_class_falls_back_with_provenance(self):
        rec = RepairKnowledgeBase.get_recommendation("quantum_flux_leak")
        self.assertFalse(rec["known_class"])
        self.assertEqual(rec["matched_class"], "quantum_flux_leak")
        self.assertTrue(len(rec["safety_notes"]) > 0, "fallback must still carry safety_notes")
        self.assertTrue(len(rec["repair_actions"]) > 0)
        # The fallback must be honestly labelled, not dressed up as an expert entry.
        self.assertEqual(rec["engine"], RepairKnowledgeBase.ENGINE_LABEL)
        self.assertFalse(rec["is_ml_predicted"])

    def test_none_and_empty_inputs_do_not_raise(self):
        for bad in (None, "", "   "):
            rec = RepairKnowledgeBase.get_recommendation(bad)
            self.assertFalse(rec["known_class"])
            self.assertTrue(len(rec["safety_notes"]) > 0)

    def test_alias_names_resolve_to_curated_entries(self):
        # Deployment-era names must land on the curated entry, not the fallback.
        for alias, target in RepairKnowledgeBase.NORMALIZE_MAP.items():
            rec = RepairKnowledgeBase.get_recommendation(alias)
            self.assertTrue(rec["known_class"], f"alias {alias} fell through to fallback")
            self.assertIn(target, RepairKnowledgeBase.KNOWLEDGE_BASE)

    def test_every_entry_is_honestly_labelled(self):
        for cls in self.CURATED + ["totally_unknown_defect"]:
            rec = RepairKnowledgeBase.get_recommendation(cls)
            self.assertEqual(rec["engine"], RepairKnowledgeBase.ENGINE_LABEL)
            self.assertEqual(rec["action_type"], RepairKnowledgeBase.ACTION_LABEL)
            self.assertFalse(rec["is_ml_predicted"])
            self.assertIn("provenance_note", rec)

    def test_no_curated_key_is_silently_shadowed_by_normalize_map(self):
        # A curated key must never also appear as a NORMALIZE_MAP source —
        # that would mean the curated entry is unreachable.
        for key in RepairKnowledgeBase.KNOWLEDGE_BASE:
            self.assertNotIn(key, RepairKnowledgeBase.NORMALIZE_MAP)

if __name__ == "__main__":
    unittest.main()
