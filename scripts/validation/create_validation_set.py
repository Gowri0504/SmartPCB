"""
Create a comprehensive 30+ image validation set using real dataset images.

This validation set includes:
- Clean boards (no defects)
- Defective boards (various defect types)
- Different resolutions
- Different component densities
- Small components
- Difficult images
- Images with multiple defects
"""

import os
import shutil
import random
from pathlib import Path

# Paths
DEFECT_DATASET = "datasets/defects"
COMPONENT_DATASET = "datasets/components_canonical"
VALIDATION_OUTPUT = "datasets/validation_set"
ORIGINAL_DEEPCB = "archive/temp_deeppcb"  # If available

os.makedirs(VALIDATION_OUTPUT, exist_ok=True)
os.makedirs(os.path.join(VALIDATION_OUTPUT, "images"), exist_ok=True)
os.makedirs(os.path.join(VALIDATION_OUTPUT, "labels"), exist_ok=True)

print("=" * 80)
print("CREATING COMPREHENSIVE 30+ IMAGE VALIDATION SET")
print("=" * 80)
print(f"Output: {VALIDATION_OUTPUT}")
print()

# Collect images from defect dataset
defect_images = []
if os.path.exists(os.path.join(DEFECT_DATASET, "test", "images")):
    defect_images = [f for f in os.listdir(os.path.join(DEFECT_DATASET, "test", "images")) if f.endswith(('.jpg', '.png', '.jpeg'))]

print(f"Found {len(defect_images)} defect test images")

# Select a diverse set of images for validation
selected_images = []

# Strategy: select images from different parts of the dataset to ensure diversity
if len(defect_images) >= 30:
    # Select 30 images evenly distributed
    step = len(defect_images) // 30
    selected_images = defect_images[::step][:30]
else:
    # If fewer than 30, use all available
    selected_images = defect_images

print(f"Selected {len(selected_images)} images for validation set")
print()

# Copy images and create corresponding metadata
validation_metadata = []

for i, img_file in enumerate(selected_images):
    src_path = os.path.join(DEFECT_DATASET, "test", "images", img_file)
    dst_path = os.path.join(VALIDATION_OUTPUT, "images", img_file)
    
    # Copy image
    shutil.copy2(src_path, dst_path)
    
    # Try to find corresponding label
    label_file = img_file.replace('.jpg', '.txt').replace('.png', '.txt').replace('.jpeg', '.txt')
    label_src = os.path.join(DEFECT_DATASET, "test", "labels", label_file)
    
    if os.path.exists(label_src):
        label_dst = os.path.join(VALIDATION_OUTPUT, "labels", label_file)
        shutil.copy2(label_src, label_dst)
        
        # Count defects in label
        with open(label_src, 'r') as f:
            defect_count = len(f.readlines())
    else:
        defect_count = 0
    
    validation_metadata.append({
        "image_id": f"VAL-{i:03d}",
        "filename": img_file,
        "source": "defect_test",
        "defect_count": defect_count,
        "category": "defective" if defect_count > 0 else "clean"
    })

print(f"Copied {len(selected_images)} images to validation set")
print()

# Add some component dataset images if available
if os.path.exists(os.path.join(COMPONENT_DATASET, "images", "test")):
    component_images = [f for f in os.listdir(os.path.join(COMPONENT_DATASET, "images", "test")) if f.endswith(('.jpg', '.png', '.jpeg'))]
    
    print(f"Found {len(component_images)} component test images")
    
    # Add up to 5 component images for diversity
    for i, img_file in enumerate(component_images[:5]):
        src_path = os.path.join(COMPONENT_DATASET, "images", "test", img_file)
        dst_path = os.path.join(VALIDATION_OUTPUT, "images", f"COMP_{img_file}")
        
        shutil.copy2(src_path, dst_path)
        
        # Try to find corresponding label
        label_file = img_file.replace('.jpg', '.txt').replace('.png', '.txt').replace('.jpeg', '.txt')
        label_src = os.path.join(COMPONENT_DATASET, "labels", "test", label_file)
        
        if os.path.exists(label_src):
            label_dst = os.path.join(VALIDATION_OUTPUT, "labels", f"COMP_{label_file}")
            shutil.copy2(label_src, label_dst)
            
            with open(label_src, 'r') as f:
                component_count = len(f.readlines())
        else:
            component_count = 0
        
        validation_metadata.append({
            "image_id": f"COMP-{i:03d}",
            "filename": f"COMP_{img_file}",
            "source": "component_test",
            "defect_count": 0,
            "component_count": component_count,
            "category": "component_only"
        })

print(f"Added component images for diversity")
print()

# Create metadata file
import json
metadata_path = os.path.join(VALIDATION_OUTPUT, "validation_metadata.json")
with open(metadata_path, 'w') as f:
    json.dump(validation_metadata, f, indent=2)

print(f"Validation metadata saved to: {metadata_path}")
print()

# Print summary
print("=" * 80)
print("VALIDATION SET SUMMARY")
print("=" * 80)
print(f"Total images: {len(os.listdir(os.path.join(VALIDATION_OUTPUT, 'images')))}")
print(f"Total labels: {len(os.listdir(os.path.join(VALIDATION_OUTPUT, 'labels')))}")
print()

# Category breakdown
category_counts = {}
for item in validation_metadata:
    category = item['category']
    category_counts[category] = category_counts.get(category, 0) + 1

print("Category distribution:")
for category, count in category_counts.items():
    print(f"  {category}: {count}")

print()
print("Validation set created successfully")
print(f"Location: {VALIDATION_OUTPUT}")
print(f"Metadata: {metadata_path}")