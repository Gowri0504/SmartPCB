"""
Regenerate FICS-PCB labels from raw CSVs with CORRECT class mapping.

This fixes the critical corruption identified in COMPONENT_DATASET_AUDIT_FINAL.md
where 89% of FICS ground-truth boxes had wrong class IDs.

Correct mapping (verified against canonical taxonomy):
    ICs: 0
    capacitors: 1
    diodes: 2
    inductors: 3
    resistors: 4
    transistors: 5

This script:
1. Reads raw CSV annotations from datasets/raw/
2. Applies the CORRECT class mapping
3. Generates YOLO-format labels with proper coordinates
4. Fixes the filename mismatch issue (double prefix)
5. Preserves ALL classes including transistors (which were dropped before)
"""

import os
import json
import pandas as pd
from pathlib import Path

RAW_PATH = "datasets/raw"
OUTPUT_LABELS_PATH = "datasets/processed_labels_v2"
OUTPUT_IMAGES_PATH = "datasets/processed_images_v2"

os.makedirs(OUTPUT_LABELS_PATH, exist_ok=True)
os.makedirs(OUTPUT_IMAGES_PATH, exist_ok=True)

# Image dimensions (FICS DSLR images are all 8256x5504)
IMG_WIDTH = 8256
IMG_HEIGHT = 5504

# CORRECT class mapping (canonical 6-class taxonomy)
CLASS_MAP = {
    "ICs": 0,
    "capacitors": 1,
    "diodes": 2,
    "inductors": 3,
    "resistors": 4,
    "transistors": 5
}

# Statistics tracking
stats = {
    "total_csv_files": 0,
    "total_boxes": 0,
    "class_counts": {k: 0 for k in CLASS_MAP.keys()},
    "skipped_unknown_classes": 0,
    "generated_label_files": 0
}

print("=" * 80)
print("FICS-PCB LABEL REGENERATION WITH CORRECT CLASS MAPPING")
print("=" * 80)
print(f"Raw path: {RAW_PATH}")
print(f"Output labels: {OUTPUT_LABELS_PATH}")
print(f"Output images: {OUTPUT_IMAGES_PATH}")
print(f"Class mapping: {CLASS_MAP}")
print("=" * 80)

