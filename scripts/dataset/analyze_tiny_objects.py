"""
Analyze tiny-object statistics in the canonical component dataset.

Tiny = normalized area < (32×32)/(640×640) = 0.0025 (i.e., smaller than 32×32px on a 640 tile)
This analysis will inform the high-resolution/tiled inference strategy.
"""

import os
from collections import defaultdict

CANONICAL_DATASET_PATH = "datasets/components_canonical"
CANONICAL_CLASSES = ["IC", "capacitor", "diode", "inductor", "resistor", "transistor"]

# Tiny object threshold
TINY_THRESHOLD = (32 * 32) / (640 * 640)  # 0.0025

print("=" * 80)
print("TINY-OBJECT ANALYSIS FOR CANONICAL COMPONENT DATASET")
print("=" * 80)
print(f"Tiny threshold: {TINY_THRESHOLD:.6f} (32×32px on 640×640 tile)")
print()

stats = {
    "total_boxes": 0,
    "tiny_boxes": 0,
    "tiny_percentage": 0.0,
    "class_stats": {},
    "box_sizes": []
}

for split in ["train", "val", "test"]:
    labels_dir = os.path.join(CANONICAL_DATASET_PATH, "labels", split)
    if not os.path.exists(labels_dir):
        continue
    
    print(f"Analyzing {split} split...")
    
    for label_file in os.listdir(labels_dir):
        if not label_file.endswith(".txt"):
            continue
        
        with open(os.path.join(labels_dir, label_file), "r") as f:
            lines = f.readlines()
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            
            class_id = int(parts[0])
            x_center = float(parts[1])
            y_center = float(parts[2])
            width = float(parts[3])
            height = float(parts[4])
            
            # Calculate box area (normalized)
            box_area = width * height
            stats["box_sizes"].append(box_area)
            
            # Determine if tiny
            is_tiny = box_area < TINY_THRESHOLD
            stats["total_boxes"] += 1
            if is_tiny:
                stats["tiny_boxes"] += 1
            
            # Track per-class statistics
            class_name = CANONICAL_CLASSES[class_id]
            if class_name not in stats["class_stats"]:
                stats["class_stats"][class_name] = {
                    "total": 0,
                    "tiny": 0,
                    "avg_size": 0.0,
                    "min_size": float('inf'),
                    "max_size": 0.0
                }
            
            stats["class_stats"][class_name]["total"] += 1
            if is_tiny:
                stats["class_stats"][class_name]["tiny"] += 1
            
            stats["class_stats"][class_name]["avg_size"] += box_area
            stats["class_stats"][class_name]["min_size"] = min(stats["class_stats"][class_name]["min_size"], box_area)
            stats["class_stats"][class_name]["max_size"] = max(stats["class_stats"][class_name]["max_size"], box_area)

# Calculate final statistics
stats["tiny_percentage"] = (stats["tiny_boxes"] / stats["total_boxes"] * 100) if stats["total_boxes"] > 0 else 0

# Calculate per-class averages
for class_name in stats["class_stats"]:
    class_stats = stats["class_stats"][class_name]
    if class_stats["total"] > 0:
        class_stats["avg_size"] /= class_stats["total"]
        class_stats["tiny_percentage"] = (class_stats["tiny"] / class_stats["total"] * 100)

print("\n" + "=" * 80)
print("OVERALL STATISTICS")
print("=" * 80)
print(f"Total boxes: {stats['total_boxes']}")
print(f"Tiny boxes: {stats['tiny_boxes']} ({stats['tiny_percentage']:.1f}%)")
print(f"Non-tiny boxes: {stats['total_boxes'] - stats['tiny_boxes']} ({100 - stats['tiny_percentage']:.1f}%)")

print("\n" + "=" * 80)
print("PER-CLASS STATISTICS")
print("=" * 80)
print(f"{'Class':<12} {'Total':<8} {'Tiny':<8} {'Tiny%':<8} {'AvgSize':<10} {'MinSize':<10} {'MaxSize':<10}")
print("-" * 80)

for class_name in CANONICAL_CLASSES:
    if class_name in stats["class_stats"]:
        class_stats = stats["class_stats"][class_name]
        print(f"{class_name:<12} {class_stats['total']:<8} {class_stats['tiny']:<8} {class_stats['tiny_percentage']:<7.1f}% {class_stats['avg_size']:<10.6f} {class_stats['min_size']:<10.6f} {class_stats['max_size']:<10.6f}")

print("\n" + "=" * 80)
print("BOX SIZE DISTRIBUTION")
print("=" * 80)
if stats["box_sizes"]:
    import numpy as np
    box_sizes_array = np.array(stats["box_sizes"])
    print(f"Mean box size: {np.mean(box_sizes_array):.6f}")
    print(f"Median box size: {np.median(box_sizes_array):.6f}")
    print(f"Std box size: {np.std(box_sizes_array):.6f}")
    print(f"Min box size: {np.min(box_sizes_array):.6f}")
    print(f"Max box size: {np.max(box_sizes_array):.6f}")
    
    # Percentiles
    for p in [10, 25, 50, 75, 90]:
        print(f"{p}th percentile: {np.percentile(box_sizes_array, p):.6f}")

print("\n" + "=" * 80)
print("RECOMMENDATIONS FOR HIGH-RESOLUTION/TILED INFERENCE")
print("=" * 80)

if stats["tiny_percentage"] > 50:
    print("CRITICAL: >50% of boxes are tiny objects")
    print("   -> High-resolution inference is mandatory")
    print("   -> Consider tile sizes: 960, 1280, or larger")
    print("   -> Use significant overlap (25-50%) to avoid missing edge components")
elif stats["tiny_percentage"] > 20:
    print("WARNING: >20% of boxes are tiny objects")
    print("   -> High-resolution inference recommended")
    print("   -> Consider tile sizes: 640, 960, or larger")
    print("   -> Use moderate overlap (20-25%)")
else:
    print("Tiny object count is manageable")
    print("   -> Standard 640x640 inference may be sufficient")
    print("   -> Consider 960x960 for improved small object detection")

print("\nRecommended inference configurations to benchmark:")
print("1. Standard: 640×640, stride 480 (25% overlap)")
print("2. High-res: 960×960, stride 640 (33% overlap)")  
print("3. Ultra-high-res: 1280×1280, stride 960 (25% overlap)")
print("4. Conservative: 640×640, stride 320 (50% overlap)")

print("\n" + "=" * 80)