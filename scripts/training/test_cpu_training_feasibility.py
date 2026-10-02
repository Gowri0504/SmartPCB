"""
Test CPU training feasibility with minimal epochs to assess runtime.
"""

from ultralytics import YOLO
import time
import os

device = 'cpu'
print(f"Testing CPU training feasibility...")

# Load smallest model
model = YOLO("yolo11n.pt")

# Very minimal training for feasibility test
test_args = {
    "data": "datasets/defects/data.yaml",
    "epochs": 2,  # Just 2 epochs to test feasibility
    "batch": 8,   # Small batch
    "imgsz": 512,  # Reduced size
    "device": device,
    "verbose": True,
    "project": "models/test_runs",
    "name": "feasibility_test",
    "exist_ok": True
}

print(f"Configuration: {test_args}")
print("Starting 2-epoch feasibility test...")

start_time = time.time()
try:
    results = model.train(**test_args)
    elapsed = time.time() - start_time
    
    print(f"\nFeasibility test completed in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"Projected time for 30 epochs: ~{elapsed * 15 / 60:.1f} hours")
    
    if elapsed * 15 / 60 > 4:  # If projected > 4 hours
        print("\nWARNING: Projected training time > 4 hours for 30 epochs")
        print("This may not be feasible in current session")
    else:
        print("\nTraining appears feasible within reasonable time")
        
except Exception as e:
    print(f"\nFeasibility test failed: {e}")
    print("CPU training may not be feasible for this dataset size")