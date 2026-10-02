import unittest
import os
import sys
import io
import tempfile
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import sys as _sys
SCRIPTS_DATASET_DIR = os.path.join(ROOT, "scripts", "dataset")
if SCRIPTS_DATASET_DIR not in _sys.path:
    _sys.path.insert(0, SCRIPTS_DATASET_DIR)

from validate_dataset import validate_dataset


def _write_empty_pgm_like_image(path):
    """Write a tiny 100x100 JPEG image using only stdlib-free approach via PIL stub."""
    try:
        from PIL import Image
    except Exception:
        raise unittest.SkipTest("Pillow not installed; cannot create test fixtures")
    img = Image.new("RGB", (100, 100), color=(120, 80, 40))
    img.save(path, format="JPEG", quality=85)


class TestDatasetValSmoke(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="pcb_ds_smoke_")
        # Create a 1-split (train only) minimal valid YOLO dataset with 1 image + 1 valid box
        for sub in ("train", "val", "test"):
            os.makedirs(os.path.join(self.tmpdir, sub, "images"), exist_ok=True)
            os.makedirs(os.path.join(self.tmpdir, sub, "labels"), exist_ok=True)

        # train: 1 valid image, 1 valid box
        _write_empty_pgm_like_image(os.path.join(self.tmpdir, "train", "images", "boardA.jpg"))
        with open(os.path.join(self.tmpdir, "train", "labels", "boardA.txt"), "w") as f:
            f.write("0 0.5 0.5 0.2 0.2\n")

        # val: 1 image with empty label file (no boxes, YOLO negative sample)
        _write_empty_pgm_like_image(os.path.join(self.tmpdir, "val", "images", "boardB.jpg"))
        open(os.path.join(self.tmpdir, "val", "labels", "boardB.txt"), "w").close()

        # test: 1 image no label file — should trigger missing_label
        _write_empty_pgm_like_image(os.path.join(self.tmpdir, "test", "images", "boardC.jpg"))
        # intentionally no boardC.txt

        # Also 1 extra orphan label file with no image in train
        with open(os.path.join(self.tmpdir, "train", "labels", "orphan.txt"), "w") as f:
            f.write("1 0.2 0.2 0.1 0.1\n")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_validate_dataset_returns_dict_with_new_T4_fields(self):
        """Validate that the validate_dataset function returns ALL the new keys added in T4."""
        dummy_classes = ["ICs", "capacitors", "diodes", "inductors", "resistors", "transistors"]
        buf = io.StringIO()
        import contextlib
        with contextlib.redirect_stdout(buf):
            result, stats_detail = validate_dataset(self.tmpdir, "SmokeFixture", dummy_classes)

        self.assertIsInstance(result, dict)
        # New top-level keys (T4)
        for k in ("image_decode_errors", "empty_label_files",
                  "phash_duplicates_group_count", "phash_unavailable_reason",
                  "hash_duplicates_group_count", "board_level_cross_split_leak_count"):
            self.assertIn(k, result, f"Missing top-level key {k}")
        self.assertIn("corrupted_images", result)
        self.assertIn("checks", result)
        self.assertIn("corrupted_images", result["checks"])
        self.assertIn("empty_label_files", result["checks"])

        # per_split new enrichments
        for split in ("train", "val", "test"):
            self.assertIn(split, result["per_split"])
            self.assertIn("empty_label_count", result["per_split"][split],
                          f"per_split.{split} missing empty_label_count")
            bs = result["per_split"][split]["box_count_per_image_stats"]
            for stat in ("min", "max", "mean", "median", "samples"):
                self.assertIn(stat, bs, f"box_count_per_image_stats missing key {stat} for split {split}")

    def test_smoke_counts_are_correct(self):
        """Verify the validator actually counts the 1 orphan + 1 empty label + 1 missing label in our fixture."""
        dummy_classes = ["ICs", "capacitors", "diodes", "inductors", "resistors", "transistors"]
        import contextlib, io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result, _ = validate_dataset(self.tmpdir, "SmokeFixture2", dummy_classes)

        # total_images = 3 (boardA in train, boardB in val, boardC in test)
        self.assertEqual(result["total_images"], 3,
                         f"Expected 3 total images; got {result['total_images']}. stdout tail: {buf.getvalue()[-400:]}")

        # val has one empty-label file -> val.empty_label_count == 1
        self.assertEqual(result["per_split"]["val"]["empty_label_count"], 1)
        self.assertEqual(result["empty_label_files"], 1)

        # Missing pairs: test/boardC.jpg no label, train/orphan.txt no image -> total >= 2
        mp = result["checks"]["missing_image_label_pairs"]
        self.assertGreaterEqual(mp["count"], 2,
                                f"Missing image/label pair count expected >=2, got {mp['count']}")


if __name__ == "__main__":
    unittest.main()
