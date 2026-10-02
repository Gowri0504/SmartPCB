"""
Run standard Ultralytics evaluation on a random subset of training data.
Fixed seed ensures reproducibility and saves CPU time.
"""

import random
import subprocess
import shutil
import yaml
from pathlib import Path

def get_random_train_subset(dataset_path, n=150, seed=42):
    """Get n random image filenames from train split."""
    random.seed(seed)
    
    train_images_dir = Path(dataset_path) / "train" / "images"
    all_images = list(train_images_dir.glob("*.jpg")) + list(train_images_dir.glob("*.png"))
    
    selected = random.sample(all_images, min(n, len(all_images)))
    return [img.name for img in selected]

def create_subset_yaml(original_yaml, subset_images, output_yaml):
    """Create a temporary data.yaml with only the subset images."""
    import yaml
    
    with open(original_yaml, 'r') as f:
        data = yaml.safe_load(f)
    
    # Override train path to point to our subset (we'll use the same path but filter in script)
    # For Ultralytics, we can't easily filter at the dataset level, so we'll use a different approach:
    # We'll create a symlinked subset directory
    
    return data

def main():
    dataset_path = "datasets/defects"
    subset_size = 150
    seed = 42
    
    print(f"Getting {subset_size} random train images with seed {seed}...")
    selected_images = get_random_train_subset(dataset_path, subset_size, seed)
    print(f"Selected {len(selected_images)} images")
    
    # Create a temporary subset directory
    import shutil
    subset_dir = Path("datasets/defects_train_subset")
    if subset_dir.exists():
        shutil.rmtree(subset_dir)
    
    subset_dir.mkdir()
    (subset_dir / "images").mkdir()
    (subset_dir / "labels").mkdir()
    
    # Copy selected images and their labels
    train_images_dir = Path(dataset_path) / "train" / "images"
    train_labels_dir = Path(dataset_path) / "train" / "labels"
    
    for img_name in selected_images:
        # Copy image
        shutil.copy(train_images_dir / img_name, subset_dir / "images" / img_name)
        # Copy corresponding label
        label_name = img_name.rsplit('.', 1)[0] + '.txt'
        if (train_labels_dir / label_name).exists():
            shutil.copy(train_labels_dir / label_name, subset_dir / "labels" / label_name)
    
    # Create minimal data.yaml for subset
    subset_yaml = {
        'path': str(subset_dir.absolute()),
        'train': 'images',
        'val': 'images',  # Use same for validation in this case
        'test': 'images',
        'nc': 6,
        'names': ['open', 'short', 'mousebite', 'spur', 'copper', 'pin-hole']
    }
    
    import yaml
    with open(subset_dir / "data.yaml", 'w') as f:
        yaml.dump(subset_yaml, f)
    
    print(f"Created subset at {subset_dir}")
    print(f"Running Ultralytics val on subset...")
    
    # Run Ultralytics val
    cmd = [
        "yolo", "val",
        "model=models/defect_best.pt",
        f"data={subset_dir / 'data.yaml'}",
        "split=val",
        "imgsz=640",
        "conf=0.001",
        "iou=0.6",
        "plots=True",
        "project=reports/eval",
        "name=defect_train_subset"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    
    # Save output to file to avoid encoding issues in print
    with open("reports/eval/train_subset_stdout.txt", "w", encoding='utf-8') as f:
        f.write(result.stdout)
    print("Output saved to reports/eval/train_subset_stdout.txt")
    
    if result.returncode != 0:
        with open("reports/eval/train_subset_stderr.txt", "w", encoding='utf-8') as f:
            f.write(result.stderr)
        print(f"Error occurred. Check reports/eval/train_subset_stderr.txt")
    
    # Clean up
    print(f"\nSubset evaluation complete. Temporary subset kept at {subset_dir} for inspection.")

if __name__ == "__main__":
    main()