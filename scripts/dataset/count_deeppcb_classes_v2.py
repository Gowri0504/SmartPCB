"""
Count DeepPCB defect classes correctly and compare against paper's Table 4 target counts.

Paper Table 4 target counts:
- open circuit: 1,702
- short: 1,317
- mouse bite: 1,748
- spur: 1,445
- spurious copper: 1,320
- missing hole: 1,320
"""

import os
from collections import Counter

DEEP_PCB_PATH = "datasets/defects"

# Paper Table 4 target counts
PAPER_TARGETS = {
    "open_circuit": 1702,
    "short": 1317,
    "mouse_bite": 1748,
    "spur": 1445,
    "spurious_copper": 1320,
    "missing_hole": 1320
}

# Canonical class mapping (current dataset uses different names)
CANONICAL_CLASSES = {
    0: "open",
    1: "short", 
    2: "mousebite",
    3: "spur",
    4: "copper",
    5: "pin-hole"
}

def count_classes_in_split(split_name):
    """Count class occurrences in a given split (train/val/test)"""
    label_dir = os.path.join(DEEP_PCB_PATH, split_name, "labels")
    if not os.path.exists(label_dir):
        return Counter(), 0
    
    class_counter = Counter()
    total_boxes = 0
    
    for label_file in os.listdir(label_dir):
        if not label_file.endswith('.txt'):
            continue
            
        label_path = os.path.join(label_dir, label_file)
        try:
            with open(label_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        class_id = int(parts[0])
                        class_counter[class_id] += 1
                        total_boxes += 1
        except Exception as e:
            print(f"Error reading {label_path}: {e}")
    
    return class_counter, total_boxes

def compare_with_paper(class_counter, split_name):
    """Compare actual counts with paper targets"""
    print(f"\n{split_name.upper()} SPLIT:")
    print("=" * 80)
    
    # Map to canonical names
    canonical_counter = Counter()
    for class_id, count in class_counter.items():
        canonical_name = CANONICAL_CLASSES.get(class_id, f"unknown_{class_id}")
        canonical_counter[canonical_name] += count
    
    # Map canonical names to paper names
    name_mapping = {
        "open": "open_circuit",
        "short": "short",
        "mousebite": "mouse_bite", 
        "spur": "spur",
        "copper": "spurious_copper",
        "pin-hole": "missing_hole"
    }
    
    paper_counter = Counter()
    for canonical_name, count in canonical_counter.items():
        paper_name = name_mapping.get(canonical_name, canonical_name)
        paper_counter[paper_name] += count
    
    # Compare with targets
    print(f"{'Class':<20} {'Actual':<10} {'Paper Target':<15} {'Difference':<15} {'Match?'}")
    print("-" * 80)
    
    matches = 0
    total_classes = len(PAPER_TARGETS)
    
    for class_name, target_count in PAPER_TARGETS.items():
        actual_count = paper_counter.get(class_name, 0)
        difference = actual_count - target_count
        match = "YES" if actual_count == target_count else "NO"
        if actual_count == target_count:
            matches += 1
        
        print(f"{class_name:<20} {actual_count:<10} {target_count:<15} {difference:+<15} {match}")
    
    print(f"\nClass match rate: {matches}/{total_classes} ({matches/total_classes*100:.1f}%)")
    
    return paper_counter

def main():
    print("=" * 80)
    print("DEEP-PCB DATASET CLASS COUNT VALIDATION")
    print("=" * 80)
    print(f"Paper Table 4 Target Counts:")
    for class_name, count in PAPER_TARGETS.items():
        print(f"  {class_name}: {count}")
    
    # Count classes in each split
    train_counter, train_total = count_classes_in_split("train")
    val_counter, val_total = count_classes_in_split("val")
    test_counter, test_total = count_classes_in_split("test")
    
    # Compare with paper targets for each split
    print("\nCOMPARISON WITH PAPER TABLE 4:")
    print("=" * 80)
    
    train_paper_counter = compare_with_paper(train_counter, "train")
    val_paper_counter = compare_with_paper(val_counter, "val")
    test_paper_counter = compare_with_paper(test_counter, "test")
    
    # Aggregate totals
    total_counter = train_counter + val_counter + test_counter
    total_boxes = train_total + val_total + test_total
    
    print("\nAGGREGATE TOTALS (ALL SPLITS):")
    print("=" * 80)
    print(f"Total boxes: {total_boxes}")
    print(f"Paper total: {sum(PAPER_TARGETS.values())}")
    print(f"Difference: {total_boxes - sum(PAPER_TARGETS.values()):+}")
    
    total_paper_counter = train_paper_counter + val_paper_counter + test_paper_counter
    print(f"\nAggregate class counts vs paper:")
    print(f"{'Class':<20} {'Actual Total':<15} {'Paper Total':<15} {'Difference':<15}")
    print("-" * 80)
    
    matches = 0
    for class_name, target_count in PAPER_TARGETS.items():
        actual_count = total_paper_counter.get(class_name, 0)
        difference = actual_count - target_count
        match = "YES" if actual_count == target_count else "NO"
        if actual_count == target_count:
            matches += 1
        print(f"{class_name:<20} {actual_count:<15} {target_count:<15} {difference:+<15} {match}")
    
    print(f"\nOverall class match rate: {matches}/{len(PAPER_TARGETS)} ({matches/len(PAPER_TARGETS)*100:.1f}%)")
    
    # Split breakdown
    print("\nSPLIT BREAKDOWN:")
    print("=" * 80)
    print(f"{'Split':<10} {'Images':<10} {'Boxes':<10} {'% of Total':<15}")
    print("-" * 80)
    
    train_images = len([f for f in os.listdir(os.path.join(DEEP_PCB_PATH, "train", "images")) if f.endswith('.jpg')])
    val_images = len([f for f in os.listdir(os.path.join(DEEP_PCB_PATH, "val", "images")) if f.endswith('.jpg')])
    test_images = len([f for f in os.listdir(os.path.join(DEEP_PCB_PATH, "test", "images")) if f.endswith('.jpg')])
    
    print(f"{'Train':<10} {train_images:<10} {train_total:<10} {train_total/total_boxes*100:.1f}%")
    print(f"{'Val':<10} {val_images:<10} {val_total:<10} {val_total/total_boxes*100:.1f}%")
    print(f"{'Test':<10} {test_images:<10} {test_total:<10} {test_total/total_boxes*100:.1f}%")
    print(f"{'Total':<10} {train_images+val_images+test_images:<10} {total_boxes:<10} 100.0%")
    
    # Split ratio verification
    print("\nSPLIT RATIO VERIFICATION:")
    print("=" * 80)
    print(f"Actual ratio: {train_images}:{val_images}:{test_images}")
    print(f"Paper ratio (8:1:1): Expected ~{int((train_images+val_images+test_images)*0.8)}:{int((train_images+val_images+test_images)*0.1)}:{int((train_images+val_images+test_images)*0.1)}")
    print(f"Actual percentages: {train_images/(train_images+val_images+test_images)*100:.1f}%:{val_images/(train_images+val_images+test_images)*100:.1f}%:{test_images/(train_images+val_images+test_images)*100:.1f}%")
    print(f"Paper percentages: 80%:10%:10%")

if __name__ == "__main__":
    main()