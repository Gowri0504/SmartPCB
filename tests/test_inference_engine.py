import os
import unittest
import numpy as np
from ai.inference.engine import SmartPCBInspectionEngine
from ai.inference.ensemble import weighted_boxes_fusion, run_tta_8view

class TestInferenceEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = SmartPCBInspectionEngine()
        # Find a real test image from the dataset
        test_dir = "datasets/defects/test/images"
        cls.test_img = None
        if os.path.exists(test_dir):
            files = [f for f in os.listdir(test_dir) if f.endswith(('.jpg', '.png'))]
            if files:
                cls.test_img = os.path.join(test_dir, files[0])

    def test_inference_on_synthetic_image(self):
        # 640x640 synthetic BGR image (green substrate with simulated components)
        img = np.full((640, 640, 3), (35, 90, 45), dtype=np.uint8)
        # Add simulated copper traces
        img[100:110, 50:500] = (20, 180, 210)
        img[300:310, 50:500] = (20, 180, 210)

        result = self.engine.inspect(img, conf_threshold=0.20, generate_xai=True)

        self.assertIn("inspection_id", result)
        self.assertIn("components", result)
        self.assertIn("defects", result)
        self.assertIn("quality_score", result)
        self.assertIn("overall_score", result["quality_score"])
        self.assertIn("recommendations", result)
        self.assertIn("annotated_image", result)

    def test_inference_on_real_image(self):
        if not self.test_img:
            self.skipTest("No test image found in datasets/defects/test/images")

        result = self.engine.inspect(self.test_img, conf_threshold=0.15, generate_xai=True)
        self.assertIn("inspection_id", result)
        self.assertIsInstance(result["components"], list)
        self.assertIsInstance(result["defects"], list)
        self.assertIsInstance(result["quality_score"]["overall_score"], (int, float))

    def test_timing_buckets_are_disjoint_and_complete(self):
        """Every named bucket must be non-negative and their sum must land inside
        [total - slack, total]: no region may be double-counted (the render/score
        gap used to live only in total_ms) and no region may exceed the total."""
        img = np.full((640, 640, 3), (35, 90, 45), dtype=np.uint8)
        img[100:110, 50:500] = (20, 180, 210)

        result = self.engine.inspect(img, conf_threshold=0.20, generate_xai=True)
        t = result["inference_timing_ms"]
        for key in ("preprocess_ms", "component_inference_ms", "defect_inference_ms",
                    "xai_ms", "postprocess_ms"):
            self.assertIn(key, t)
            self.assertGreaterEqual(t[key], 0.0, f"{key} went negative: {t[key]}")
        bucket_sum = sum(t[k] for k in
                         ("preprocess_ms", "component_inference_ms", "defect_inference_ms",
                          "xai_ms", "postprocess_ms"))
        # Thread-scheduling noise: allow a small under-count of total, but the
        # sum may never meaningfully EXCEED the total (that would mean overlap).
        self.assertLessEqual(bucket_sum, t["total_ms"] + 1.0,
                             f"buckets overlap total: sum={bucket_sum} total={t['total_ms']}")
        self.assertGreaterEqual(bucket_sum, t["total_ms"] - 5.0,
                                f"buckets miss most of total: sum={bucket_sum} total={t['total_ms']}")

if __name__ == "__main__":
    unittest.main()


class TestAccuracyModeFlags(unittest.TestCase):
    """Engine must accept TTA + ensemble + per_class_conf constructor args
    without raising, and the inspect() pipeline must run successfully end-to-
    end (no raw bbox transform crash, no WBF divide-by-zero, no NPE).

    These are SMOKE tests — they do NOT assert accuracy uplift; they assert
    that the new constructor flags are backward-compatible and the code path
    does not crash on a synthetic image.  Accuracy uplift is measured in the
    evaluation script against ground-truth.
    """

    @staticmethod
    def _synth_img():
        img = np.full((640, 640, 3), (35, 90, 45), dtype=np.uint8)
        img[100:110, 50:500] = (20, 180, 210)
        img[300:310, 50:500] = (20, 180, 210)
        return img

    def test_engine_tta_flag_accepted_and_runs(self):
        try:
            engine = SmartPCBInspectionEngine(device="cpu", tta_enabled=True)
        except Exception as e:
            self.fail(f"Engine with tta_enabled=True failed to construct: {e}")
        out = engine.inspect(self._synth_img(), conf_threshold=0.25, generate_xai=False)
        self.assertIn("defects", out)
        self.assertIn("components", out)
        self.assertIn("overall_score", out["quality_score"])
        self.assertIn("accuracy_mode", out["inference_timing_ms"])
        self.assertTrue(out["inference_timing_ms"]["accuracy_mode"]["tta_enabled"])

    @unittest.skipUnless(os.path.isdir(os.path.join("models")),
                         "models/ directory required for ensemble test")
    def test_engine_ensemble_loads_two_models_and_runs(self):
        scratch = os.path.join("models", "defect_best_scratch.pt")
        legacy = os.path.join("models", "defect_best_legacy.pt")
        extras = []
        if os.path.isfile(legacy):
            extras.append(legacy)
        if not os.path.isfile(scratch):
            self.skipTest(f"Primary scratch checkpoint not found: {scratch}")
        try:
            engine = SmartPCBInspectionEngine(
                device="cpu",
                defect_model_path=scratch,
                defect_ensemble_paths=extras,
                tta_enabled=False,
                per_class_defect_conf_overrides={"pin-hole": 0.75},
                wbf_iou=0.5,
            )
        except Exception as e:
            self.fail(f"Engine with ensemble extras failed to construct: {e}")
        self.assertGreaterEqual(len(engine.defect_models), 1,
                                "Primary defect model must always be loaded")
        if extras:
            self.assertGreaterEqual(len(engine.defect_models), 2,
                                    "Extra ensemble paths must be loaded (not silently dropped)")
        out = engine.inspect(self._synth_img(), conf_threshold=0.25, generate_xai=False)
        self.assertIn("defects", out)
        am = out["inference_timing_ms"]["accuracy_mode"]
        self.assertTrue(am["ensemble_count"] >= 1)
        self.assertTrue(am["per_class_conf_overrides_applied"])


