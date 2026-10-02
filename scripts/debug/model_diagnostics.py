import os
import sys
import time
import json
import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from ultralytics import YOLO

MODELS_DIR = os.path.join(ROOT, "models")
DEBUG_DIR = os.path.join(ROOT, "debug_outputs")
DATASETS_DIR = os.path.join(ROOT, "datasets")

os.makedirs(DEBUG_DIR, exist_ok=True)


def inspect_model(model_path, model_label):
    print(f"\n{'=' * 80}")
    print(f"MODEL INSPECTION: {model_label}")
    print(f"{'=' * 80}")
    print(f"Path: {model_path}")
    print(f"Exists: {os.path.exists(model_path)}")

    if not os.path.exists(model_path):
        print(f"  [WARNING] Model file does not exist!")
        return None

    size_mb = os.path.getsize(model_path) / (1024 * 1024)
    print(f"File Size: {size_mb:.2f} MB")

    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"  [ERROR] Failed to load model: {e}")
        return None

    total_params = sum(p.numel() for p in model.model.parameters())
    trainable = sum(p.numel() for p in model.model.parameters() if p.requires_grad)
    print(f"Total Parameters: {total_params:,}")
    print(f"Trainable Parameters: {trainable:,}")

    names = model.names if hasattr(model, 'names') else {}
    num_classes = len(names)
    print(f"Number of Classes: {num_classes}")
    print(f"Class Names: {json.dumps(names, indent=2)}")

    arch = "Unknown"
    try:
        arch_name = type(model.model).__name__
        first_layer = list(model.model.children())[0] if hasattr(model.model, 'children') else None
        arch = f"{arch_name}"
    except Exception:
        pass
    print(f"Architecture: {arch}")

    try:
        ckpt = model.ckpt if hasattr(model, 'ckpt') else None
        if ckpt:
            epoch = ckpt.get('epoch', 'N/A')
            print(f"Checkpoint Epoch: {epoch}")
            for k in ['best_fitness', 'fitness']:
                if k in ckpt:
                    print(f"  {k}: {ckpt[k]}")
            if 'train_args' in ckpt:
                args = ckpt['train_args']
                print("Training Args:")
                for key in ['imgsz', 'batch', 'epochs', 'lr0', 'optimizer', 'data']:
                    if key in args:
                        print(f"  {key}: {args[key]}")
    except Exception as e:
        print(f"  Could not extract ckpt metadata: {e}")

    return {
        "path": model_path,
        "size_mb": size_mb,
        "total_params": total_params,
        "num_classes": num_classes,
        "class_names": names,
        "model_obj": model
    }


def find_test_images(dataset_subdir, max_images=5):
    imgs = []
    search_dirs = [
        os.path.join(DATASETS_DIR, dataset_subdir, "test", "images"),
        os.path.join(DATASETS_DIR, dataset_subdir, "val", "images"),
    ]
    for d in search_dirs:
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    imgs.append(os.path.join(d, f))
                    if len(imgs) >= max_images:
                        return imgs
    return imgs


def draw_boxes(img, detections, color=(0, 255, 0), label_prefix=""):
    h, w = img.shape[:2]
    for det in detections:
        cls_id = det.get('class_id', 0)
        cls_name = det.get('class', f"cls_{cls_id}")
        conf = det.get('confidence', 0.0)
        x1, y1, x2, y2 = [int(v) for v in det.get('bbox', [0, 0, w, h])]
        x1 = max(0, min(w - 1, x1))
        y1 = max(0, min(h - 1, y1))
        x2 = max(0, min(w - 1, x2))
        y2 = max(0, min(h - 1, y2))
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        label = f"{label_prefix}{cls_name} {conf:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(img, label, (x1 + 2, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    return img


