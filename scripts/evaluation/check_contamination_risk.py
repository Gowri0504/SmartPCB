"""
Attempt to determine contamination risk by comparing local test images with public DeepPCB sources.
DeepPCB is a well-known public dataset, so we can check if local test images match any public versions.
"""

import os
import hashlib
from pathlib import Path

# Local test images
LOCAL_TEST_DIR = "datasets/defects/test/images"
LOCAL_TEST_IMAGES = list(Path(LOCAL_TEST_DIR).glob("*.jpg")) + list(Path(LOCAL_TEST_DIR).glob("*.png"))

print(f"Local test images: {len(LOCAL_TEST_IMAGES)}")

# Compute MD5 hashes for local test images
local_hashes = {}
for img_path in LOCAL_TEST_IMAGES:
    try:
        with open(img_path, 'rb') as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        local_hashes[img_path.name] = md5
    except Exception as e:
        print(f"Error reading {img_path}: {e}")

print(f"Computed {len(local_hashes)} MD5 hashes")

# Save local hashes
import json
with open("reports/eval/local_test_hashes.json", "w") as f:
    json.dump(local_hashes, f, indent=2)

print(f"Saved to reports/eval/local_test_hashes.json")

# Check for common DeepPCB naming patterns
print("\nChecking for DeepPCB naming patterns...")
deeppcb_patterns = [
    "test", "Sub", "sub", "train", "Train"
]

for img_name in local_hashes.keys():
    for pattern in deeppcb_patterns:
        if pattern in img_name:
            print(f"  {img_name} contains '{pattern}'")

print("\nNote: Without access to the original Kaggle training dataset manifest,")
print("we cannot definitively prove overlap. However, the suspicious clustering")
print("of train (0.993) / val (0.993) / test (0.983) mAP50 suggests potential")
print("train/test overlap in the remote Kaggle training data.")
print("\nResolution: From-scratch training on local dataset is required to") 
print("eliminate this ambiguity.")