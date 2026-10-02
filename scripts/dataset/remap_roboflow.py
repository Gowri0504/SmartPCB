import os
import re
import yaml
import zipfile
from tqdm import tqdm

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ZIP_PATH = os.path.join(ROOT, "datasets", "PCB-Components.v1495i.yolov11.zip")
OUTPUT_DIR = os.path.join(ROOT, "datasets", "roboflow_remapped")

# 6 Canonical Classes
CANONICAL_CLASSES = {
    0: "ICs",
    1: "capacitors",
    2: "diodes",
    3: "inductors",
    4: "resistors",
    5: "transistors"
}

def get_canonical_class(name: str):
    nl = name.lower().strip()
    
    # Exclude text labels, markings, jumpers, test points, buttons, headers, etc.
    if nl.startswith("-component text-") or "test point" in nl or "jumper" in nl or "button" in nl or "switch" in nl or "connector" in nl or "header" in nl:
        return None

    # Resistors
    if "resistor" in nl or re.search(r'\br\d+\b', nl):
        return 4
    # Capacitors
    if "capacitor" in nl or re.search(r'\bc\d+\b', nl):
        return 1
    # Diodes & LEDs
    if "diode" in nl or "led" in nl or re.search(r'\bd\d+\b', nl):
        return 2
    # Inductors
    if "inductor" in nl or "choke" in nl or re.search(r'\bl\d+\b', nl):
        return 3
    # Transistors & MOSFETs
    if "transistor" in nl or "mosfet" in nl or re.search(r'\bq\d+\b', nl):
        return 5
    # ICs / Chips / Microcontrollers
    if "ic" in nl or "chip" in nl or "processor" in nl or "eeprom" in nl or re.search(r'\bu\d+\b', nl):
        return 0

    # Direct keyword matches
    if nl in ["resistor", "resistors"]:
        return 4
    if nl in ["capacitor", "capacitors"]:
        return 1
    if nl in ["ic", "ics"]:
        return 0
    if nl in ["diode", "diodes", "led"]:
        return 2
    if nl in ["inductor", "inductors"]:
        return 3
    if nl in ["transistor", "transistors"]:
        return 5

    return None

def main():
    if not os.path.exists(ZIP_PATH):
        print(f"Error: {ZIP_PATH} not found.")
        return

    print("Opening Roboflow ZIP archive...")
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        yaml_content = z.read("data.yaml").decode("utf-8")
        data_cfg = yaml.safe_load(yaml_content)
        original_names = data_cfg.get("names", [])
        
        # Build mapping: orig_id -> canonical_id
        class_map = {}
        mapped_counts = {i: 0 for i in range(6)}
        unmapped = 0
        
        for idx, name in enumerate(original_names):
            c_id = get_canonical_class(name)
            class_map[idx] = c_id
            if c_id is not None:
                mapped_counts[c_id] += 1
            else:
                unmapped += 1

        print("\nRoboflow Class Mapping Summary:")
        for cid, cname in CANONICAL_CLASSES.items():
            print(f"  Class {cid} ({cname}): {mapped_counts[cid]} original categories remapped")
        print(f"  Discarded non-component/text categories: {unmapped}")

        # Extract and remap
        splits = ['train', 'valid', 'test']
        total_kept_images = 0
        total_kept_boxes = 0
        per_class_boxes = {i: 0 for i in range(6)}

        for split in splits:
            target_split = 'val' if split == 'valid' else split
            split_img_dir = os.path.join(OUTPUT_DIR, target_split, "images")
            split_lbl_dir = os.path.join(OUTPUT_DIR, target_split, "labels")
            os.makedirs(split_img_dir, exist_ok=True)
            os.makedirs(split_lbl_dir, exist_ok=True)

            label_prefix = f"{split}/labels/"
            label_files = [n for n in z.namelist() if n.startswith(label_prefix) and n.endswith(".txt")]
            print(f"\nProcessing {split} split ({len(label_files)} label files)...")

            for lbl_path in tqdm(label_files, desc=f"Remapping {split}"):
                lines = z.read(lbl_path).decode("utf-8").strip().splitlines()
                remapped_lines = []

                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        orig_cid = int(parts[0])
                        target_cid = class_map.get(orig_cid)
                        if target_cid is not None:
                            remapped_lines.append(f"{target_cid} " + " ".join(parts[1:5]))
                            per_class_boxes[target_cid] += 1
                            total_kept_boxes += 1

                # If this image has valid mapped component boxes, extract the image and write the new label
                if remapped_lines:
                    fname = os.path.basename(lbl_path)
                    img_name = fname.replace(".txt", ".jpg")
                    img_path_in_zip = f"{split}/images/{img_name}"
                    
                    # Some images might be png
                    if img_path_in_zip not in z.namelist():
                        img_name = fname.replace(".txt", ".png")
                        img_path_in_zip = f"{split}/images/{img_name}"

                    if img_path_in_zip in z.namelist():
                        # Extract image
                        with open(os.path.join(split_img_dir, img_name), "wb") as f_img:
                            f_img.write(z.read(img_path_in_zip))
                        # Write label
                        with open(os.path.join(split_lbl_dir, fname), "w", encoding="utf-8") as f_lbl:
                            f_lbl.write("\n".join(remapped_lines) + "\n")
                        total_kept_images += 1

        # Write data.yaml for roboflow_remapped
        out_yaml = {
            "path": OUTPUT_DIR,
            "train": "train/images",
            "val": "val/images",
            "test": "test/images",
            "names": CANONICAL_CLASSES
        }
        with open(os.path.join(OUTPUT_DIR, "data.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(out_yaml, f, sort_keys=False)

        print("\n==========================================")
        print("Roboflow Remapping Complete!")
        print(f"Total valid images extracted: {total_kept_images}")
        print(f"Total valid bounding boxes: {total_kept_boxes}")
        print("Per-class box counts:")
        for cid, cname in CANONICAL_CLASSES.items():
            print(f"  {cname} ({cid}): {per_class_boxes[cid]}")
        print(f"Saved dataset to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