def run_inference(model_info, test_images, model_label, conf_thresh=0.15, imgsz=640):
    print(f"\n{'=' * 80}")
    print(f"INFERENCE TEST: {model_label}  (conf={conf_thresh}, imgsz={imgsz})")
    print(f"{'=' * 80}")

    model = model_info["model_obj"]
    results_summary = []
    total_detections = 0

    header = f"{'IMAGE':<40} {'CLASS':<12} {'CONF':<7} {'X1':<7} {'Y1':<7} {'X2':<7} {'Y2':<7} {'INFERENCE_MS':<14}"
    print(header)
    print("-" * len(header))

    for img_path in test_images:
        img_name = os.path.basename(img_path)
        img_bgr = cv2.imread(img_path)
        if img_bgr is None:
            print(f"  [SKIP] Cannot read: {img_path}")
            continue

        h_orig, w_orig = img_bgr.shape[:2]

        t0 = time.perf_counter()
        try:
            preds = model.predict(source=img_bgr, conf=conf_thresh, imgsz=imgsz,
                                  device="cpu", verbose=False)
        except Exception as e:
            print(f"  [ERROR] Inference failed on {img_name}: {e}")
            continue
        t1 = time.perf_counter()
        inf_ms = (t1 - t0) * 1000.0

        image_detections = []
        for r in preds:
            for i in range(len(r.boxes)):
                xyxy = r.boxes.xyxy[i].cpu().numpy().tolist()
                conf = float(r.boxes.conf[i].cpu().numpy())
                cls_id = int(r.boxes.cls[i].cpu().numpy())
                cls_name = r.names.get(cls_id, f"class_{cls_id}")
                x1, y1, x2, y2 = [round(v, 2) for v in xyxy]
                det = {
                    "image": img_name,
                    "class": cls_name,
                    "class_id": cls_id,
                    "confidence": round(conf, 4),
                    "bbox": [x1, y1, x2, y2],
                    "inference_ms": round(inf_ms, 2)
                }
                image_detections.append(det)
                total_detections += 1
                print(f"{img_name:<40} {cls_name:<12} {conf:.4f}  {x1:<7} {y1:<7} {x2:<7} {y2:<7} {inf_ms:<14.2f}")

        if not image_detections:
            print(f"{img_name:<40} {'(NONE)':<12} {'-':<7} {'-':<7} {'-':<7} {'-':<7} {'-':<7} {inf_ms:<14.2f}")

        annotated = img_bgr.copy()
        color = (0, 200, 255) if "COMPONENT" in model_label else (0, 0, 255)
        annotated = draw_boxes(annotated, image_detections, color=color)
        prefix = "COMP" if "COMPONENT" in model_label else "DEFECT"
        out_path = os.path.join(DEBUG_DIR, f"{prefix}_{img_name}")
        cv2.imwrite(out_path, annotated)
        print(f"  -> Saved annotated image: {out_path}  ({len(image_detections)} detections)")

        results_summary.append({
            "image": img_name,
            "dimensions": [w_orig, h_orig],
            "num_detections": len(image_detections),
            "inference_ms": round(inf_ms, 2),
            "detections": image_detections
        })

    print("\n" + "-" * 60)
    print(f"Total detections across {len(test_images)} images: {total_detections}")
    avg_ms = np.mean([r["inference_ms"] for r in results_summary]) if results_summary else 0
    avg_per_img = total_detections / len(results_summary) if results_summary else 0
    print(f"Avg inference time: {avg_ms:.2f} ms | Avg detections/image: {avg_per_img:.2f}")

    return results_summary


