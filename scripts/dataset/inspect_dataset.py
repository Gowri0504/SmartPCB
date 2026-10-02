import os
import csv
import json
import zipfile
import pandas as pd

INVENTORY_CSV = os.path.join(os.path.dirname(__file__), "dataset_inventory.csv")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATASETS_DIR = os.path.join(ROOT, "datasets")

inventory_rows = []

# 1. FICS-PCB DSLR
raw_dir = os.path.join(DATASETS_DIR, "raw")
dslr_images = 0
dslr_annotations = 0
dslr_classes = set()

if os.path.exists(raw_dir):
    for sample in sorted(os.listdir(raw_dir)):
        ann_path = os.path.join(raw_dir, sample, "DSLR", "annotation")
        img_path = os.path.join(raw_dir, sample, "DSLR", "img")
        if os.path.exists(img_path):
            dslr_images += len([f for f in os.listdir(img_path) if f.lower().endswith(('.jpg', '.tif', '.png'))])
        if os.path.exists(ann_path):
            for f in os.listdir(ann_path):
                if f.endswith(".csv"):
                    with open(os.path.join(ann_path, f), "r", encoding="utf-8") as fh:
                        reader = csv.DictReader(fh)
                        for r in reader:
                            ct = (r.get("component_type") or "").strip()
                            if ct:
                                dslr_classes.add(ct)
                                dslr_annotations += 1

inventory_rows.append({
    "dataset_name": "FICS-PCB (DSLR)",
    "category": "A. PCB Component Detection",
    "source": "Florida Institute for Cybersecurity Research (FICS)",
    "images_count": dslr_images,
    "annotations_count": dslr_annotations,
    "classes_count": len(dslr_classes),
    "classes": ", ".join(sorted(dslr_classes)),
    "annotation_format": "CSV (JSON bounding box)",
    "image_dimensions": "~8256x5504",
    "status": "Available in datasets/raw"
})

# 2. FICS-PCB Microscope
mic_images = 0
mic_annotations = 0
mic_classes = set()

if os.path.exists(raw_dir):
    for sample in sorted(os.listdir(raw_dir)):
        mic_ann = os.path.join(raw_dir, sample, "Microscope", "annotation")
        mic_img = os.path.join(raw_dir, sample, "Microscope", "img")
        if os.path.exists(mic_img):
            for root, dirs, files in os.walk(mic_img):
                mic_images += len([f for f in files if f.lower().endswith(('.jpg', '.tif', '.png'))])
        if os.path.exists(mic_ann):
            for root, dirs, files in os.walk(mic_ann):
                for f in files:
                    if f.endswith(".csv"):
                        try:
                            with open(os.path.join(root, f), "r", encoding="utf-8") as fh:
                                reader = csv.DictReader(fh)
                                for r in reader:
                                    ct = (r.get("component_type") or "").strip()
                                    if ct:
                                        mic_classes.add(ct)
                                        mic_annotations += 1
                        except Exception:
                            pass

inventory_rows.append({
    "dataset_name": "FICS-PCB (Microscope)",
    "category": "A. PCB Component Detection",
    "source": "Florida Institute for Cybersecurity Research (FICS)",
    "images_count": mic_images,
    "annotations_count": mic_annotations,
    "classes_count": len(mic_classes),
    "classes": ", ".join(sorted(mic_classes)),
    "annotation_format": "CSV (JSON bounding box)",
    "image_dimensions": "Variable (optical zoom 1x-2x)",
    "status": "Available in datasets/raw (needs YOLO conversion)"
})

# 3. Roboflow PCB-Components.v1495i.yolov11.zip
robo_zip = os.path.join(DATASETS_DIR, "PCB-Components.v1495i.yolov11.zip")
robo_images = 0
robo_annos = 0
robo_nc = 0
robo_classes_sample = ""

if os.path.exists(robo_zip):
    with zipfile.ZipFile(robo_zip) as z:
        names = z.namelist()
        robo_images = len([n for n in names if n.endswith(('.jpg', '.jpeg', '.png'))])
        robo_annos = len([n for n in names if n.endswith('.txt') and not n.endswith('requirements.txt')])
        if "data.yaml" in names:
            import yaml
            ydata = yaml.safe_load(z.read("data.yaml").decode("utf-8"))
            robo_nc = ydata.get("nc", 0)
            names_list = ydata.get("names", [])
            robo_classes_sample = ", ".join(names_list[:6]) + f" ... ({robo_nc} total)"

inventory_rows.append({
    "dataset_name": "PCB-Components (Roboflow v1495i)",
    "category": "A/E. PCB Component Detection",
    "source": "Roboflow Universe (nchowdarym/pcb-components-djhuq)",
    "images_count": robo_images,
    "annotations_count": robo_annos,
    "classes_count": robo_nc,
    "classes": robo_classes_sample,
    "annotation_format": "YOLO TXT (normalized cx, cy, w, h)",
    "image_dimensions": "Various crops / augmented",
    "status": "In ZIP archive (needs remapping to 6 generic classes)"
})

# 4. DeepPCB Defect Dataset
inventory_rows.append({
    "dataset_name": "DeepPCB Defect Dataset",
    "category": "B. PCB Defect Detection",
    "source": "Tang et al. (arXiv 2019 / GitHub: tangsanli5201/DeepPCB)",
    "images_count": "1,500 pairs (1,000 trainval, 500 test)",
    "annotations_count": "3 to 12 defects per 640x640 image",
    "classes_count": 6,
    "classes": "open, short, mousebite, spur, copper, pin-hole",
    "annotation_format": "TXT (x1, y1, x2, y2, type)",
    "image_dimensions": "640x640",
    "status": "Available for download from open-source GitHub repository"
})

# Write CSV
fieldnames = [
    "dataset_name", "category", "source", "images_count",
    "annotations_count", "classes_count", "classes",
    "annotation_format", "image_dimensions", "status"
]

with open(INVENTORY_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(inventory_rows)

print(f"Dataset inventory successfully generated at: {INVENTORY_CSV}")
for row in inventory_rows:
    print(f"\n- {row['dataset_name']} [{row['category']}]: {row['images_count']} images, {row['classes_count']} classes")
