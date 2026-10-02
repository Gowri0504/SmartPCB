import os
import unittest
import numpy as np
from ai.inference.engine import SmartPCBInspectionEngine

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
