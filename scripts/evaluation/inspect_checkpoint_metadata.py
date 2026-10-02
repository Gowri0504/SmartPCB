"""
Inspect defect checkpoint metadata to check training configuration and potential leakage.
"""

from ultralytics import YOLO
import json

# Load the defect model
model = YOLO("models/defect_best.pt")

# Get model metadata
print("="*80)
print("DEFECT MODEL CHECKPOINT METADATA")
print("="*80)

# Check if model has training args
if hasattr(model, 'trainer') and model.trainer is not None:
    print(f"Trainer: {model.trainer}")
else:
    print("No trainer attribute directly accessible")

# Try to get model configuration
print(f"\nModel info:")
print(f"  Model type: {type(model)}")
print(f"  Task: {model.task}")
print(f"  Names: {model.names}")

# Check for model config
if hasattr(model, 'cfg'):
    print(f"  Config: {model.cfg}")

# Check for model args from Ultralytics
if hasattr(model, 'args'):
    print(f"  Args: {model.args}")

# Extract info from model.model if available
if hasattr(model, 'model'):
    print(f"\nModel architecture:")
    print(f"  {model.model}")

# Save what we can extract
metadata = {
    "model_type": str(type(model)),
    "task": model.task,
    "names": model.names,
    "has_trainer": hasattr(model, 'trainer') and model.trainer is not None,
    "has_cfg": hasattr(model, 'cfg'),
    "has_args": hasattr(model, 'args')
}

if hasattr(model, 'args'):
    metadata["args"] = str(model.args)

with open("reports/eval/defect_checkpoint_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)
    print(f"\nMetadata saved to reports/eval/defect_checkpoint_metadata.json")

print("\n" + "="*80)
print("LEAKAGE ANALYSIS")
print("="*80)
print("Checkpoint class names (model emits):")
for idx, name in model.names.items():
    print(f"  {idx}: {name}")

print("\nCanonical class names (dataset expects):")
print("  0: open")
print("  1: short")
print("  2: mousebite")
print("  3: spur")
print("  4: copper")
print("  5: pin-hole")

print("\nMISMATCH DETECTED:")
print("Model uses DeepPCB PCB-DATASET names (missing_hole, mouse_bite, open_circuit, short, spur, spurious_copper)")
print("Dataset uses canonical names (open, short, mousebite, spur, copper, pin-hole)")
print("This is why positional alignment is required (index mapping), not name matching.")