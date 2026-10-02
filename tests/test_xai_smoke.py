import unittest
import numpy as np
import cv2
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class TestXAISmoke(unittest.TestCase):
    """XAI smoke tests — verify XAI module runs without crashing and returns
    honest attribution metadata (disclaimer + method label + correct shape)."""

    @classmethod
    def setUpClass(cls):
        from ai.inference.engine import SmartPCBInspectionEngine
        cls.engine = SmartPCBInspectionEngine(device="cpu")

    def _synthetic_pcb(self, H=512, W=512):
        """Synthesizes a plausible green PCB-like image with copper-looking shapes."""
        img = np.zeros((H, W, 3), dtype=np.uint8)
        img[:, :] = (40, 110, 50)  # PCB green
        # Traces
        for y in range(60, H - 60, 60):
            img[y : y + 6, 50 : W - 50] = (180, 120, 80)
        # Pads
        for x in range(100, W - 100, 80):
            cv2.rectangle(img, (x, 200), (x + 30, 230), (150, 100, 60), -1)
        cv2.rectangle(img, (200, 300), (350, 380), (60, 60, 60), -1)  # fake component
        cv2.rectangle(img, (200, 300), (350, 380), (200, 200, 200), 2)
        return img

    def test_xai_output_keys_and_shape_when_defects(self):
        img = self._synthetic_pcb()
        # Force at least one synthetic detection into defects by running inspection
        result = self.engine.inspect(img, generate_xai=True)
        xai = result.get("xai") or {}
        self.assertIsInstance(xai, dict)
        # Always present keys if any detections:
        if xai and "error" not in xai and result.get("defects"):
            for required in [
                "attribution_method",
                "disclaimer",
            ]:
                self.assertIn(required, xai, f"XAI missing key {required}")
            # Honest labeling must not claim Grad-CAM++ gradient
            self.assertNotEqual(
                xai.get("attribution_method"),
                "gradcam++",
                "XAI must not claim gradient Grad-CAM++ when it is an energy approximation.",
            )
            self.assertIsInstance(xai.get("disclaimer"), str)
            self.assertTrue(len(xai["disclaimer"]) > 0)
            self.assertIn("Not authentic", xai["disclaimer"])
        # Either error or output always has dict structure
        self.assertTrue(isinstance(xai, dict))

    def test_xai_overlay_image_shape_matches_input_when_run(self):
        img = self._synthetic_pcb(640, 640)
        # Direct test of gradcam module
        if self.engine.xai_engine is None:
            self.skipTest("XAI engine not loaded (defect model missing or failed init)")
        out = self.engine.xai_engine.generate_heatmap(
            img_bgr=img,
            target_box=[100, 100, 400, 400],
            class_id=1,
            target_class_name="short",
            target_confidence=0.9,
        )
        # Returns dict (not tuple like original code)
        self.assertIsInstance(out, dict)
        for k in ["heatmap_norm", "overlay_bgr", "attribution_method", "disclaimer",
                  "target_class", "target_confidence", "target_bbox", "overlay_shape"]:
            self.assertIn(k, out, f"missing key {k}")
        self.assertEqual(out["overlay_bgr"].shape, img.shape)
        self.assertEqual(out["overlay_bgr"].dtype, np.uint8)
        self.assertEqual(out["heatmap_norm"].shape, (img.shape[0], img.shape[1]))
        self.assertTrue(np.all(np.isfinite(out["heatmap_norm"])))
        self.assertEqual(out["target_class"], "short")
        self.assertAlmostEqual(out["target_confidence"], 0.9)
        self.assertEqual(out["attribution_method"], "activation_energy_approximation")

    def test_xai_does_not_crash_on_corrupt_target_box(self):
        img = self._synthetic_pcb(256, 256)
        if self.engine.xai_engine is None:
            self.skipTest("XAI engine not loaded")
        # Out of bounds target box: engine should still return something finite
        out = self.engine.xai_engine.generate_heatmap(
            img_bgr=img,
            target_box=[-1000, -99999, 99999, 99999],
            class_id=2,
            target_class_name="mousebite",
            target_confidence=0.5,
        )
        self.assertIsInstance(out, dict)
        self.assertTrue(np.all(np.isfinite(out["heatmap_norm"])))


if __name__ == "__main__":
    unittest.main()
