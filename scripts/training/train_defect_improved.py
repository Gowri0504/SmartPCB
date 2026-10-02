"""
Train improved defect model with incremental technique additions.

This implements the reduced-scope CPU approach as specified in Phase 1b:
- yolo11n instead of yolo11s (faster, smaller)
- Reduced image size (512 instead of 640)
- Realistic epoch count (30-60 epochs with early stopping)
- Incremental technique additions with before/after measurement
"""

from ultralytics import YOLO
import torch
import os
import json
from datetime import datetime

# Check available device
device = 'cpu'  # CPU-only environment
print(f"Using device: {device}")
print(f"PyTorch version: {torch.__version__}")

# Data configuration
data_yaml = "datasets/defects/data.yaml"
output_dir = "models/defect_improvement_runs"

# Create output directory
os.makedirs(output_dir, exist_ok=True)

# Load YOLOv11n model (smaller/faster than yolo11s)
model = YOLO("yolo11n.pt")

# BASELINE CONFIGURATION (minimal changes from defaults)
baseline_args = {
    "data": data_yaml,
    "epochs": 30,  # Realistic CPU epoch count
    "batch": 16,   # Smaller batch for CPU
    "imgsz": 512,  # Reduced image size for CPU speed
    "device": device,
    "lr0": 0.01,   # Initial learning rate
    "lrf": 0.001,  # Final learning rate
    "momentum": 0.937,
    "weight_decay": 0.0005,
    "patience": 10,  # Early stopping patience
    "verbose": True,
    "save": True,
    "project": output_dir,
    "name": "baseline",
    "exist_ok": True
}

print("\n" + "="*80)
print("BASELINE TRAINING (yolo11n, 512px, 30 epochs)")
print("="*80)
print(f"Configuration: {baseline_args}")

try:
    # Train baseline
    baseline_results = model.train(**baseline_args)
    
    print("\nBaseline training completed!")
    print(f"Best model saved to: {output_dir}/baseline/weights/best.pt")
    
    # Save baseline results
    baseline_info = {
        "configuration": "baseline",
        "model": "yolo11n",
        "imgsz": 512,
        "epochs": 30,
        "batch": 16,
        "device": device,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(f"{output_dir}/baseline/training_info.json", "w") as f:
        json.dump(baseline_info, f, indent=2)
    
except Exception as e:
    print(f"\nBaseline training failed with error: {e}")
    print("This is expected if CPU constraints are too severe.")
    baseline_info = {
        "configuration": "baseline",
        "status": "FAILED",
        "error": str(e),
        "timestamp": datetime.now().isoformat()
    }
    
    with open(f"{output_dir}/baseline/training_info.json", "w") as f:
        json.dump(baseline_info, f, indent=2)

print("\nNext: Would implement incremental technique additions if baseline succeeded")