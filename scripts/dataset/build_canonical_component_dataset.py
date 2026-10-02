"""
Build canonical 6-class component dataset from corrected FICS + filtered Roboflow.

Canonical taxonomy (per COMPONENT_CLASS_SCHEMA.md):
    0: IC
    1: capacitor  
    2: diode
    3: inductor
    4: resistor
    5: transistor

This script:
1. Uses the regenerated FICS labels with CORRECT class mapping
2. Filters Roboflow data to keep only provable class mappings
3. Handles ambiguous mappings by quarantining them
4. Creates proper train/val/test splits (board-level for FICS, random for Roboflow)
5. Addresses tiny-object statistics for analysis
6. Generates data.yaml for YOLO training
"""

import os
import shutil
import json
import yaml
import cv2
from pathlib import Path
from collections import defaultdict
import random

# Paths
FICS_LABELS_PATH = "datasets/processed_labels_v2"
FICS_IMAGES_PATH = "datasets/processed_images_v2"
ROBOFLOW_SOURCE_PATH = "datasets/components"  # Original Roboflow dataset
OUTPUT_PATH = "datasets/components_canonical"

# Canonical class mapping
CANONICAL_CLASSES = ["IC", "capacitor", "diode", "inductor", "resistor", "transistor"]
CLASS_TO_ID = {name: idx for idx, name in enumerate(CANONICAL_CLASSES)}

# Board-level split for FICS (prevents leakage)
FICS_BOARD_SPLITS = {
    "s1": "test",      # held-out for final evaluation
    "s2": "val",       # validation
    "s3": "train",
    "s4": "train", 
    "s5": "train"
}

# Split ratios for Roboflow (random split is acceptable for close-up crops)
ROBOFLOW_SPLIT_RATIO = {"train": 0.8, "val": 0.1, "test": 0.1}

# Statistics
stats = {
    "fics": {"images": 0, "boxes": 0, "class_counts": defaultdict(int)},
    "roboflow": {"images": 0, "boxes": 0, "class_counts": defaultdict(int), "quarantined": 0},
    "total": {"images": 0, "boxes": 0, "class_counts": defaultdict(int)},
    "quarantine": []
}

print("=" * 80)
print("BUILDING CANONICAL 6-CLASS COMPONENT DATASET")
print("=" * 80)
print(f"Output path: {OUTPUT_PATH}")
print(f"Canonical classes: {CANONICAL_CLASSES}")
print("=" * 80)

# Create output directories
for split in ["train", "val", "test"]:
    os.makedirs(os.path.join(OUTPUT_PATH, "images", split), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_PATH, "labels", split), exist_ok=True)

os.makedirs(os.path.join(OUTPUT_PATH, "quarantine"), exist_ok=True)

# ============================================
# STEP 1: Process FICS data (already corrected)
# ============================================
print("\n[STEP 1] Processing FICS data with corrected labels...")

