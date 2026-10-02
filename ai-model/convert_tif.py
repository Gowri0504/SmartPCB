from PIL import Image
import os

RAW_DATASET = r"datasets/raw"
OUTPUT = r"datasets/processed/images"

os.makedirs(OUTPUT, exist_ok=True)

count = 0

for sample in os.listdir(RAW_DATASET):

    dslr_path = os.path.join(RAW_DATASET, sample, "DSLR", "img")

    if not os.path.exists(dslr_path):
        continue

    for file in os.listdir(dslr_path):

        if file.lower().endswith((".tif", ".tiff")):

            image = Image.open(os.path.join(dslr_path, file))

            save_name = sample + "_" + file.replace(".tif", ".jpg").replace(".tiff", ".jpg")

            image.save(os.path.join(OUTPUT, save_name))

            count += 1

            print("Converted:", save_name)

print("--------------------------------")
print("Total Images:", count)