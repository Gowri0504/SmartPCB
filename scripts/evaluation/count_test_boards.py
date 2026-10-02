"""
Count distinct physical boards in the components_unified test split.
Board IDs are encoded in filenames (e.g., fics_s1_front_x1536_y4096).
"""

import os
from pathlib import Path
from collections import defaultdict

TEST_DIR = "datasets/components_unified/test/images"
test_images = list(Path(TEST_DIR).glob("*.jpg")) + list(Path(TEST_DIR).glob("*.png"))

print(f"Test images: {len(test_images)}")

# Extract board IDs from filenames
board_ids = set()
for img_path in test_images:
    # Pattern: fics_s1_front_x1536_y4096 -> board ID is "s1"
    # Pattern: fics_s3_s3_front_x5632_y1024 -> board ID is "s3_s3"
    parts = img_path.stem.split('_')
    # Board ID is typically the second part (s1, s2, s3_s3, s4_s4, s5_s5)
    if len(parts) >= 2:
        board_id = parts[1]
        board_ids.add(board_id)

print(f"Distinct board IDs: {len(board_ids)}")
print(f"Board IDs: {sorted(board_ids)}")

# Check if any board appears in multiple images
board_image_count = defaultdict(int)
for img_path in test_images:
    parts = img_path.stem.split('_')
    if len(parts) >= 2:
        board_id = parts[1]
        board_image_count[board_id] += 1

print(f"\nImages per board:")
for board_id, count in sorted(board_image_count.items(), key=lambda x: x[1], reverse=True):
    print(f"  {board_id}: {count} images")

# Risk assessment
if len(board_ids) <= 2:
    print(f"\nRISK: Only {len(board_ids)} distinct boards in test split.")
    print("   Generalization risk: HIGH - model may be overfitting to specific boards")
elif len(board_ids) <= 5:
    print(f"\nRISK: Only {len(board_ids)} distinct boards in test split.")
    print("   Generalization risk: MODERATE - limited board diversity")
else:
    print(f"\nGOOD: {len(board_ids)} distinct boards in test split.")
    print("   Generalization risk: LOW")