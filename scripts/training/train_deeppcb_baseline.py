"""
Train baseline YOLOv11s on DeepPCB dataset for defect detection improvement project.

This is a realistic baseline training given CPU-only constraints.
"""

from ultralytics import YOLO
import torch
import os

# Check available device
device = 'cpu'  # CPU-only environment
print(f"Using device: {device}")
print(f"PyTorch version: {torch.__version__}")

# Data configuration
data_yaml = "datasets/defects/data.yaml"
output_dir = "models/deeppcb_baseline"

# Create output directory
os.makedirs(output_dir, exist_ok=True)

# Load YOLOv11s model
model = YOLO("yolo11s.pt")

# Training configuration (adapted for CPU constraints)
# Paper uses: 300 epochs, batch 16, imgsz 640, lr 0.01
# CPU adaptation: Fewer epochs, smaller batch, early stopping
training_args = {
    "data": data_yaml,
    "epochs": 10,  # Reduced from 300 due to CPU constraints
    "batch": 8,    # Reduced from 16 due to CPU memory
    "imgsz": 640,
    "device": device,
    "lr0": 0.01,   # Initial learning rate (paper spec)
    "lrf": 0.001,  # Final learning rate (paper spec)
    "momentum": 0.937,  # SGD momentum (paper spec)
    "weight_decay": 0.0005,  # Weight decay (paper spec)
    "patience": 5,  # Early stopping patience
    "verbose": True,
    "save": True,
    "project": output_dir,
    "name": "baseline_run",
    "exist_ok": True
}

print("Starting baseline YOLOv11s training on DeepPCB dataset...")
print(f"Configuration: {training_args}")

try:
    # Train the model
    results = model.train(**training_args)
    
    print("\nTraining completed successfully!")
    print(f"Best model saved to: {output_dir}/baseline_run/weights/best.pt")
    
    # Export model info
    print(f"\nModel information:")
    print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"Model size: {os.path.getsize(f'{output_dir}/baseline_run/weights/best.pt') / (1024*1024):.2f} MB")
    
except Exception as e:
    print(f"\nTraining failed with error: {e}")
    print("This is expected given CPU-only constraints and limited epochs.")
    print("Full training would require GPU or significantly more CPU time.")