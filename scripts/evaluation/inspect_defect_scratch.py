"""
Inspect defect_best_scratch.pt class names.
"""

import torch

MODEL_PATH = "models/defect_best_scratch.pt"

print(f"Loading model: {MODEL_PATH}")
checkpoint = torch.load(MODEL_PATH, weights_only=False, map_location='cpu')

# Check for class names
if 'model' in checkpoint and hasattr(checkpoint['model'], 'names'):
    print(f"\nClass names from checkpoint['model'].names: {checkpoint['model'].names}")
else:
    print("\nNo class names found")
