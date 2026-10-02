"""
Fix out-of-range class IDs in components_unified dataset.

From DATA_LEAKAGE_AUDIT.md:
- 13 out-of-range class IDs (index 7 against 6-class yaml)
- 9 in train, 4 in test
- Root cause: likely from merging 10-class Roboflow export into 6-class schema

Strategy: Remove boxes with class ID 7 (invalid for 6-class schema)
"""

import os
from pathlib import Path

def find_out_of_range_labels(dataset_path):
    """Find all label files with class ID 7."""
    out_of_range_files = []
    
    for split in ['train', 'val', 'test']:
        labels_dir = Path(dataset_path) / split / 'labels'
        if not labels_dir.exists():
            continue
            
        for label_file in labels_dir.glob('*.txt'):
            try:
                with open(label_file, 'r') as f:
                    lines = f.readlines()
                
                for line in lines:
                    parts = line.strip().split()
                    if not parts:
                        continue
                    
                    class_id = int(parts[0])
                    if class_id == 7:  # Out of range for 6-class schema (0-5)
                        out_of_range_files.append({
                            'file': str(label_file),
                            'split': split,
                            'class_id': class_id,
                            'count': lines.count(line.strip())
                        })
                        break  # Only need to know file has issue once
            except Exception as e:
                print(f"Error reading {label_file}: {e}")
    
    return out_of_range_files

def remove_out_of_range_boxes(dataset_path, backup=True):
    """Remove boxes with class ID 7 from label files."""
    if backup:
        # Create backup
        backup_dir = Path(dataset_path).parent / f"{Path(dataset_path).name}_backup_before_fix"
        import shutil
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(dataset_path, backup_dir)
        print(f"Backup created at: {backup_dir}")
    
    fixed_count = 0
    for split in ['train', 'val', 'test']:
        labels_dir = Path(dataset_path) / split / 'labels'
        if not labels_dir.exists():
            continue
            
        for label_file in labels_dir.glob('*.txt'):
            try:
                with open(label_file, 'r') as f:
                    lines = f.readlines()
                
                original_count = len(lines)
                # Filter out lines with class ID 7
                filtered_lines = [line for line in lines if not line.strip().startswith('7 ')]
                
                if len(filtered_lines) != original_count:
                    with open(label_file, 'w') as f:
                        f.writelines(filtered_lines)
                    fixed_count += (original_count - len(filtered_lines))
                    print(f"Fixed {label_file}: removed {original_count - len(filtered_lines)} class-7 boxes")
                    
            except Exception as e:
                print(f"Error fixing {label_file}: {e}")
    
    return fixed_count

if __name__ == "__main__":
    dataset_path = "datasets/components_unified"
    
    print("Finding out-of-range class IDs...")
    issues = find_out_of_range_labels(dataset_path)
    print(f"Found {len(issues)} files with class ID 7:")
    for issue in issues:
        print(f"  {issue['split']}/{Path(issue['file']).name}: {issue['count']} boxes")
    
    print("\nRemoving out-of-range boxes...")
    fixed = remove_out_of_range_boxes(dataset_path)
    print(f"Removed {fixed} out-of-range boxes total")
    
    print("\nRe-running validation...")
    os.system("python scripts/dataset/validate_dataset.py")