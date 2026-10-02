import unittest
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class TestFastAPIHealth(unittest.TestCase):
    """Verify FastAPI app imports, TestClient can GET /health, and response
    contains truthful structured info (no hardcoded fake model strings)."""

    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient
        except Exception as e:
            raise unittest.SkipTest(f"fastapi TestClient not available: {e}")
        from ai_service.main import app
        cls.client = TestClient(app)

    def test_health_200_with_required_keys(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for top_key in ["status", "timestamp", "version", "device",
                        "engine_status", "model_status", "canonical_classes"]:
            self.assertIn(top_key, data, f"/health missing top-level key {top_key}")

    def test_health_device_is_cpu_or_cuda_not_hardcoded(self):
        data = self.client.get("/health").json()
        dev = data["device"]
        # Never hardcoded to e.g. a specific marketing string
        self.assertIn(dev, ("cpu", "cuda", "cuda:0", "unknown", ""))
        import torch
        # If CUDA is not available, device should never be "cuda:0" without CUDA
        if not torch.cuda.is_available():
            self.assertIn(dev, ("cpu", "unknown", ""))

    def test_health_model_status_structured(self):
        data = self.client.get("/health").json()
        ms = data["model_status"]
        for sub in ["component_model", "defect_model", "xai_engine"]:
            self.assertIn(sub, ms)
        cm = ms["component_model"]
        self.assertIn("path", cm)
        self.assertIn("loaded", cm)
        self.assertIn("classes", cm)
        self.assertIsInstance(cm["loaded"], bool)
        # CORRECTED 2026-09-23: these assertions previously claimed the deployed
        # component model had 6 classes. The checkpoint verifiably emits 10
        # (model.names read from models/component_best.pt). The old assertions
        # encoded an untruthful contract; they now assert the real class space.
        self.assertEqual(len(cm["classes"]), 10)
        self.assertEqual(cm["classes"], [
            "relay", "buzzer", "ic", "switch", "battery",
            "transistor", "capacitor", "resistor", "led", "diode",
        ])
        dm = ms["defect_model"]
        self.assertEqual(len(dm["classes"]), 6)
        self.assertEqual(dm["classes"], ["open", "short", "mousebite", "spur", "copper", "pin-hole"])

    def test_health_canonical_classes_matches_ac11(self):
        data = self.client.get("/health").json()
        ccls = data["canonical_classes"]
        self.assertEqual(ccls["components"], [
            "relay", "buzzer", "ic", "switch", "battery",
            "transistor", "capacitor", "resistor", "led", "diode",
        ])
        self.assertEqual(ccls["defects"], ["open", "short", "mousebite", "spur", "copper", "pin-hole"])

    def test_health_reports_class_taxonomy_mapping_honestly(self):
        """Component taxonomy stays PARTIAL (5 unmapped classes, 1 undetectable).
        Defect taxonomy is FULL via CANONICAL deployment (from-scratch model 2026-09-26).
        The scratch model uses canonical names directly; legacy PCB-DATASET alignment
        is preserved in history but no longer active."""
        data = self.client.get("/health").json()
        tax = data["class_taxonomy"]
        comp = tax["components"]
        self.assertEqual(comp["mapping_status"], "PARTIAL")
        for unmapped in ["relay", "buzzer", "switch", "battery", "led"]:
            self.assertIn(unmapped, comp["unmapped_model_classes"])
        self.assertIn("inductors", comp["undetectable_curated_classes"])
        self.assertEqual(comp["curated_dataset_classes"],
                         ["ICs", "capacitors", "diodes", "inductors", "resistors", "transistors"])
        defects = tax["defects"]
        self.assertEqual(defects["mapping_status"], "FULL")
        self.assertEqual(defects["alignment_mode"], "positional")
        self.assertIs(defects["checkpoint_name_strings_authoritative"], False)
        # Keys normalized to int: HTTP JSON round-trips dict keys to strings.
        idx_map = {int(k): v for k, v in defects["model_index_to_canonical"].items()}
        self.assertEqual(idx_map,
                         {0: "open", 1: "short", 2: "mousebite",
                          3: "spur", 4: "copper", 5: "pin-hole"})
        self.assertEqual(defects["approximate_mappings"], {})
        self.assertEqual(defects["unmapped_model_classes"], [])
        self.assertEqual(defects["undetectable_curated_classes"], [])
        self.assertEqual(len(defects["raw_to_canonical"]), 6)

    def test_health_component_verification_declares_mapping_status(self):
        data = self.client.get("/health").json()
        ver = data["model_status"]["component_model"]["verification"]
        self.assertIn("canonical_mapping_status", ver)
        self.assertIn("unmapped_loaded_classes", ver)
        self.assertIn("class_count_loaded", ver)


if __name__ == "__main__":
    unittest.main()
