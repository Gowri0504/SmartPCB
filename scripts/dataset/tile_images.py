import os
import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROC_IMG = os.path.join(ROOT, "datasets", "processed", "images")
PROC_LBL = os.path.join(ROOT, "datasets", "processed", "labels")
RAW_DIR = os.path.join(ROOT, "datasets", "raw")
OUTPUT_DIR = os.path.join(ROOT, "datasets", "fics_tiled")

TILE_SIZE = 640
STRIDE = 512  # 128px overlap

# Board-level split to completely prevent data leakage
# Boards s1 and s2 for test and validation
# Boards s3, s4, s5 for training
BOARD_SPLIT = {
    "s1": "test",
    "s2": "val",
    "s3": "train",
    "s4": "train",
    "s5": "train"
}

def get_board_id(filename: str):
    for bid in ["s1", "s2", "s3", "s4", "s5"]:
        if bid in filename:
            return bid
    return "train"

def tile_single_image(img_path, label_path, split, output_dir):
    img = Image.open(img_path)
    img_w, img_h = img.size

    # Read original normalized YOLO labels
    boxes = []
    if os.path.exists(label_path):
        with open(label_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    cid = int(parts[0])
                    cx, cy, nw, nh = map(float, parts[1:5])
                    # Absolute pixels
                    bx1 = (cx - nw / 2.0) * img_w
                    by1 = (cy - nh / 2.0) * img_h
                    bx2 = (cx + nw / 2.0) * img_w
                    by2 = (cy + nh / 2.0) * img_h
                    boxes.append((cid, bx1, by1, bx2, by2, nw * nh * img_w * img_h))

    base_name = os.path.splitext(os.path.basename(img_path))[0]
    out_img_dir = os.path.join(output_dir, split, "images")
    out_lbl_dir = os.path.join(output_dir, split, "labels")
    os.makedirs(out_img_dir, exist_ok=True)
    os.makedirs(out_lbl_dir, exist_ok=True)

    generated_tiles = 0
    generated_boxes = 0

    # Grid tiling
    x_steps = list(range(0, img_w - TILE_SIZE + 1, STRIDE))
    if x_steps[-1] < img_w - TILE_SIZE:
        x_steps.append(img_w - TILE_SIZE)

    y_steps = list(range(0, img_h - TILE_SIZE + 1, STRIDE))
    if y_steps[-1] < img_h - TILE_SIZE:
        y_steps.append(img_h - TILE_SIZE)

    for y in y_steps:
        for x in x_steps:
            tx1, ty1 = x, y
            tx2, ty2 = x + TILE_SIZE, y + TILE_SIZE

            tile_labels = []
            for cid, bx1, by1, bx2, by2, orig_area in boxes:
                # Calculate overlap
                ix1 = max(bx1, tx1)
                iy1 = max(by1, ty1)
                ix2 = min(bx2, tx2)
                iy2 = min(by2, ty2)

                if ix2 > ix1 and iy2 > iy1:
                    inter_area = (ix2 - ix1) * (iy2 - iy1)
                    # Keep if at least 35% of the component is in this tile
                    if (inter_area / max(1.0, orig_area)) >= 0.35:
                        # Convert to tile-relative coordinates
                        tcx = ((ix1 + ix2) / 2.0 - tx1) / TILE_SIZE
                        tcy = ((iy1 + iy2) / 2.0 - ty1) / TILE_SIZE
                        tw = (ix2 - ix1) / TILE_SIZE
                        th = (iy2 - iy1) / TILE_SIZE

                        # Valid bbox checks
                        if tw > 0.005 and th > 0.005:
                            tile_labels.append(f"{cid} {tcx:.6f} {tcy:.6f} {tw:.6f} {th:.6f}")

            # Only save tile if it has components (or 2% of background for training diversity)
            save_tile = False
            if tile_labels:
                save_tile = True
            elif split == "train" and np.random.rand() < 0.02:
                save_tile = True

            if save_tile:
                tile_crop = img.crop((tx1, ty1, tx2, ty2))
                tile_name = f"{base_name}_x{tx1}_y{ty1}"
                tile_crop.save(os.path.join(out_img_dir, f"{tile_name}.jpg"), quality=95)

                if tile_labels:
                    with open(os.path.join(out_lbl_dir, f"{tile_name}.txt"), "w", encoding="utf-8") as f:
                        f.write("\n".join(tile_labels) + "\n")
                    generated_boxes += len(tile_labels)

                generated_tiles += 1

    return generated_tiles, generated_boxes

def main():
    print("Starting FICS-PCB DSLR Tiling with Leakage Prevention...")
    
    # Ensure s1_front image is available in processed
    # s1_front.jpg is already in datasets/raw/s1/DSLR/img/s1_front.jpg
    s1_raw_img = os.path.join(RAW_DIR, "s1", "DSLR", "img", "s1_front.jpg")
    s1_target = os.path.join(PROC_IMG, "s1_front.jpg")
    if os.path.exists(s1_raw_img) and not os.path.exists(s1_target):
        import shutil
        shutil.copy2(s1_raw_img, s1_target)
        print("Copied s1_front.jpg to processed images.")

    # List all processed images
    image_files = [f for f in os.listdir(PROC_IMG) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    print(f"Found {len(image_files)} full-resolution DSLR images in {PROC_IMG}")

    total_tiles = 0
    total_boxes = 0

    for img_file in tqdm(image_files, desc="Tiling boards"):
        img_path = os.path.join(PROC_IMG, img_file)
        
        # Match label file
        # name could be s2_s2_front.jpg -> s2_front.txt or s1_front.jpg -> s1_front.txt
        label_candidates = [
            img_file.replace(".jpg", ".txt").replace(".png", ".txt"),
            img_file.replace("s2_s2_", "s2_").replace("s3_s3_", "s3_").replace("s4_s4_", "s4_").replace("s5_s5_", "s5_").replace(".jpg", ".txt")
        ]
        
        label_path = None
        for cand in label_candidates:
            cand_path = os.path.join(PROC_LBL, cand)
            if os.path.exists(cand_path):
                label_path = cand_path
                break

        board_id = get_board_id(img_file)
        split = BOARD_SPLIT.get(board_id, "train")

        tiles, bboxes = tile_single_image(img_path, label_path, split, OUTPUT_DIR)
        print(f"  {img_file} (Board: {board_id} -> Split: {split}): Generated {tiles} tiles, {bboxes} bounding boxes")
        total_tiles += tiles
        total_boxes += bboxes

    # Create data.yaml
    yaml_content = f"""path: {OUTPUT_DIR}
train: train/images
val: val/images
test: test/images

names:
  0: ICs
  1: capacitors
  2: diodes
  3: inductors
  4: resistors
  5: transistors
"""
    with open(os.path.join(OUTPUT_DIR, "data.yaml"), "w", encoding="utf-8") as f:
        f.write(yaml_content)

    print("\n==========================================")
    print("FICS-PCB Tiling Complete!")
    print(f"Total tiles generated: {total_tiles}")
    print(f"Total valid bounding boxes: {total_boxes}")
    print(f"Output saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