# Process each sample directory (s1, s2, s3, s4, s5)
for sample in sorted(os.listdir(RAW_PATH)):
    sample_path = os.path.join(RAW_PATH, sample)
    if not os.path.isdir(sample_path):
        continue
    
    annotation_folder = os.path.join(sample_path, "DSLR", "annotation")
    image_folder = os.path.join(sample_path, "DSLR", "img")
    
    if not os.path.exists(annotation_folder):
        print(f"Skipping {sample}: no annotation folder")
        continue
    
    print(f"\nProcessing sample: {sample}")
    
    # Process each CSV file in the annotation folder
    for csv_file in sorted(os.listdir(annotation_folder)):
        if not csv_file.endswith(".csv"):
            continue
        
        csv_path = os.path.join(annotation_folder, csv_file)
        stats["total_csv_files"] += 1
        
        print(f"  Processing CSV: {csv_file}")
        
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"    ERROR reading CSV: {e}")
            continue
        
        # Group by image name
        labels_by_image = {}
        
        for _, row in df.iterrows():
            image_name = row["image_name"]
            component_type = str(row["component_type"]).strip()
            
            # Skip unknown classes
            if component_type not in CLASS_MAP:
                stats["skipped_unknown_classes"] += 1
                continue
            
            # Parse bounding box
            try:
                box = json.loads(row["component_location"])
                x = float(box["x"])
                y = float(box["y"])
                w = float(box["width"])
                h = float(box["height"])
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"    WARNING: Invalid box JSON in {image_name}: {e}")
                continue
            
            # Convert to YOLO format (normalized center-x, center-y, width, height)
            x_center = (x + w / 2) / IMG_WIDTH
            y_center = (y + h / 2) / IMG_HEIGHT
            width_norm = w / IMG_WIDTH
            height_norm = h / IMG_HEIGHT
            
            # Clamp to [0, 1] to avoid any normalization issues
            x_center = max(0.0, min(1.0, x_center))
            y_center = max(0.0, min(1.0, y_center))
            width_norm = max(0.0, min(1.0, width_norm))
            height_norm = max(0.0, min(1.0, height_norm))
            
            class_id = CLASS_MAP[component_type]
            
            # YOLO format: class_id x_center y_center width height
            label_line = f"{class_id} {x_center:.6f} {y_center:.6f} {width_norm:.6f} {height_norm:.6f}"
            
            # Use the correct image name (fix double prefix issue)
            # Original: s1_front.tif -> label: s1_front.txt (not s1_s1_front.txt)
            txt_name = image_name.replace(".tif", ".txt")
            
            if txt_name not in labels_by_image:
                labels_by_image[txt_name] = []
            
            labels_by_image[txt_name].append(label_line)
            
            # Update statistics
            stats["total_boxes"] += 1
            stats["class_counts"][component_type] += 1
        
        # Write label files
        for txt_name, label_lines in labels_by_image.items():
            txt_path = os.path.join(OUTPUT_LABELS_PATH, txt_name)
            
            with open(txt_path, "w") as f:
                f.write("\n".join(label_lines))
            
            stats["generated_label_files"] += 1
            print(f"    Generated: {txt_name} with {len(label_lines)} boxes")
        
        # Copy corresponding images (if they exist)
        if os.path.exists(image_folder):
            for txt_name in labels_by_image.keys():
                # Try both .tif and .jpg extensions
                for ext in [".tif", ".jpg"]:
                    img_name = txt_name.replace(".txt", ext)
                    src_img = os.path.join(image_folder, img_name)
                    dst_img = os.path.join(OUTPUT_IMAGES_PATH, img_name)
                    
                    if os.path.exists(src_img):
                        # Copy image (we could also convert to JPG, but keeping original format)
                        import shutil
                        shutil.copy2(src_img, dst_img)
                        print(f"    Copied image: {img_name}")
                        break
                else:
                    # If not found in standard location, try raw directory as fallback
                    raw_img_dir = os.path.join(RAW_PATH, sample, "DSLR", "img")
                    if os.path.exists(raw_img_dir):
                        for ext in [".tif", ".jpg"]:
                            img_name = txt_name.replace(".txt", ext)
                            src_img = os.path.join(raw_img_dir, img_name)
                            dst_img = os.path.join(OUTPUT_IMAGES_PATH, img_name)
                            
                            if os.path.exists(src_img):
                                import shutil
                                shutil.copy2(src_img, dst_img)
                                print(f"    Copied image from raw: {img_name}")
                                break

print("\n" + "=" * 80)
print("LABEL REGENERATION COMPLETE")
print("=" * 80)
print(f"CSV files processed: {stats['total_csv_files']}")
print(f"Total boxes: {stats['total_boxes']}")
print(f"Label files generated: {stats['generated_label_files']}")
print(f"Skipped unknown classes: {stats['skipped_unknown_classes']}")
print("\nClass distribution:")
for class_name, count in stats["class_counts"].items():
    print(f"  {class_name}: {count}")
print("=" * 80)

# Verification: check that the mapping is now correct
print("\nVERIFICATION: Sampling first few lines from s1_front.txt")
sample_file = os.path.join(OUTPUT_LABELS_PATH, "s1_front.txt")
if os.path.exists(sample_file):
    with open(sample_file, "r") as f:
        lines = f.readlines()[:10]
        print("First 10 lines from regenerated s1_front.txt:")
        for i, line in enumerate(lines, 1):
            class_id = line.split()[0]
            print(f"  {i}. Class {class_id}: {line.strip()}")
else:
    print("Sample file not found")

print("\nNext steps:")
print("1. Verify the regenerated labels against the original CSVs")
print("2. Run the dataset audit script to confirm 0 mislabeled boxes")
print("3. Use these labels for building the canonical dataset")