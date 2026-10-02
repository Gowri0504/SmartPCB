"""
Train a new component detector on the corrected canonical dataset.

This training uses:
- Canonical 6-class taxonomy (IC, capacitor, diode, inductor, resistor, transistor)
- Corrected FICS labels (89% corruption fixed)
- High-resolution training (960×960) for tiny objects
- CPU-compatible settings
"""

import os
from ultralytics import YOLO
from pathlib import Path

# Paths
CANONICAL_DATA_PATH = "datasets/components_canonical/data.yaml"
OUTPUT_DIR = "experiments/component_canonical_v2"
MODEL_NAME = "yolo11n"  # Use nano for CPU training

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 80)
print("TRAINING COMPONENT DETECTOR ON CORRECTED CANONICAL DATASET")
print("=" * 80)
print(f"Data: {CANONICAL_DATA_PATH}")
print(f"Output: {OUTPUT_DIR}")
print(f"Model: {MODEL_NAME}")
print()

# Training configuration optimized for CPU and tiny objects
TRAINING_CONFIG = {
    "data": CANONICAL_DATA_PATH,
    "epochs": 50,           # Reasonable for CPU training
    "imgsz": 960,           # High resolution for tiny objects
    "batch": 8,             # Small batch for CPU memory
    "device": "cpu",        # CPU-only training
    "workers": 4,          # Parallel data loading
    "optimizer": "AdamW",   # Good for small datasets
    "lr0": 0.001,          # Conservative learning rate
    "patience": 10,         # Early stopping patience
    "save": True,           # Save checkpoints
    "project": OUTPUT_DIR,
    "name": "canonical_training",
    "exist_ok": True,
    "pretrained": True,     # Start from pretrained weights
    "augment": True,       # Enable augmentation for small dataset
    "mosaic": 0.5,         # Moderate mosaic augmentation
    "mixup": 0.0,          # Disable mixup for stability
    "copy_paste": 0.0,     # Disable copy-paste for now
    "fliplr": 0.5,         # Horizontal flip
    "scale": 0.5,          # Scale augmentation
    "translate": 0.1,      # Translation augmentation
    "shear": 0.0,          # Disable shear for stability
    "perspective": 0.0,    # Disable perspective for stability
    "hsv_h": 0.015,        # HSV hue augmentation
    "hsv_s": 0.7,          # HSV saturation augmentation
    "hsv_v": 0.4,          # HSV value augmentation
}

print("Training configuration:")
for key, value in TRAINING_CONFIG.items():
    print(f"  {key}: {value}")
print()

print("Starting training...")
print("Note: This may take several hours on CPU.")
print("The model will be saved to:", OUTPUT_DIR)
print()

try:
    # Load model
    model = YOLO(f"{MODEL_NAME}.pt")
    
    # Train
    results = model.train(**TRAINING_CONFIG)
    
    print("\n" + "=" * 80)
    print("TRAINING COMPLETE")
    print("=" * 80)
    print(f"Best model saved to: {OUTPUT_DIR}/canonical_training/weights/best.pt")
    print(f"Training results: {results}")
    
except Exception as e:
    print(f"\nTraining failed with error: {e}")
    print("This is expected if:")
    print("  - Dataset is too small (only 9 images)")
    print("  - System runs out of memory")
    print("  - Training takes too long on CPU")
    print("\nAlternative: Use the existing model with improved inference")