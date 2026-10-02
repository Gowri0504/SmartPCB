import os
import json
import pandas as pd

RAW_PATH = r"datasets/raw"
LABEL_PATH = r"datasets/processed/labels"

os.makedirs(LABEL_PATH, exist_ok=True)

# Image dimensions
IMG_WIDTH = 8256
IMG_HEIGHT = 5504

# Class Mapping
CLASS_MAP = {
    "ICs": 0,
    "capacitors": 1,
    "diodes": 2,
    "inductors": 3,
    "resistors": 4,
    "transistors": 5
}

for sample in os.listdir(RAW_PATH):

    annotation_folder = os.path.join(RAW_PATH, sample, "DSLR", "annotation")

    if not os.path.exists(annotation_folder):
        continue

    for csv_file in os.listdir(annotation_folder):

        if not csv_file.endswith(".csv"):
            continue

        csv_path = os.path.join(annotation_folder, csv_file)

        df = pd.read_csv(csv_path)

        labels = {}

        for _, row in df.iterrows():

            image_name = row["image_name"]

            component = str(row["component_type"]).strip()

            if component not in CLASS_MAP:
                continue

            box = json.loads(row["component_location"])

            x = box["x"]
            y = box["y"]
            w = box["width"]
            h = box["height"]

            x_center = (x + w / 2) / IMG_WIDTH
            y_center = (y + h / 2) / IMG_HEIGHT

            width = w / IMG_WIDTH
            height = h / IMG_HEIGHT

            line = f"{CLASS_MAP[component]} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"

            txt_name = image_name.replace(".tif", ".txt")

            if txt_name not in labels:
                labels[txt_name] = []

            labels[txt_name].append(line)

        for txt_name, data in labels.items():

            with open(os.path.join(LABEL_PATH, txt_name), "w") as f:

                f.write("\n".join(data))

            print("Created:", txt_name)

print("--------------------------------")
print("YOLO label conversion completed!")