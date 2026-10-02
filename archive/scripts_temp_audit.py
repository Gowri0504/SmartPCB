import os
import csv

raw = 'd:/SmartPCB-XAI/datasets/raw'

for sample in sorted(os.listdir(raw)):
    ann_path = os.path.join(raw, sample, 'DSLR', 'annotation')
    img_path = os.path.join(raw, sample, 'DSLR', 'img')
    if not os.path.exists(ann_path):
        continue

    imgs = [f for f in os.listdir(img_path) if not f.startswith('.')] if os.path.exists(img_path) else []
    csvs = [f for f in os.listdir(ann_path) if f.endswith('.csv')]

    print(f"{sample}:")
    print(f"  DSLR images: {imgs}")

    for csv_file in csvs:
        fpath = os.path.join(ann_path, csv_file)
        with open(fpath, 'r', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)

        classes = {}
        for row in rows:
            ct = (row.get('component_type') or '').strip()
            if ct:
                classes[ct] = classes.get(ct, 0) + 1

        print(f"  CSV {csv_file}: {len(rows)} annotations")
        for k, v in sorted(classes.items(), key=lambda x: -x[1]):
            print(f"    {k}: {v}")
    print()