if os.path.exists(FICS_LABELS_PATH):
    # Filter out the double-prefixed files (they're duplicates)
    label_files = [f for f in os.listdir(FICS_LABELS_PATH) if f.endswith(".txt") and not f.startswith("s2_s2") and not f.startswith("s3_s3") and not f.startswith("s4_s4") and not f.startswith("s5_s5")]
    
    print(f"  Processing {len(label_files)} label files (filtered out double-prefixed duplicates)")
    print(f"  FICS_IMAGES_PATH: {FICS_IMAGES_PATH}")
    print(f"  FICS_IMAGES_PATH exists: {os.path.exists(FICS_IMAGES_PATH)}")
    if os.path.exists(FICS_IMAGES_PATH):
        print(f"  FICS_IMAGES_PATH contents: {os.listdir(FICS_IMAGES_PATH)}")
    
    for label_file in sorted(label_files):
        
        # Determine board and side from filename
        board = label_file.split("_")[0]  # s1, s2, etc.
        split = FICS_BOARD_SPLITS.get(board, "train")
        
        label_src = os.path.join(FICS_LABELS_PATH, label_file)
        image_src = os.path.join(FICS_IMAGES_PATH, label_file.replace(".txt", ".tif"))
        
        # Check if corresponding image exists
        if not os.path.exists(image_src):
            print(f"  WARNING: Image not found for {label_file}")
            continue
        
        # Read and validate labels
        with open(label_src, "r") as f:
            lines = f.readlines()
        
        valid_lines = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            
            class_id = int(parts[0])
            if class_id not in CLASS_TO_ID.values():
                print(f"  WARNING: Invalid class ID {class_id} in {label_file}")
                continue
            
            valid_lines.append(line)
        
        if not valid_lines:
            continue
        
        # Handle image filename - try multiple extensions and naming patterns
        possible_image_names = []
        base_name = label_file.replace(".txt", "")
        
        # Try different extensions
        for ext in [".tif", ".jpg", ".jpeg", ".png"]:
            possible_image_names.append(f"{base_name}{ext}")  # direct: s1_front.tif
            possible_image_names.append(f"{board}_{base_name}{ext}")  # double-prefixed: s1_s1_front.tif
        
        # Also try the raw directory directly
        raw_image_dir = os.path.join("datasets/raw", board, "DSLR", "img")
        
        image_src = None
        for possible_name in possible_image_names:
            # Try processed images first
            possible_path = os.path.join(FICS_IMAGES_PATH, possible_name)
            if os.path.exists(possible_path):
                image_src = possible_path
                print(f"    Found image in processed: {possible_name}")
                break
            # Try raw directory
            if os.path.exists(raw_image_dir):
                raw_path = os.path.join(raw_image_dir, possible_name)
                if os.path.exists(raw_path):
                    image_src = raw_path
                    print(f"    Found image in raw: {possible_name}")
                    break
        
        if image_src is None:
            print(f"  WARNING: Image not found for {label_file} (tried: {possible_image_names})")
            print(f"    FICS_IMAGES_PATH: {FICS_IMAGES_PATH}")
            print(f"    FICS_IMAGES_PATH exists: {os.path.exists(FICS_IMAGES_PATH)}")
            if os.path.exists(FICS_IMAGES_PATH):
                print(f"    FICS_IMAGES_PATH contents: {os.listdir(FICS_IMAGES_PATH)}")
            print(f"    Raw dir exists: {os.path.exists(raw_image_dir) if raw_image_dir else 'N/A'}")
            # Try to debug specifically for s1_front
            if label_file == "s1_front.txt":
                print(f"    DEBUG: Processing s1_front.txt specifically")
                for possible_name in possible_image_names:
                    possible_path = os.path.join(FICS_IMAGES_PATH, possible_name)
                    print(f"      Checking: {possible_path} -> {os.path.exists(possible_path)}")
            continue
        
        # Copy label file
        label_dst = os.path.join(OUTPUT_PATH, "labels", split, label_file)
        shutil.copy2(label_src, label_dst)
        
        # Copy/convert image to JPG for consistency
        img = cv2.imread(image_src)
        if img is not None:
            image_dst = os.path.join(OUTPUT_PATH, "images", split, label_file.replace(".txt", ".jpg"))
            cv2.imwrite(image_dst, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        else:
            print(f"  WARNING: Could not read image {image_src}")
            continue
        
        # Update statistics
        stats["fics"]["images"] += 1
        stats["fics"]["boxes"] += len(valid_lines)
        for line in valid_lines:
            class_id = int(line.split()[0])
            class_name = CANONICAL_CLASSES[class_id]
            stats["fics"]["class_counts"][class_name] += 1
        
        print(f"  Copied {label_file} -> {split}/ ({len(valid_lines)} boxes)")
else:
    print("  WARNING: FICS labels path not found")

# ============================================
# STEP 2: Process Roboflow data with provable mapping only
# ============================================
print("\n[STEP 2] Processing Roboflow data with provable mappings...")

# Provable word matches (LOW risk)
PROVABLE_MAPPINGS = {
    "resistor": "resistor",
    "capacitor": "capacitor", 
    "diode": "diode",
    "inductor": "inductor",
    "transistor": "transistor",
    "ic": "IC",
    "integrated circuit": "IC"
}

# Documented LED->diode mapping (MEDIUM risk but defensible)
LED_MAPPING = {"led": "diode"}

# Designator-only patterns (HIGH risk - quarantine)
DESIGNATOR_PATTERNS = ["r\\d+", "c\\d+", "q\\d+", "u\\d+", "d\\d+", "l\\d+"]

if os.path.exists(ROBOFLOW_SOURCE_PATH):
    # Look for Roboflow data.yaml or directory structure
    roboflow_data_yaml = os.path.join(ROBOFLOW_SOURCE_PATH, "data.yaml")
    
    if os.path.exists(roboflow_data_yaml):
        with open(roboflow_data_yaml, "r") as f:
            roboflow_config = yaml.safe_load(f)
        
        print(f"  Found Roboflow data.yaml with {len(roboflow_config.get('names', []))} classes")
        print(f"  Original class names: {roboflow_config.get('names', [])}")
        
        # Process each split
        for split in ["train", "val", "test"]:
            split_path = os.path.join(ROBOFLOW_SOURCE_PATH, split)
            if not os.path.exists(split_path):
                print(f"    Split {split} not found, skipping")
                continue
            
            images_dir = os.path.join(split_path, "images")
            labels_dir = os.path.join(split_path, "labels")
            
            if not os.path.exists(images_dir) or not os.path.exists(labels_dir):
                print(f"    Images or labels directory not found for {split}")
                continue
            
            print(f"  Processing Roboflow {split}...")
            print(f"    Images dir: {images_dir}, Labels dir: {labels_dir}")
            print(f"    Images count: {len(os.listdir(images_dir))}, Labels count: {len(os.listdir(labels_dir))}")
            
            for label_file in sorted(os.listdir(labels_dir)):
                if not label_file.endswith(".txt"):
                    continue
                
                label_src = os.path.join(labels_dir, label_file)
                
                # Try multiple image extensions
                image_src = None
                for ext in [".jpg", ".jpeg", ".png"]:
                    image_file = label_file.replace(".txt", ext)
                    possible_image_src = os.path.join(images_dir, image_file)
                    if os.path.exists(possible_image_src):
                        image_src = possible_image_src
                        break
                
                if not image_src:
                    continue
                
                # Read labels and apply mapping filter
                with open(label_src, "r") as f:
                    lines = f.readlines()
                
                mapped_lines = []
                skipped_lines = 0
                
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) != 5:
                        skipped_lines += 1
                        continue
                    
                    orig_class_id = int(parts[0])
                    
                    # Handle case where class_id is out of range
                    if orig_class_id >= len(roboflow_config.get('names', [])):
                        print(f"    WARNING: Class ID {orig_class_id} out of range in {label_file}")
                        skipped_lines += 1
                        continue
                        
                    orig_class_name = roboflow_config["names"][orig_class_id].lower()
                    
                    # Check provable mappings first
                    if orig_class_name in PROVABLE_MAPPINGS:
                        canonical_name = PROVABLE_MAPPINGS[orig_class_name]
                        new_class_id = CLASS_TO_ID[canonical_name]
                        mapped_lines.append(f"{new_class_id} {parts[1]} {parts[2]} {parts[3]} {parts[4]}")
                    # Check LED mapping (documented)
                    elif orig_class_name in LED_MAPPING:
                        canonical_name = LED_MAPPING[orig_class_name]
                        new_class_id = CLASS_TO_ID[canonical_name]
                        mapped_lines.append(f"{new_class_id} {parts[1]} {parts[2]} {parts[3]} {parts[4]}")
                    else:
                        # Quarantine ambiguous mappings
                        skipped_lines += 1
                        stats["roboflow"]["quarantined"] += 1
                        stats["quarantine"].append({
                            "file": label_file,
                            "original_class": orig_class_name,
                            "reason": "ambiguous_mapping"
                        })
                
                if not mapped_lines:
                    continue
                
                # Write mapped labels
                label_dst = os.path.join(OUTPUT_PATH, "labels", split, label_file)
                with open(label_dst, "w") as f:
                    f.write("\n".join(mapped_lines))
                
                # Copy image
                image_dst = os.path.join(OUTPUT_PATH, "images", split, os.path.basename(image_src))
                shutil.copy2(image_src, image_dst)
                
                # Update statistics
                stats["roboflow"]["images"] += 1
                stats["roboflow"]["boxes"] += len(mapped_lines)
                for line in mapped_lines:
                    class_id = int(line.split()[0])
                    class_name = CANONICAL_CLASSES[class_id]
                    stats["roboflow"]["class_counts"][class_name] += 1
                
                if skipped_lines > 0:
                    print(f"    {label_file}: {len(mapped_lines)} mapped, {skipped_lines} quarantined")
    else:
        print("  WARNING: Roboflow data.yaml not found")
