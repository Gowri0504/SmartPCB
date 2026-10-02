import os
import shutil
import yaml
from PIL import Image
from tqdm import tqdm

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_BASE = os.path.join(ROOT, "archive", "temp_deeppcb", "PCBData")
DEST_DIR = os.path.join(ROOT, "datasets", "defects")

# Defect class mapping (DeepPCB 1-indexed to YOLO 0-indexed)
DEFECT_CLASSES = {
    0: "open",
    1: "short",
    2: "mousebite",
    3: "spur",
    4: "copper",
    5: "pin-hole"
}

IMG_SIZE = 640.0

def convert_annotation(txt_path):
    yolo_lines = []
    if not os.path.exists(txt_path):
        return yolo_lines

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 5:
                x1, y1, x2, y2 = map(float, parts[:4])
                orig_type = int(parts[4])

                # DeepPCB uses 1..6
                if 1 <= orig_type <= 6:
                    yolo_cid = orig_type - 1
                    cx = ((x1 + x2) / 2.0) / IMG_SIZE
                    cy = ((y1 + y2) / 2.0) / IMG_SIZE
                    w = (x2 - x1) / IMG_SIZE
                    h = (y2 - y1) / IMG_SIZE

                    # Boundary clamping
                    cx = max(0.0, min(1.0, cx))
                    cy = max(0.0, min(1.0, cy))
                    w = max(0.001, min(1.0, w))
                    h = max(0.001, min(1.0, h))

                    yolo_lines.append(f"{yolo_cid} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

    return yolo_lines

def process_split(file_list, split_name, class_counters):
    img_dest = os.path.join(DEST_DIR, split_name, "images")
    lbl_dest = os.path.join(DEST_DIR, split_name, "labels")
    os.makedirs(img_dest, exist_ok=True)
    os.makedirs(lbl_dest, exist_ok=True)

    saved_count = 0
    box_count = 0

    for item in tqdm(file_list, desc=f"Processing {split_name}"):
        parts = item.split()
        if len(parts) != 2:
            continue
        rel_img, rel_txt = parts[0], parts[1]

        # In DeepPCB, test images are named <id>_test.jpg
        test_rel_img = rel_img.replace(".jpg", "_test.jpg")
        src_img = os.path.join(SRC_BASE, test_rel_img)
        if not os.path.exists(src_img):
            src_img = os.path.join(SRC_BASE, rel_img)
        src_txt = os.path.join(SRC_BASE, rel_txt)

        if not os.path.exists(src_img):
            continue

        yolo_lines = convert_annotation(src_txt)
        img_name = os.path.basename(rel_img)
        txt_name = os.path.basename(rel_txt)

        # Copy image
        shutil.copy2(src_img, os.path.join(img_dest, img_name))

        # Write labels
        if yolo_lines:
            with open(os.path.join(lbl_dest, txt_name), "w", encoding="utf-8") as f:
                f.write("\n".join(yolo_lines) + "\n")
            for l in yolo_lines:
                cid = int(l.split()[0])
                class_counters[cid] += 1
                box_count += 1
        else:
            # Empty annotation file for background/clean
            with open(os.path.join(lbl_dest, txt_name), "w", encoding="utf-8") as f:
                f.write("")

        saved_count += 1

    return saved_count, box_count

def main():
    if not os.path.exists(SRC_BASE):
        print(f"Error: {SRC_BASE} does not exist.")
        return

    trainval_path = os.path.join(SRC_BASE, "trainval.txt")
    test_path = os.path.join(SRC_BASE, "test.txt")

    with open(trainval_path, "r") as f:
        trainval_items = [l.strip() for l in f if l.strip()]

    with open(test_path, "r") as f:
        test_items = [l.strip() for l in f if l.strip()]

    # 85% train, 15% val from trainval
    n_train = int(len(trainval_items) * 0.85)
    train_items = trainval_items[:n_train]
    val_items = trainval_items[n_train:]

    class_counters = {i: 0 for i in range(6)}

    print(f"DeepPCB Splitting: {len(train_items)} train, {len(val_items)} val, {len(test_items)} test")

    tr_imgs, tr_boxes = process_split(train_items, "train", class_counters)
    va_imgs, va_boxes = process_split(val_items, "val", class_counters)
    te_imgs, te_boxes = process_split(test_items, "test", class_counters)

    # Generate data.yaml
    yaml_dict = {
        "path": DEST_DIR,
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "names": DEFECT_CLASSES
    }

    with open(os.path.join(DEST_DIR, "data.yaml"), "w", encoding="utf-8") as f:
        yaml.dump(yaml_dict, f, sort_keys=False)

    print("\n==========================================")
    print("DeepPCB Defect Dataset Successfully Formatted!")
    print(f"Train: {tr_imgs} images, {tr_boxes} boxes")
    print(f"Val:   {va_imgs} images, {va_boxes} boxes")
    print(f"Test:  {te_imgs} images, {te_boxes} boxes")
    print("\nTotal Defect Class Distribution:")
    for cid, cname in DEFECT_CLASSES.items():
        print(f"  Class {cid} ({cname}): {class_counters[cid]}")
    print(f"Saved dataset configuration to {os.path.join(DEST_DIR, 'data.yaml')}")

if __name__ == "__main__":
    main()
