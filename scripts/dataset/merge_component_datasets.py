import os
import shutil
import yaml
from tqdm import tqdm

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FICS_TILED = os.path.join(ROOT, "datasets", "fics_tiled")
ROBO_REMAPPED = os.path.join(ROOT, "datasets", "roboflow_remapped")
UNIFIED_DIR = os.path.join(ROOT, "datasets", "components_unified")

CANONICAL_CLASSES = {
    0: "ICs",
    1: "capacitors",
    2: "diodes",
    3: "inductors",
    4: "resistors",
    5: "transistors"
}

def copy_split(src_dir, dest_dir, prefix):
    total_imgs = 0
    total_boxes = 0
    class_counts = {i: 0 for i in range(6)}

    for split in ["train", "val", "test"]:
        src_img_dir = os.path.join(src_dir, split, "images")
        src_lbl_dir = os.path.join(src_dir, split, "labels")

        dest_img_dir = os.path.join(dest_dir, split, "images")
        dest_lbl_dir = os.path.join(dest_dir, split, "labels")
        os.makedirs(dest_img_dir, exist_ok=True)
        os.makedirs(dest_lbl_dir, exist_ok=True)

        if not os.path.exists(src_img_dir):
            continue

        for img_name in os.listdir(src_img_dir):
            if not img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue

            dest_img_name = f"{prefix}_{img_name}"
            shutil.copy2(os.path.join(src_img_dir, img_name), os.path.join(dest_img_dir, dest_img_name))
            total_imgs += 1

            lbl_name = os.path.splitext(img_name)[0] + ".txt"
            src_lbl_path = os.path.join(src_lbl_dir, lbl_name)
            dest_lbl_path = os.path.join(dest_lbl_dir, f"{prefix}_{lbl_name}")

            if os.path.exists(src_lbl_path):
                shutil.copy2(src_lbl_path, dest_lbl_path)
                with open(src_lbl_path, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if parts:
                            cid = int(parts[0])
                            if cid in class_counts:
                                class_counts[cid] += 1
                                total_boxes += 1
            else:
                # empty label file
                with open(dest_lbl_path, "w") as f:
                    pass

    return total_imgs, total_boxes, class_counts

def main():
    print("Merging FICS-PCB tiles and remapped Roboflow into unified component dataset...")
    os.makedirs(UNIFIED_DIR, exist_ok=True)

    fics_imgs, fics_boxes, fics_cls = copy_split(FICS_TILED, UNIFIED_DIR, "fics")
    print(f"FICS-PCB Tiles merged: {fics_imgs} images, {fics_boxes} boxes")

    robo_imgs, robo_boxes, robo_cls = copy_split(ROBO_REMAPPED, UNIFIED_DIR, "robo")
    print(f"Roboflow remapped merged: {robo_imgs} images, {robo_boxes} boxes")

    # Generate data.yaml
    data_yaml = {
        "path": UNIFIED_DIR,
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "names": CANONICAL_CLASSES
    }

    with open(os.path.join(UNIFIED_DIR, "data.yaml"), "w", encoding="utf-8") as f:
        yaml.dump(data_yaml, f, sort_keys=False)

    total_images = fics_imgs + robo_imgs
    total_boxes = fics_boxes + robo_boxes
    total_classes = {i: fics_cls[i] + robo_cls[i] for i in range(6)}

    print("\n==========================================")
    print("Unified PCB Component Dataset Created!")
    print(f"Total images: {total_images}")
    print(f"Total bounding boxes: {total_boxes}")
    print("\nClass distribution:")
    for cid, cname in CANONICAL_CLASSES.items():
        print(f"  Class {cid} ({cname}): {total_classes[cid]} boxes")
    print(f"Saved configuration to: {os.path.join(UNIFIED_DIR, 'data.yaml')}")

if __name__ == "__main__":
    main()
