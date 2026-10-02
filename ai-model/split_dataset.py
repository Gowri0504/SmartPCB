import splitfolders

splitfolders.ratio(
    "datasets/processed",
    output="datasets/components",
    seed=42,
    ratio=(0.7, 0.2, 0.1)
)

print("Dataset split completed.")