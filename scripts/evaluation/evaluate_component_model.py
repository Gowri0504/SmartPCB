import os
import sys
import json
import time
import cv2
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from ultralytics import YOLO

MODELS_DIR = os.path.join(ROOT, "models")
METRICS_DIR = os.path.join(ROOT, "metrics")
os.makedirs(METRICS_DIR, exist_ok=True)

CANONICAL_COMPONENT_MAP = {
    "ic": "ICs", "ics": "ICs", "IC": "ICs", "ICs": "ICs",
    "capacitor": "capacitors", "capacitors": "capacitors",
    "resistor": "resistors", "resistors": "resistors",
    "diode": "diodes", "diodes": "diodes",
    "transistor": "transistors", "transistors": "transistors",
    "inductor": "inductors", "inductors": "inductors",
}

CANONICAL_DEFECT_MAP = {
    "open": "open", "open_circuit": "open",
    "short": "short",
    "mousebite": "mousebite", "mouse_bite": "mousebite",
    "spur": "spur",
    "copper": "copper", "spurious_copper": "copper",
    "pin-hole": "pin-hole", "missing_hole": "pin-hole", "pin_hole": "pin-hole",
}


def bbox_iou(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter = inter_w * inter_h
    a_area = max(0.0, (ax2 - ax1) * (ay2 - ay1))
    b_area = max(0.0, (bx2 - bx1) * (by2 - by1))
    union = a_area + b_area - inter + 1e-9
    return inter / union


def load_yolo_labels(label_path, img_w, img_h):
    gts = []
    if not os.path.exists(label_path):
        return gts
    with open(label_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            cls_id = int(parts[0])
            cx, cy, w, h = [float(x) for x in parts[1:5]]
            x1 = (cx - w / 2) * img_w
            y1 = (cy - h / 2) * img_h
            x2 = (cx + w / 2) * img_w
            y2 = (cy + h / 2) * img_h
            gts.append({"class_id": cls_id, "bbox": [x1, y1, x2, y2]})
    return gts


def map_class_name_to_canonical(name, cmap):
    return cmap.get(name.lower(), name)


def evaluate_dataset(model_path, data_yaml_path, dataset_label,
                     class_map=None, conf_thresholds=None, imgsz=640, split="test"):
    if conf_thresholds is None:
        conf_thresholds = [0.10, 0.20, 0.30, 0.40, 0.50]

    print(f"\n{'='*90}")
    print(f"EVALUATING {dataset_label}")
    print(f"Model: {model_path}")
    print(f"Data YAML: {data_yaml_path}")
    print(f"Split: {split} | imgsz: {imgsz}")
    print(f"{'='*90}")

    import yaml
    with open(data_yaml_path, 'r') as f:
        data_cfg = yaml.safe_load(f)

    data_root = data_cfg.get('path', os.path.dirname(data_yaml_path))
    split_dir = data_cfg.get(split, f"{split}/images")
    if not os.path.isabs(split_dir):
        split_dir = os.path.join(data_root, split_dir)

    labels_dir = os.path.join(os.path.dirname(split_dir), "labels")
    yaml_class_names = data_cfg.get('names', {})
    if isinstance(yaml_class_names, list):
        yaml_class_names = {i: n for i, n in enumerate(yaml_class_names)}

    print(f"Dataset root: {data_root}")
    print(f"Images dir: {split_dir}  (exists={os.path.isdir(split_dir)})")
    print(f"Labels dir: {labels_dir}  (exists={os.path.isdir(labels_dir)})")
    print(f"YAML classes: {yaml_class_names}")

    img_files = []
    if os.path.isdir(split_dir):
        for f in sorted(os.listdir(split_dir)):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                img_files.append(os.path.join(split_dir, f))
    print(f"Found {len(img_files)} images in split '{split}'")

    if not img_files:
        print("[WARN] No images found. Skipping.")
        return None

    model = YOLO(model_path)
    model_class_names = {k: (class_map.get(v.lower(), v) if class_map else v)
                         for k, v in model.names.items()}
    print(f"Model classes: {model.names}")
    print(f"Mapped classes: {model_class_names}")

    threshold_results = {}
    for conf in conf_thresholds:
        all_tp, all_fp, all_fn = 0, 0, 0
        per_class_stats = {}
        image_records = []

        for img_path in img_files:
            img_name = os.path.basename(img_path)
            img_bgr = cv2.imread(img_path)
            if img_bgr is None:
                continue
            h, w = img_bgr.shape[:2]

            lbl_path = os.path.join(labels_dir, os.path.splitext(img_name)[0] + ".txt")
            gts = load_yolo_labels(lbl_path, w, h)
            for g in gts:
                gt_name = yaml_class_names.get(g['class_id'], f"unk_{g['class_id']}")
                gt_canon = (class_map.get(gt_name.lower(), gt_name) if class_map else gt_name)
                g['class'] = gt_canon

            t0 = time.perf_counter()
            preds = model.predict(source=img_bgr, conf=conf, imgsz=imgsz,
                                  device="cpu", verbose=False)
            t1 = time.perf_counter()
            inf_ms = (t1 - t0) * 1000.0

            detections = []
            for r in preds:
                for i in range(len(r.boxes)):
                    xyxy = r.boxes.xyxy[i].cpu().numpy().tolist()
                    pconf = float(r.boxes.conf[i].cpu().numpy())
                    pcid = int(r.boxes.cls[i].cpu().numpy())
                    pcname = r.names.get(pcid, f"cls_{pcid}")
                    pcanon = (class_map.get(pcname.lower(), pcname) if class_map else pcname)
                    detections.append({
                        "class": pcanon, "class_id": pcid,
                        "confidence": pconf, "bbox": xyxy,
                        "matched": False
                    })

            gt_remaining = list(gts)
            img_tp = img_fp = img_fn = 0
            for d in sorted(detections, key=lambda x: -x['confidence']):
                best_iou = 0.0
                best_gt_idx = -1
                for gi, g in enumerate(gt_remaining):
                    if g['class'] != d['class']:
                        continue
                    iou = bbox_iou(d['bbox'], g['bbox'])
                    if iou > best_iou:
                        best_iou = iou
                        best_gt_idx = gi
                if best_iou >= 0.5 and best_gt_idx >= 0:
                    d['matched'] = True
                    gt_remaining.pop(best_gt_idx)
                    img_tp += 1
                else:
                    img_fp += 1
            img_fn = len(gt_remaining)

            all_tp += img_tp
            all_fp += img_fp
            all_fn += img_fn

            def bucket(d, k):
                stats = per_class_stats.setdefault(k, {"TP": 0, "FP": 0, "FN": 0, "GT": 0})
                stats[d] += 1

            for d in detections:
                cls = d['class']
                per_class_stats.setdefault(cls, {"TP": 0, "FP": 0, "FN": 0, "GT": 0})
                if d['matched']:
                    per_class_stats[cls]["TP"] += 1
                else:
                    per_class_stats[cls]["FP"] += 1
            for g in gts:
                cls = g['class']
                per_class_stats.setdefault(cls, {"TP": 0, "FP": 0, "FN": 0, "GT": 0})
                per_class_stats[cls]["GT"] += 1
                if any(g2['class'] == cls for g2 in gt_remaining):
                    # approximate; will fix below
                    pass

            # Rebuild accurate per-class FN from gt_remaining
            for g in gt_remaining:
                cls = g['class']
                per_class_stats.setdefault(cls, {"TP": 0, "FP": 0, "FN": 0, "GT": 0})
                per_class_stats[cls]["FN"] += 1

            image_records.append({
                "image": img_name,
                "width": w, "height": h,
                "tp": img_tp, "fp": img_fp, "fn": img_fn,
                "gt_count": len(gts), "pred_count": len(detections),
                "inference_ms": round(inf_ms, 2)
            })

        prec = all_tp / max(1e-9, (all_tp + all_fp))
        rec = all_tp / max(1e-9, (all_tp + all_fn))
        f1 = 2 * (prec * rec) / max(1e-9, (prec + rec))
        avg_inf = np.mean([r["inference_ms"] for r in image_records]) if image_records else 0

        for cls, s in per_class_stats.items():
            cp = s["TP"] / max(1e-9, (s["TP"] + s["FP"]))
            cr = s["TP"] / max(1e-9, (s["TP"] + s["FN"]))
            cf1 = 2 * (cp * cr) / max(1e-9, (cp + cr))
            s["Precision"] = round(cp, 4)
            s["Recall"] = round(cr, 4)
            s["F1"] = round(cf1, 4)

        result = {
            "dataset": dataset_label,
            "conf_threshold": conf,
            "imgsz": imgsz,
            "images": len(image_records),
            "overall": {
                "TP": all_tp, "FP": all_fp, "FN": all_fn,
                "Precision": round(prec, 4), "Recall": round(rec, 4),
                "F1": round(f1, 4),
                "avg_inference_ms": round(avg_inf, 2)
            },
            "per_class": per_class_stats,
            "images": image_records,
        }
        threshold_results[conf] = result
        print(f"\n--- conf={conf} ---")
        print(f"  TP={all_tp}  FP={all_fp}  FN={all_fn}  "
              f"Prec={prec*100:.2f}%  Rec={rec*100:.2f}%  F1={f1*100:.2f}%  "
              f"AvgInf={avg_inf:.2f}ms")
        for cls, s in sorted(per_class_stats.items()):
            print(f"    {cls:<15} GT={s['GT']:<4} TP={s['TP']:<4} "
                  f"FP={s['FP']:<4} FN={s['FN']:<4} "
                  f"P={s['Precision']*100:>6.2f}%  R={s['Recall']*100:>6.2f}%  "
                  f"F1={s['F1']*100:>6.2f}%")

    return threshold_results


def plot_confusion_matrix(per_class, title, out_path):
    classes = sorted(per_class.keys())
    if not classes:
        return
    n = len(classes)
    mat = np.zeros((n, n), dtype=np.float32)
    for i, c in enumerate(classes):
        s = per_class[c]
        mat[i, i] = s.get("TP", 0)
    fig, ax = plt.subplots(figsize=(max(6, n * 0.9), max(5, n * 0.8)))
    im = ax.imshow(mat, cmap="Blues")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(classes, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(classes, fontsize=8)
    for i in range(n):
        for j in range(n):
            ax.text(j, i, int(mat[i, j]), ha="center", va="center",
                    color="white" if mat[i, j] > mat.max() / 2 else "black",
                    fontsize=8)
    ax.set_title(title)
    plt.colorbar(im)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_threshold_sweep(threshold_results, title, out_path):
    thrs = sorted(threshold_results.keys())
    precs = [threshold_results[t]["overall"]["Precision"] for t in thrs]
    recs = [threshold_results[t]["overall"]["Recall"] for t in thrs]
    f1s = [threshold_results[t]["overall"]["F1"] for t in thrs]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(thrs, precs, marker="o", label="Precision")
    ax.plot(thrs, recs, marker="s", label="Recall")
    ax.plot(thrs, f1s, marker="^", label="F1")
    ax.set_xlabel("Confidence Threshold")
    ax.set_ylabel("Score")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)


def build_per_class_csv(threshold_results, out_path):
    rows = []
    for conf, res in threshold_results.items():
        for cls, s in res["per_class"].items():
            rows.append({
                "conf_threshold": conf, "class": cls,
                "GT": s.get("GT", 0), "TP": s.get("TP", 0),
                "FP": s.get("FP", 0), "FN": s.get("FN", 0),
                "Precision": s.get("Precision", 0), "Recall": s.get("Recall", 0),
                "F1": s.get("F1", 0)
            })
    pd.DataFrame(rows).to_csv(out_path, index=False)


def main_component():
    comp_model = os.path.join(MODELS_DIR, "component_best.pt")
    comp_yaml = os.path.join(ROOT, "datasets", "components_unified", "data.yaml")
    out = evaluate_dataset(comp_model, comp_yaml, "PCB_COMPONENTS",
                           class_map=CANONICAL_COMPONENT_MAP,
                           conf_thresholds=[0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70],
                           split="test")
    if out is None:
        return
    json_path = os.path.join(METRICS_DIR, "component_metrics.json")
    with open(json_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    best_conf = max(out.keys(), key=lambda t: out[t]["overall"]["F1"])
    print(f"\nComponent best operating threshold (F1): {best_conf}")
    plot_confusion_matrix(out[best_conf]["per_class"],
                          "Component Detection Confusion Matrix",
                          os.path.join(METRICS_DIR, "confusion_matrix_component.png"))
    plot_threshold_sweep(out, "Component Precision / Recall / F1 vs Confidence",
                         os.path.join(METRICS_DIR, "precision_recall_component.png"))
    build_per_class_csv(out, os.path.join(METRICS_DIR, "per_class_metrics_component.csv"))
    print(f"Component metrics saved to {METRICS_DIR}")
    return out


def main_defect():
    defect_model = os.path.join(MODELS_DIR, "defect_best.pt")
    defect_yaml = os.path.join(ROOT, "datasets", "defects", "data.yaml")
    out = evaluate_dataset(defect_model, defect_yaml, "PCB_DEFECTS",
                           class_map=CANONICAL_DEFECT_MAP,
                           conf_thresholds=[0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70],
                           split="test")
    if out is None:
        return
    json_path = os.path.join(METRICS_DIR, "defect_metrics.json")
    with open(json_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    best_conf = max(out.keys(), key=lambda t: out[t]["overall"]["Recall"])
    print(f"\nDefect best recall threshold: {best_conf}")
    plot_confusion_matrix(out[best_conf]["per_class"],
                          "Defect Detection Confusion Matrix",
                          os.path.join(METRICS_DIR, "confusion_matrix_defect.png"))
    plot_threshold_sweep(out, "Defect Precision / Recall / F1 vs Confidence",
                         os.path.join(METRICS_DIR, "precision_recall_defect.png"))
    build_per_class_csv(out, os.path.join(METRICS_DIR, "per_class_metrics_defect.csv"))
    print(f"Defect metrics saved to {METRICS_DIR}")
    return out


def main_full_pipeline():
    """Run the full inspection engine on 20+ real images and generate REALTIME_VERIFICATION_REPORT data."""
    from ai.inference.engine import SmartPCBInspectionEngine

    engine = SmartPCBInspectionEngine()

    defect_test = os.path.join(ROOT, "datasets", "defects", "test", "images")
    comp_test = os.path.join(ROOT, "datasets", "components_unified", "test", "images")

    test_images = []
    for d in [defect_test, comp_test]:
        if os.path.isdir(d):
            for f in sorted(os.listdir(d))[:10]:
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    test_images.append(os.path.join(d, f))

    for f in ["test.jpg", "t2.jpg", "defect-pcb.jpg"]:
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            test_images.append(p)

    print(f"\nRunning full pipeline on {len(test_images)} images...")
    records = []
    for img_path in test_images:
        try:
            img_bgr = cv2.imread(img_path)
            if img_bgr is None:
                continue
            t0 = time.perf_counter()
            result = engine.inspect(img_bgr, conf_threshold=0.20, generate_xai=True)
            t1 = time.perf_counter()
            total_ms = (t1 - t0) * 1000.0
            qs = result.get("quality_score", {})
            overall = qs.get("overall_score")  # None = deliberately withheld (REVIEW_REQUIRED)
            records.append({
                "image": os.path.basename(img_path),
                "width": result["image_dimensions"]["width"],
                "height": result["image_dimensions"]["height"],
                "components_detected": len(result["components"]),
                "defects_detected": len(result["defects"]),
                "avg_component_conf": round(np.mean([c["confidence"] for c in result["components"]]), 4) if result["components"] else 0.0,
                "avg_defect_conf": round(np.mean([d["confidence"] for d in result["defects"]]), 4) if result["defects"] else 0.0,
                "quality_score": overall,
                "status": qs.get("status", "UNKNOWN"),
                "pipeline_latency_ms": round(total_ms, 2),
            })
            print(f"  {records[-1]['image']:<40} comps={records[-1]['components_detected']:<3} "
                  f"defects={records[-1]['defects_detected']:<3} score={str(records[-1]['quality_score']):<6} "
                  f"status={records[-1]['status']:<16} time={records[-1]['pipeline_latency_ms']:.1f}ms")
        except Exception as e:
            print(f"  [ERROR] {os.path.basename(img_path)}: {e}")

    df = pd.DataFrame(records)
    csv_path = os.path.join(METRICS_DIR, "pipeline_20_images_report.csv")
    df.to_csv(csv_path, index=False)
    json_path = os.path.join(METRICS_DIR, "full_pipeline_metrics.json")
    with open(json_path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"\nFull pipeline report saved: {csv_path}")
    return records


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "all":
        main_component()
        main_defect()
        main_full_pipeline()
    elif sys.argv[1] == "component":
        main_component()
    elif sys.argv[1] == "defect":
        main_defect()
    elif sys.argv[1] == "pipeline":
        main_full_pipeline()
