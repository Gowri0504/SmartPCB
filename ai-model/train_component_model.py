from ultralytics import YOLO

model = YOLO("yolo11n.pt")

model.train(
    data="datasets/components/data.yaml",
    epochs=100,
    imgsz=640,
    batch=4,
    workers=2,
    project="runs",
    name="pcb_component_detection",
    device="cpu"
)