class TestWBFStability(unittest.TestCase):
    """Weighted Boxes Fusion must not crash on:
      (1) empty input,
      (2) no-overlap inputs,
      (3) exactly-overlapping boxes (numerical stability),
      (4) conf clamp to [0,1] after length-weighted scale.
    """

    def test_wbf_stable_empty_and_no_overlap(self):
        self.assertEqual(weighted_boxes_fusion([], iou_thresh=0.5), [])
        self.assertEqual(weighted_boxes_fusion([None], iou_thresh=0.5), [])
        # Two non-overlapping, single-class
        boxes = [
            {"bbox": [10, 10, 50, 50], "confidence": 0.9, "class": "open"},
            {"bbox": [100, 100, 150, 150], "confidence": 0.8, "class": "open"},
        ]
        fused = weighted_boxes_fusion(boxes, iou_thresh=0.5)
        self.assertEqual(len(fused), 2)

    def test_wbf_stable_exact_overlap_and_conf_clamp(self):
        # Four exactly-overlapping boxes from "ensemble views"
        boxes = [
            {"bbox": [10, 10, 50, 50], "confidence": 0.9, "class": "short"},
            {"bbox": [10, 10, 50, 50], "confidence": 0.95, "class": "short"},
            {"bbox": [10, 10, 50, 50], "confidence": 0.85, "class": "short"},
            {"bbox": [10, 10, 50, 50], "confidence": 0.92, "class": "short"},
        ]
        fused = weighted_boxes_fusion(boxes, iou_thresh=0.5)
        self.assertEqual(len(fused), 1)
        c = fused[0]["confidence"]
        self.assertGreaterEqual(c, 0.0)
        self.assertLessEqual(c, 1.0, "WBF scaled confidence must clamp into [0,1]")
        # bbox coords must be inside original range
        bx, by, bX, bY = fused[0]["bbox"]
        self.assertGreaterEqual(bx, 10 - 1e-6)
        self.assertLessEqual(bX, 50 + 1e-6)

    def test_wbf_class_aware_does_not_mix_classes(self):
        # Same bbox, two different classes: must NOT be fused together into one
        boxes = [
            {"bbox": [10, 10, 50, 50], "confidence": 0.9, "class": "open"},
            {"bbox": [10, 10, 50, 50], "confidence": 0.9, "class": "short"},
        ]
        fused = weighted_boxes_fusion(boxes, iou_thresh=0.99, class_aware=True)
        self.assertEqual(len(fused), 2)
        classes_out = sorted(b["class"] for b in fused)
        self.assertEqual(classes_out, ["open", "short"])

    def test_tta_8view_returns_8_and_inverse_roundtrip(self):
        """run_tta_8view must emit exactly 8 views with an inv_fn that maps a
        synthetic bbox back into the original coordinate frame approximately.
        We don't require pixel-perfect (rotations bloat bbox via AABB) but we do
        require numeric stability and 8 unique aug_names."""
        img = np.full((640, 640, 3), 0, dtype=np.uint8)
        views = run_tta_8view(img)
        self.assertEqual(len(views), 8)
        names = [v[0] for v in views]
        self.assertEqual(len(set(names)), 8)
        for aug_name, aug_img, inv_fn in views:
            self.assertEqual(aug_img.ndim, 3)
            orig_boxes = [{"bbox": [100, 100, 200, 200], "confidence": 0.9, "class": "open"}]
            back = inv_fn(orig_boxes)
            self.assertIsInstance(back, list)
            self.assertEqual(len(back), 1)
            x1, y1, x2, y2 = back[0]["bbox"]
            self.assertTrue(np.isfinite(x1), f"{aug_name}: inverse bbox non-finite")
            self.assertLess(x1, x2)
            self.assertLess(y1, y2)


if __name__ == "__main__":
    unittest.main()
