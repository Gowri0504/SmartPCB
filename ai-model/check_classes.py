import pandas as pd
import os

raw = "datasets/raw"

classes = set()

for sample in os.listdir(raw):
    ann = os.path.join(raw, sample, "DSLR", "annotation")

    if os.path.exists(ann):
        for f in os.listdir(ann):
            if f.endswith(".csv"):
                df = pd.read_csv(os.path.join(ann, f))
                classes.update(df["component_type"].dropna().unique())

print("\nComponent Classes Found:\n")
for c in sorted(classes):
    print(c)

print("\nTotal Classes:", len(classes))