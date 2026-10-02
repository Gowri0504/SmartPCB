"""
Test Test-Time Augmentation (TTA) improvement on existing defect model.

This applies TTA as specified in Phase 3, Step 17 of the prompt.
"""

from ultralytics import YOLO
import time

device = 'cpu'
print(f"Testing TTA improvement on existing defect model...")
print(f"Device: {device}")

# Load existing strong model
model = YOLO("models/defect_best.pt")

print("\n" + "="*80)
print("BASELINE EVALUATION (No TTA)")
print("="*80)

start_time = time.time()
baseline_results = model.val(
    data="datasets/defects/data.yaml",
    split="test",  # Test set (500 images)
    device=device,
    verbose=True
)
baseline_time = time.time() - start_time

print(f"\nBaseline Results:")
print(f"  mAP50: {baseline_results.box.map50:.4f} ({baseline_results.box.map50*100:.2f}%)")
print(f"  mAP50-95: {baseline_results.box.map:.4f} ({baseline_results.box.map*100:.2f}%)")
print(f"  Precision: {baseline_results.box.mp:.4f} ({baseline_results.box.mp*100:.2f}%)")
print(f"  Recall: {baseline_results.box.mr:.4f} ({baseline_results.box.mr*100:.2f}%)")
print(f"  Evaluation time: {baseline_time:.1f}s")

print("\n" + "="*80)
print("TTA EVALUATION (Test-Time Augmentation)")
print("="*80)

start_time = time.time()
tta_results = model.val(
    data="datasets/defects/data.yaml",
    split="test",
    device=device,
    augment=True,  # Enable TTA
    verbose=True
)
tta_time = time.time() - start_time

print(f"\nTTA Results:")
print(f"  mAP50: {tta_results.box.map50:.4f} ({tta_results.box.map50*100:.2f}%)")
print(f"  mAP50-95: {tta_results.box.map:.4f} ({tta_results.box.map*100:.2f}%)")
print(f"  Precision: {tta_results.box.mp:.4f} ({tta_results.box.mp*100:.2f}%)")
print(f"  Recall: {tta_results.box.mr:.4f} ({tta_results.box.mr*100:.2f}%)")
print(f"  Evaluation time: {tta_time:.1f}s")

print("\n" + "="*80)
print("TTA IMPROVEMENT ANALYSIS")
print("="*80)
map50_delta = (tta_results.box.map50 - baseline_results.box.map50) * 100
map_delta = (tta_results.box.map - baseline_results.box.map) * 100
time_delta = tta_time - baseline_time

print(f"mAP50 delta: {map50_delta:+.2f}%")
print(f"mAP50-95 delta: {map_delta:+.2f}%")
print(f"Time delta: {time_delta:+.1f}s ({time_delta/baseline_time*100:+.1f}% slower)")

if map50_delta > 0:
    print(f"\n✓ TTA provides {map50_delta:.2f}% mAP50 improvement")
else:
    print(f"\n✗ TTA does not improve mAP50 ({map50_delta:.2f}% delta)")

print(f"\nConclusion: TTA {'improves' if map50_delta > 0 else 'does not improve'} model performance by {abs(map50_delta):.2f}% mAP50 with {time_delta/baseline_time:.1f}x inference time cost")