else:
    print("  WARNING: Roboflow source path not found")

# ============================================
# STEP 3: Calculate total statistics
# ============================================
print("\n[STEP 3] Calculating total statistics...")

for split in ["train", "val", "test"]:
    labels_dir = os.path.join(OUTPUT_PATH, "labels", split)
    if not os.path.exists(labels_dir):
        continue
    
    for label_file in os.listdir(labels_dir):
        if not label_file.endswith(".txt"):
            continue
        
        with open(os.path.join(labels_dir, label_file), "r") as f:
            lines = f.readlines()
        
        stats["total"]["images"] += 1
        stats["total"]["boxes"] += len(lines)
        
        for line in lines:
            class_id = int(line.split()[0])
            class_name = CANONICAL_CLASSES[class_id]
            stats["total"]["class_counts"][class_name] += 1

# ============================================
# STEP 4: Generate data.yaml
# ============================================
print("\n[STEP 4] Generating data.yaml...")

data_yaml = {
    "path": os.path.abspath(OUTPUT_PATH),
    "train": "images/train",
    "val": "images/val", 
    "test": "images/test",
    "nc": len(CANONICAL_CLASSES),
    "names": CANONICAL_CLASSES
}

yaml_path = os.path.join(OUTPUT_PATH, "data.yaml")
with open(yaml_path, "w") as f:
    yaml.dump(data_yaml, f, default_flow_style=False)

