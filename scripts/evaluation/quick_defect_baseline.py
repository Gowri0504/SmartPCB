"""
Quick baseline evaluation using Ultralytics built-in val() for standard mAP metrics.
This will give us the true baseline mAP50/mAP50-95 on the test set.
"""

from ultralytics import YOLO
import torch

# Check device
device = 'cpu'  # CPU-only environment
print(f"Using device: {device}")

# Load model
model = YOLO("models/defect_best.pt")

# Run validation on test set using Ultralytics standard evaluation
print("Running standard Ultralytics validation on test set...")
results = model.val(
    data="datasets/defects/data.yaml",
    split="test",  # Test set (500 images)
    device=device,
    verbose=True
)

print("\n" + "="*80)
print("BASELINE DEFECT MODEL RESULTS (STANDARD ULTRALYTICS EVALUATION)")
print("="*80)
print(f"Dataset: DeepPCB test set (500 images)")
print(f"Device: {device}")
print(f"Standard mAP metrics:")
print(f"  mAP50: {results.box.map50:.4f} ({results.box.map50*100:.2f}%)")
print(f"  mAP50-95: {results.box.map:.4f} ({results.box.map*100:.2f}%)")
print(f"  Precision: {results.box.mp:.4f} ({results.box.mp*100:.2f}%)")
print(f"  Recall: {results.box.mr:.4f} ({results.box.mr*100:.2f}%)")
print("\nPer-class metrics:")
for i, class_name in enumerate(model.names):
    print(f"  {class_name}: AP50 = {results.box.maps[i]:.4f} ({results.box.maps[i]*100:.2f}%)")