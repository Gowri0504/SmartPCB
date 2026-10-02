"""
Diagnose the class-index alignment between a deployed checkpoint and the local
dataset it is scored against.

Why this exists
---------------
The defect evaluation scored mAP50 ~= 0.0001 on datasets/defects/test while the
checkpoint self-reports mAP50 0.9079. A single-image check showed the model's
boxes coincide with ground-truth boxes almost exactly, but under *different
class indices*. That means the checkpoint's class-name strings and this
dataset's data.yaml names disagree about what each index means.

This script measures the disagreement directly and without trusting either name
list: it matches detections to ground truth purely geometrically
(class-agnostic, greedy by confidence, IoU >= 0.5) and tallies the
(model_class_index, gt_class_index) pairs. If the checkpoint and the dataset
share an index order, the tally concentrates on the diagonal.

Honesty note: the alignment decision is taken on the VALIDATION split. The test
split is printed as confirmation only and is never used to choose the mapping.

Usage
-----
    python scripts/debug/diagnose_defect_class_alignment.py --model defect    --split val
    python scripts/debug/diagnose_defect_class_alignment.py --model component --split val
"""

import argparse
import collections
import json
import os
import sys

import cv2
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

IOU_MATCH = 0.5

MODELS = {
    "component": {
        "checkpoint": os.path.join("models", "component_best.pt"),
        "yaml": os.path.join("datasets", "components_unified", "data.yaml"),
        "imgsz": 1024,
    },
    "defect": {
        "checkpoint": os.path.join("models", "defect_best.pt"),
        "yaml": os.path.join("datasets", "defects", "data.yaml"),
        "imgsz": 640,
    },
}