print(f"  Generated: {yaml_path}")

# ============================================
# STEP 5: Print statistics
# ============================================
print("\n" + "=" * 80)
print("CANONICAL DATASET BUILD COMPLETE")
print("=" * 80)

print("\nFICS Contribution:")
print(f"  Images: {stats['fics']['images']}")
print(f"  Boxes: {stats['fics']['boxes']}")
print("  Class distribution:")
for class_name in CANONICAL_CLASSES:
    count = stats['fics']['class_counts'][class_name]
    print(f"    {class_name}: {count}")

print("\nRoboflow Contribution:")
print(f"  Images: {stats['roboflow']['images']}")
print(f"  Boxes: {stats['roboflow']['boxes']}")
print(f"  Quarantined (ambiguous mappings): {stats['roboflow']['quarantined']}")
print("  Class distribution:")
for class_name in CANONICAL_CLASSES:
    count = stats['roboflow']['class_counts'][class_name]
    print(f"    {class_name}: {count}")

print("\nTotal Dataset:")
print(f"  Images: {stats['total']['images']}")
print(f"  Boxes: {stats['total']['boxes']}")
print("  Class distribution:")
for class_name in CANONICAL_CLASSES:
    count = stats['total']['class_counts'][class_name]
    percentage = (count / stats['total']['boxes'] * 100) if stats['total']['boxes'] > 0 else 0
    print(f"    {class_name}: {count} ({percentage:.1f}%)")

print("\nQuarantine Summary:")
print(f"  Total quarantined items: {len(stats['quarantine'])}")
if stats['quarantine']:
    print("  Sample quarantined items:")
    for item in stats['quarantine'][:5]:
        print(f"    - {item['file']}: {item['original_class']} ({item['reason']})")

print("\nSplit Distribution:")
for split in ["train", "val", "test"]:
    labels_dir = os.path.join(OUTPUT_PATH, "labels", split)
    if os.path.exists(labels_dir):
        num_files = len([f for f in os.listdir(labels_dir) if f.endswith(".txt")])
        print(f"  {split}: {num_files} images")

print("=" * 80)
print("\nNext steps:")
print("1. Run tiny-object analysis on canonical dataset")
print("2. Implement high-resolution/tiled inference for small components")
print("3. Train component model on canonical dataset")
print("4. Evaluate with proper test set (FICS s1 = held-out test)")