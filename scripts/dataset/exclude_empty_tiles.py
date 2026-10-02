"""
Exclude the 4 files with 0 boxes from the component dataset.
These tiles have no remaining component annotations after removing class-7 boxes.
"""

import os
from pathlib import Path

# Files to exclude (both image and label)
FILES_TO_EXCLUDE = [
    "datasets/components_unified/test/images/fics_s1_front_x2560_y1536.jpg",
    "datasets/components_unified/test/labels/fics_s1_front_x2560_y1536.txt",
    "datasets/components_unified/train/images/fics_s3_s3_front_x5632_y1024.jpg",
    "datasets/components_unified/train/labels/fics_s3_s3_front_x5632_y1024.txt",
    "datasets/components_unified/train/images/fics_s4_s4_front_x3072_y2560.jpg",
    "datasets/components_unified/train/labels/fics_s4_s4_front_x3072_y2560.txt",
    "datasets/components_unified/train/images/fics_s4_s4_front_x3584_y2560.jpg",
    "datasets/components_unified/train/labels/fics_s4_s4_front_x3584_y2560.txt",
]

def main():
    print("=" * 80)
    print("EXCLUDING 4 FILES WITH 0 BOXES")
    print("=" * 80)
    
    excluded_count = 0
    for file_path_str in FILES_TO_EXCLUDE:
        file_path = Path(file_path_str)
        
        if file_path.exists():
            os.remove(file_path)
            print(f"Removed: {file_path}")
            excluded_count += 1
        else:
            print(f"Not found (already removed?): {file_path}")
    
    print(f"\nTotal files excluded: {excluded_count}")
    print("\nNOTE: These tiles had no remaining component boxes after removing class-7.")
    print("They have been excluded from both train and test splits.")

if __name__ == "__main__":
    main()