def bbox_iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    union = ((ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter)
    return inter / union if union > 0 else 0.0


def load_gt(label_path, w, h):
    out = []
    if not os.path.isfile(label_path):
        return out
    with open(label_path, "r") as f:
        for line in f:
            p = line.split()
            if len(p) < 5:
                continue
            cid = int(float(p[0]))
            cx, cy, bw, bh = (float(x) for x in p[1:5])
            out.append({
                "cls_id": cid,
                "bbox": [(cx - bw / 2) * w, (cy - bh / 2) * h,
                         (cx + bw / 2) * w, (cy + bh / 2) * h],
            })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="defect", choices=sorted(MODELS))
    ap.add_argument("--split", default="val", choices=["train", "val", "test"])
    ap.add_argument("--max-images", type=int, default=0, help="0 = all")
    ap.add_argument("--imgsz", type=int, default=0, help="0 = model default")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    spec = MODELS[args.model]
    imgsz = args.imgsz or spec["imgsz"]
    data_yaml = os.path.join(ROOT, spec["yaml"])
    with open(data_yaml, "r") as f:
        cfg = yaml.safe_load(f)
    root = cfg.get("path", os.path.dirname(data_yaml))
    names = cfg["names"]
    if isinstance(names, list):
        names = {i: n for i, n in enumerate(names)}
    gt_names = {int(k): v for k, v in names.items()}

    rel = cfg[args.split]
    img_dir = rel if os.path.isabs(rel) else os.path.join(root, rel)
    lbl_dir = img_dir.replace("\\", "/").replace("/images", "/labels").replace("/", os.sep)

    from ultralytics import YOLO
    model = YOLO(os.path.join(ROOT, spec["checkpoint"]))
    m_names = {int(k): v for k, v in model.names.items()}

    print("=" * 74)
    print(f"CLASS-ALIGNMENT DIAGNOSTIC — model={args.model} split={args.split} imgsz={imgsz}")
    print(f"  checkpoint    : {spec['checkpoint']}")
    print(f"  model classes : {[m_names[i] for i in sorted(m_names)]}")
    print(f"  yaml  classes : {[gt_names[i] for i in sorted(gt_names)]}")
    print("=" * 74)

    files = sorted(f for f in os.listdir(img_dir)
                   if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")))
    if args.max_images:
        files = files[:args.max_images]

    pair_counts = collections.Counter()
    row_totals = collections.Counter()
    n_gt_total = n_dets_total = n_matched = 0
    unmatched_by_gt = collections.Counter()
    unmatched_by_model = collections.Counter()
    ious = []

    for i, fname in enumerate(files, 1):
        img = cv2.imread(os.path.join(img_dir, fname))
        if img is None:
            continue
        h, w = img.shape[:2]
        res = model.predict(img, imgsz=imgsz, conf=args.conf, iou=0.45,
                            verbose=False, device="cpu")[0]

        dets = sorted(
            [{"cls_id": int(b.cls.item()),
              "conf": float(b.conf.item()),
              "bbox": [float(v) for v in b.xyxy[0].tolist()]} for b in res.boxes],
            key=lambda d: -d["conf"],
        )
        gts = load_gt(os.path.join(lbl_dir, os.path.splitext(fname)[0] + ".txt"), w, h)
        n_gt_total += len(gts)
        n_dets_total += len(dets)

        used = [False] * len(gts)
        for d in dets:
            best_j, best_iou = -1, 0.0
            for j, g in enumerate(gts):
                if used[j]:
                    continue
                v = bbox_iou(d["bbox"], g["bbox"])
                if v > best_iou:
                    best_iou, best_j = v, j
            if best_j >= 0 and best_iou >= IOU_MATCH:
                used[best_j] = True
                pair_counts[(d["cls_id"], gts[best_j]["cls_id"])] += 1
                row_totals[d["cls_id"]] += 1
                ious.append(best_iou)
                n_matched += 1
            else:
                unmatched_by_model[d["cls_id"]] += 1
        for j, g in enumerate(gts):
            if not used[j]:
                unmatched_by_gt[g["cls_id"]] += 1

        if i % 25 == 0 or i == len(files):
            print(f"  {i}/{len(files)} images...")

    print(f"\nimages            : {len(files)}")
    print(f"GT boxes          : {n_gt_total}")
    print(f"detections @>={args.conf} : {n_dets_total}")
    if n_matched:
        print(f"IoU>={IOU_MATCH} matches  : {n_matched}  (mean IoU {sum(ious) / len(ious):.3f})")
    else:
        print("IoU>=0.5 matches  : 0")

    cols = sorted(gt_names)
    print("\n-- contingency matrix rows=model idx, cols=gt idx --")
    print("  model \\ gt   |" + "".join(f"{gt_names[c][:11]:>13}" for c in cols))
    for r in sorted(m_names):
        row = f"  {m_names[r][:12]:>12} |"
        for c in cols:
            row += f"{pair_counts.get((r, c), 0):>13}"
        print(row + f"   <- idx {r}")

    diag = sum(v for (r, c), v in pair_counts.items() if r == c)
    print("\n-- per-model-index best correspondence --")
    if n_matched:
        print(f"  diagonal pairs (model_idx == gt_idx): {diag}/{n_matched} "
              f"({100.0 * diag / n_matched:.1f}%)")
    realised = {}
    for r in sorted(m_names):
        if not row_totals[r]:
            continue
        c, n = max(((c, pair_counts.get((r, c), 0)) for c in cols), key=lambda t: t[1])
        realised[r] = {"gt_idx": c, "gt_name": gt_names[c], "n": n,
                       "model_total": row_totals[r]}
        print(f"  model idx {r:2d} '{m_names[r]:<16}' (n={row_totals[r]:4d}) "
              f"-> most often GT idx {c} '{gt_names[c]}' (n={n})")

    print("\n-- unmatched --")
    print(f"  GT never matched by any detection : "
          f"{ {gt_names[k]: v for k, v in sorted(unmatched_by_gt.items())} }")
    print(f"  detections matching no GT         : "
          f"{ {m_names[k]: v for k, v in sorted(unmatched_by_model.items())} }")

    if args.json_out:
        payload = {
            "model": args.model,
            "split": args.split,
            "imgsz": imgsz,
            "conf": args.conf,
            "iou_match": IOU_MATCH,
            "images": len(files),
            "gt_boxes": n_gt_total,
            "detections": n_dets_total,
            "matched": n_matched,
            "mean_matched_iou": round(sum(ious) / len(ious), 4) if ious else None,
            "model_raw_classes": [m_names[i] for i in sorted(m_names)],
            "dataset_classes": [gt_names[i] for i in sorted(gt_names)],
            "contingency": {
                f"model_idx_{r}_gt_idx_{c}": v for (r, c), v in sorted(pair_counts.items())
            },
            "diagonal_pairs": diag,
            "per_model_index_best_gt": realised,
            "unmatched_gt": {gt_names[k]: v for k, v in sorted(unmatched_by_gt.items())},
            "unmatched_detections": {m_names[k]: v for k, v in sorted(unmatched_by_model.items())},
        }
        os.makedirs(os.path.dirname(args.json_out), exist_ok=True)
        with open(args.json_out, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