def run_full_pipeline_test(img_path, component_info, defect_info, conf=0.20):
    """Run the full inspection pipeline on a single image (independent of FastAPI)."""
    from ai.inference.engine import SmartPCBInspectionEngine

    print(f"\n{'=' * 80}")
    print(f"FULL PIPELINE TEST (using SmartPCBInspectionEngine)")
    print(f"Image: {img_path}")
    print(f"{'=' * 80}")

    img_bgr = cv2.imread(img_path)
    if img_bgr is None:
        print(f"Cannot read image. Aborting pipeline test.")
        return None

    try:
        engine = SmartPCBInspectionEngine(
            component_model_path=component_info["path"],
            defect_model_path=defect_info["path"]
        )
    except Exception as e:
        print(f"[ERROR] Failed to init inspection engine: {e}")
        import traceback
        traceback.print_exc()
        return None

    t0 = time.perf_counter()
    result = engine.inspect(img_bgr, conf_threshold=conf, generate_xai=True)
    t1 = time.perf_counter()
    total_ms = (t1 - t0) * 1000.0

    print(f"\n--- PIPELINE RESULT ---")
    print(f"Inspection ID: {result.get('inspection_id')}")
    print(f"Image dims: {result.get('image_dimensions')}")
    print(f"Components detected: {len(result.get('components', []))}")
    for c in result.get('components', []):
        print(f"  COMPONENT: id={c['id']} class={c['class']} conf={c['confidence']:.4f} bbox={c['bbox']}")
    print(f"Defects detected: {len(result.get('defects', []))}")
    for d in result.get('defects', []):
        sev = d.get('severity', {})
        print(f"  DEFECT: id={d['id']} class={d['class']} conf={d['confidence']:.4f} "
              f"severity={sev.get('level')}({sev.get('score')}) bbox={d['bbox']}")
    qs = result.get('quality_score', {})
    print(f"\nQuality Score: score={qs.get('overall_score')} status={qs.get('status')} "
          f"grade={qs.get('grade')} defect_count={qs.get('defect_count', 0)}")
    print(f"Recommendations: {len(result.get('recommendations', []))}")
    xai = result.get('xai', {})
    print(f"XAI overlay generated: {'overlay_base64' in xai or result.get('xai_overlay_image') is not None}")
    print(f"Total pipeline time: {total_ms:.2f} ms")

    annotated = result.get('annotated_image')
    if annotated is not None:
        out_name = f"PIPELINE_{os.path.basename(img_path)}"
        cv2.imwrite(os.path.join(DEBUG_DIR, out_name), annotated)
        print(f"Pipeline preview saved: {os.path.join(DEBUG_DIR, out_name)}")
    xai_overlay = result.get('xai_overlay_image')
    if xai_overlay is not None:
        out_name = f"PIPELINE_XAI_{os.path.basename(img_path)}"
        cv2.imwrite(os.path.join(DEBUG_DIR, out_name), xai_overlay)
        print(f"Pipeline XAI overlay saved: {os.path.join(DEBUG_DIR, out_name)}")

    json_out = {k: (v.tolist() if hasattr(v, 'tolist') else v) for k, v in result.items() if k not in ['annotated_image', 'xai_overlay_image']}
    json_path = os.path.join(DEBUG_DIR, f"PIPELINE_{os.path.splitext(os.path.basename(img_path))[0]}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_out, f, indent=2, default=str)
    print(f"Pipeline JSON saved: {json_path}")

    return result


def main():
    comp_path = os.path.join(MODELS_DIR, "component_best.pt")
    defect_path = os.path.join(MODELS_DIR, "defect_best.pt")

    comp_info = inspect_model(comp_path, "COMPONENT DETECTOR")
    defect_info = inspect_model(defect_path, "DEFECT DETECTOR")

    if comp_info is None or defect_info is None:
        print("\n[FATAL] One or both models failed to load. Cannot proceed.")
        return 1

    comp_test = find_test_images("components_unified", max_images=5)
    if not comp_test:
        comp_test = find_test_images("components", max_images=5)
    print(f"\nComponent test images found: {len(comp_test)}")
    for p in comp_test:
        print(f"  - {p}")

    defect_test = find_test_images("defects", max_images=8)
    print(f"\nDefect test images found: {len(defect_test)}")
    for p in defect_test:
        print(f"  - {p}")

    comp_res = run_inference(comp_info, comp_test, "COMPONENT DETECTOR", conf_thresh=0.15, imgsz=640)
    defect_res = run_inference(defect_info, defect_test, "DEFECT DETECTOR", conf_thresh=0.15, imgsz=640)

    with open(os.path.join(DEBUG_DIR, "comp_raw_detections.json"), "w", encoding="utf-8") as f:
        json.dump(comp_res, f, indent=2)
    with open(os.path.join(DEBUG_DIR, "defect_raw_detections.json"), "w", encoding="utf-8") as f:
        json.dump(defect_res, f, indent=2)
    print("\nRaw detection JSONs saved to debug_outputs/.")

    if defect_test:
        sample_defect = defect_test[0]
        run_full_pipeline_test(sample_defect, comp_info, defect_info, conf=0.20)

    if comp_test:
        sample_comp = comp_test[0]
        run_full_pipeline_test(sample_comp, comp_info, defect_info, conf=0.20)

    sample_root = [os.path.join(ROOT, "test.jpg"),
                   os.path.join(ROOT, "t2.jpg"),
                   os.path.join(ROOT, "defect-pcb.jpg")]
    for sp in sample_root:
        if os.path.exists(sp):
            print(f"\n[INFO] Found extra sample at root: {sp}")
            run_full_pipeline_test(sp, comp_info, defect_info, conf=0.18)

    summary = {
        "component_model": {k: v for k, v in comp_info.items() if k != "model_obj"},
        "defect_model": {k: v for k, v in defect_info.items() if k != "model_obj"},
        "component_test_images": len(comp_test),
        "defect_test_images": len(defect_test),
        "component_total_detections": sum(r["num_detections"] for r in comp_res),
        "defect_total_detections": sum(r["num_detections"] for r in defect_res),
    }
    with open(os.path.join(DEBUG_DIR, "DIAGNOSTIC_SUMMARY.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'=' * 80}")
    print("DIAGNOSTIC COMPLETE. Summary:")
    print(json.dumps(summary, indent=2))
    print(f"All outputs saved to: {DEBUG_DIR}")
    print(f"{'=' * 80}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
