"""
Inspect component model class names to verify training dataset.
"""

import torch
from pathlib import Path

MODEL_PATH = "models/component_best_new.pt"

print(f"Loading model: {MODEL_PATH}")
checkpoint = torch.load(MODEL_PATH, weights_only=False, map_location='cpu')

# Check for class names in different possible locations
if 'names' in checkpoint:
    print(f"\nClass names from checkpoint['names']: {checkpoint['names']}")
elif 'model' in checkpoint and hasattr(checkpoint['model'], 'names'):
    print(f"\nClass names from checkpoint['model'].names: {checkpoint['model'].names}")
else:
    print("\nNo direct 'names' key found")
    print(f"Checkpoint keys: {list(checkpoint.keys())}")

# Check for dataset info
if 'train_args' in checkpoint:
    print(f"\nTrain args: {checkpoint['train_args']}")
else:
    print("\nNo train_args found")

# Check for any dataset path references
import json
checkpoint_str = json.dumps({k: str(v) for k, v in checkpoint.items() if not isinstance(v, torch.Tensor)}, indent=2)
if 'data' in checkpoint_str.lower() or 'dataset' in checkpoint_str.lower():
    print("\nDataset-related info found in checkpoint:")
    for key in checkpoint.keys():
        if 'data' in str(key).lower() or 'dataset' in str(key).lower():
            print(f"  {key}: {checkpoint[key]}")
