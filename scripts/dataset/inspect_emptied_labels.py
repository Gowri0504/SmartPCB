"""
Inspect the 13 label files that were emptied by fix_out_of_range_class_ids.py
For each file, draw the image with any remaining boxes to determine if it contains visible components.
"""

import os
import cv2
from pathlib import Path
import shutil

# The 13 files that had class-7 boxes removed
EMPTIED_FILES = [
    "datasets/components_unified/test/labels/fics_s1_front_x2560_y1536.txt",
    "datasets/components_unified/test/labels/fics_s1_front_x2560_y2048.txt",
    "datasets/components_unified/test/labels/fics_s1_front_x3584_y3072.txt",
    "datasets/components_unified/test/labels/fics_s1_front_x3584_y3584.txt",
    "datasets/components_unified/train/labels/fics_s3_s3_front_x5632_y1024.txt",
    "datasets/components_unified/train/labels/fics_s3_s3_front_x5632_y1536.txt",
    "datasets/components_unified/train/labels/fics_s4_s4_front_x3072_y2560.txt",
    "datasets/components_unified/train/labels/fics_s4_s4_front_x3584_y1536.txt",
    "datasets/components_unified/train/labels/fics_s4_s4_front_x3584_y2560.txt",
    "datasets/components_unified/train/labels/fics_s4_s4_front_x6144_y1536.txt",
    "datasets/components_unified/train/labels/fics_s4_s4_front_x6144_y2048.txt",
    "datasets/components_unified/train/labels/fics_s5_s5_front_x1536_y3584.txt",
    "datasets/components_unified/train/labels/fics_s5_s5_front_x2048_y3584.txt",
]

OUTPUT_DIR = "reports/dataset/emptied_labels"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def draw_labels_on_image(label_path, image_path, output_path):
    """Draw bounding boxes from label file on image."""
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        return
    
    # Read image
    img = cv2.imread(str(image_path))
    if img is None:
        print(f"Failed to read image: {image_path}")
        return
    
    h, w = img.shape[:2]
    
    # Read labels
    with open(label_path, 'r') as f:
        lines = f.readlines()
    
    box_count = len(lines)
    
    # Draw boxes
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        
        class_id = int(parts[0])
        x_center, y_center, box_w, box_h = map(float, parts[1:5])
        
        # Convert to pixel coordinates
        x1 = int((x_center - box_w / 2) * w)
        y1 = int((y_center - box_h / 2) * h)
        x2 = int((x_center + box_w / 2) * w)
        y2 = int((y_center + box_h / 2) * h)
        
        # Draw rectangle
        color = (0, 255, 0) if class_id >= 0 and class_id <= 5 else (0, 0, 255)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(img, f"class_{class_id}", (x1, y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Add info text
    info_text = f"Boxes: {box_count}"
    cv2.putText(img, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Save
    cv2.imwrite(str(output_path), img)
    print(f"Saved: {output_path} (boxes: {box_count})")

def main():
    print("=" * 80)
    print("INSPECTING 13 EMPTIED LABEL FILES")
    print("=" * 80)
    
    results = []
    
    for label_path_str in EMPTIED_FILES:
        label_path = Path(label_path_str)
        
        # Find corresponding image
        image_dir = label_path.parent.parent / "images"
        image_name = label_path.stem + ".jpg"
        image_path = image_dir / image_name
        
        # Check if label file is empty
        with open(label_path, 'r') as f:
            lines = f.readlines()
        box_count = len(lines)
        
        # Draw and save
        output_name = f"{label_path.stem}_annotated.jpg"
        output_path = Path(OUTPUT_DIR) / output_name
        
        draw_labels_on_image(label_path, image_path, output_path)
        
        results.append({
            'label_file': str(label_path),
            'image_file': str(image_path),
            'box_count': box_count,
            'output_file': str(output_path)
        })
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for r in results:
        print(f"{r['label_file']}: {r['box_count']} boxes")
    
    print(f"\nAll annotated images saved to: {OUTPUT_DIR}")
    
    # Decision recommendation
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    empty_count = sum(1 for r in results if r['box_count'] == 0)
    print(f"Files with 0 boxes: {empty_count}/13")
    
    if empty_count == 13:
        print("RECOMMENDATION: EXCLUDE all 13 files from dataset")
        print("Reason: All tiles have no remaining component boxes after removing class-7")
    else:
        print("RECOMMENDATION: EXCLUDE files with 0 boxes, KEEP files with remaining boxes")
        print("Reason: Some tiles still have valid component annotations")

if __name__ == "__main__":
    main()