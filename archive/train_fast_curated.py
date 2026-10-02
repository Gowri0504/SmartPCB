import os
import shutil
from ultralytics import YOLO

ROOT = r"d:\SmartPCB-XAI"
MODELS_DIR = os.path.join(ROOT, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

def train_curated():
    print("=" * 60)
    print("TRAINING HIGH-PERFORMANCE COMPONENT DETECTOR (15 EPOCHS)")
    print("=" * 60)
    comp_yaml = os.path.join(ROOT, "datasets", "components_curated", "data.yaml")
    comp_model = YOLO("yolo11n.pt")
    comp_model.train(
        data=comp_yaml,
        epochs=15,
        batch=16,
        imgsz=512,
        device="cpu",
        workers=0,
        project=os.path.join(ROOT, "experiments"),
        name="comp_fast",
        exist_ok=True,
        verbose=True,
        save=True
    )
    best_comp = os.path.join(ROOT, "experiments", "comp_fast", "weights", "best.pt")
    if os.path.exists(best_comp):
        shutil.copy2(best_comp, os.path.join(MODELS_DIR, "component_best.pt"))
        print("Updated models/component_best.pt successfully!")

    print("\n" + "=" * 60)
    print("TRAINING HIGH-PERFORMANCE DEFECT DETECTOR (15 EPOCHS)")
    print("=" * 60)
    def_yaml = os.path.join(ROOT, "datasets", "defects_curated", "data.yaml")
    def_model = YOLO("yolo11n.pt")
    def_model.train(
        data=def_yaml,
        epochs=15,
        batch=16,
        imgsz=512,
        device="cpu",
        workers=0,
        project=os.path.join(ROOT, "experiments"),
        name="defect_fast",
        exist_ok=True,
        verbose=True,
        save=True
    )
    best_def = os.path.join(ROOT, "experiments", "defect_fast", "weights", "best.pt")
    if os.path.exists(best_def):
        shutil.copy2(best_def, os.path.join(MODELS_DIR, "defect_best.pt"))
        print("Updated models/defect_best.pt successfully!")

if __name__ == "__main__":
    train_curated()
