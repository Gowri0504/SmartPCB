import os
import shutil
from ultralytics import YOLO

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_YAML = os.path.join(ROOT, "datasets", "defects", "data.yaml")
EXPERIMENT_DIR = os.path.join(ROOT, "experiments")
MODELS_DIR = os.path.join(ROOT, "models")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(EXPERIMENT_DIR, exist_ok=True)

def train_defect_model(epochs=5, batch=8, imgsz=512, device="cpu"):
    print("=" * 60)
    print("STARTING REAL TRAINING: PCB Defect Detector (YOLOv11 on DeepPCB)")
    print(f"Data YAML: {DATA_YAML}")
    print(f"Epochs: {epochs} | Batch: {batch} | ImgSz: {imgsz} | Device: {device}")
    print("=" * 60)

    # Initialize YOLOv11 nano model
    model = YOLO("yolo11n.pt")

    # Train
    results = model.train(
        data=DATA_YAML,
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        workers=0,
        patience=5,
        save=True,
        save_period=1,
        project=EXPERIMENT_DIR,
        name="defect_yolo11",
        exist_ok=True,
        verbose=True,
        optimizer="SGD",
        lr0=0.01,
        cos_lr=True,
        mosaic=0.5
    )

    # Copy best weights to models/
    best_pt = os.path.join(EXPERIMENT_DIR, "defect_yolo11", "weights", "best.pt")
    target_pt = os.path.join(MODELS_DIR, "defect_best.pt")
    if os.path.exists(best_pt):
        shutil.copy2(best_pt, target_pt)
        print(f"\nSuccessfully saved best model checkpoint to: {target_pt}")

    print("\nDefect Model Training Complete!")
    return results

if __name__ == "__main__":
    train_defect_model()
