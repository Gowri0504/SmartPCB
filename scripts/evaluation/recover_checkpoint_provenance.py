"""
Recover training provenance from models/defect_best.pt
Uses torch.load with weights_only=False on trusted local file.
"""

import torch
import json

print("Loading checkpoint with weights_only=False (trusted local file)...")
try:
    checkpoint = torch.load("models/defect_best.pt", weights_only=False, map_location='cpu')
    
    print("\nCheckpoint keys:", list(checkpoint.keys()))
    
    # Extract available metadata
    metadata = {}
    
    if 'train_args' in checkpoint:
        print("\n=== TRAIN_ARGS ===")
        train_args = checkpoint['train_args']
        print(json.dumps(train_args, indent=2, default=str))
        metadata['train_args'] = {k: str(v) for k, v in train_args.items()}
    
    if 'args' in checkpoint:
        print("\n=== ARGS ===")
        args = checkpoint['args']
        print(json.dumps(args, indent=2, default=str))
        metadata['args'] = {k: str(v) for k, v in args.items()}
    
    if 'epoch' in checkpoint:
        print(f"\nEpoch: {checkpoint['epoch']}")
        metadata['epoch'] = checkpoint['epoch']
    
    if 'date' in checkpoint:
        print(f"Date: {checkpoint['date']}")
        metadata['date'] = checkpoint['date']
    
    if 'model' in checkpoint:
        print(f"\nModel type: {type(checkpoint['model'])}")
        metadata['model_type'] = str(type(checkpoint['model']))
    
    # Check for Ultralytics model metadata
    if hasattr(checkpoint, 'model') and hasattr(checkpoint.model, 'args'):
        print("\n=== MODEL.ARGS ===")
        model_args = checkpoint['model'].args
        print(json.dumps(model_args, indent=2, default=str))
        metadata['model_args'] = {k: str(v) for k, v in model_args.items()}
    
    # Save metadata
    with open("reports/eval/defect_checkpoint_provenance.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print("\nMetadata saved to reports/eval/defect_checkpoint_provenance.json")
    
except Exception as e:
    print(f"Error loading checkpoint: {e}")
    print("This is expected if PyTorch 2.6+ blocks the load even with weights_only=False")