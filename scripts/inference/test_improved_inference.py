"""
Test the improved high-resolution tiled inference on canonical dataset.

This will validate whether the improved inference configuration
helps with the 94.2% tiny objects in the component dataset.
"""

import os
import sys
import cv2
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from ai.inference.engine import SmartPCBInspectionEngine

CANONICAL_DATASET_PATH = "datasets/components_canonical"
TEST_IMAGE = "datasets/components_canonical/images/test/s1_front.jpg"

print("=" * 80)
print("TESTING IMPROVED HIGH-RESOLUTION TILED INFERENCE")
print("=" * 80)
print(f"Test image: {TEST_IMAGE}")
print()

# Initialize engine
print("Initializing inspection engine...")
engine = SmartPCBInspectionEngine()
print(f"Component model loaded: {engine.component_model_loaded}")
print(f"Defect model loaded: {engine.defect_model_loaded}")
print(f"Device: {engine.device}")
print()

# Test on canonical test image
if os.path.exists(TEST_IMAGE):
    print(f"Testing on {TEST_IMAGE}...")
    start_time = time.time()
    
    result = engine.inspect(
        image_input=TEST_IMAGE,
        conf_threshold=0.18,
        iou_threshold=0.45,
        generate_xai=False  # Skip XAI for faster testing
    )
    
    inference_time = time.time() - start_time
    
    print(f"Inference time: {inference_time:.2f}s")
    print(f"Components detected: {result['component_count']}")
    print(f"Defects detected: {result['defect_count']}")
    print(f"Quality score: {result['quality_score']}")
    print()
    
    # Analyze component detections
    if result['components']:
        print("Component detections:")
        for comp in result['components']:
            print(f"  {comp['class']}: {comp['confidence']:.3f} at {comp['bbox']}")
    
    # Compare with ground truth
    label_file = TEST_IMAGE.replace("images", "labels").replace(".jpg", ".txt")
    if os.path.exists(label_file):
        with open(label_file, "r") as f:
            gt_lines = f.readlines()
        
        print(f"\nGround truth boxes: {len(gt_lines)}")
        print(f"Predicted boxes: {result['component_count']}")
        
        if result['component_count'] > 0:
            detection_rate = result['component_count'] / len(gt_lines) * 100
            print(f"Detection rate: {detection_rate:.1f}%")
    else:
        print("No ground truth label found")
    
    print("\nInference timing breakdown:")
    timing = result.get('inference_timing_ms', {})
    for key, value in timing.items():
        print(f"  {key}: {value:.2f}ms")
    
else:
    print(f"Test image not found: {TEST_IMAGE}")

print("\n" + "=" * 80)
print("IMPROVED INFERENCE TEST COMPLETE")
print("=" * 80)