"""
Evaluate the DEPLOYED checkpoints (models/component_best.pt, models/defect_best.pt)
against locally held-out splits, and write machine-readable metrics artifacts.

Honesty rules enforced by this script
-------------------------------------
* Every number written to disk is computed here from real predictions on real
  images. Nothing is hardcoded, interpolated or carried over from other reports.
* The threshold sweep runs on the VALIDATION split only. The test split is then
  reported at (a) the ultralytics default 0.25 and (b) the val-calibrated
  threshold. The test split never influences threshold selection.
* Provenance of the deployed checkpoints is NOT this repository's training runs
  (they carry Kaggle train_args). This script records that fact in the output so
  the numbers cannot be mistaken for a locally-trained baseline comparison.

Usage
-----
    python scripts/evaluation/evaluate_deployed_models.py --model component
    python scripts/evaluation/evaluate_deployed_models.py --model defect
    python scripts/evaluation/evaluate_deployed_models.py --model both
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime

import cv2
import numpy as np
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from ai.config import (  # noqa: E402
    CANONICAL_COMPONENT_CLASSES,
    CANONICAL_DEFECT_CLASSES,
    COMPONENT_CLASS_ALIASES,
    DEFECT_ALIGNMENT_MODE,
    DEFECT_MODEL_INDEX_TO_CANONICAL,
    UNDETECTABLE_CURATED_COMPONENT_CLASSES,
)

METRICS_DIR = os.path.join(ROOT, "metrics")

IOU_MATCH_THRESHOLD = 0.5
SWEEP_START, SWEEP_END, SWEEP_STEP = 0.10, 0.70, 0.05
LOW_CONF_FOR_SWEEP = 0.05  # collect detections once at a low conf, then sweep in memory


# ---------------------------------------------------------------------------
# geometry / label IO
# ---------------------------------------------------------------------------
def bbox_iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def load_yolo_gt(label_path, img_w, img_h):
    """Return list of {cls_id, bbox} in absolute pixel xyxy."""
    out = []
    if not os.path.exists(label_path):
        return out
    with open(label_path, "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 5:
                continue
            try:
                cid = int(float(parts[0]))
                cx, cy, bw, bh = (float(x) for x in parts[1:5])
            except ValueError:
                continue
            x1 = (cx - bw / 2.0) * img_w
            y1 = (cy - bh / 2.0) * img_h
            x2 = (cx + bw / 2.0) * img_w
            y2 = (cy + bh / 2.0) * img_h
            out.append({"cls_id": cid, "bbox": [x1, y1, x2, y2]})
    return out


def normalize_name(raw_name, alias_map):
    """raw model/GT label -> canonical class name via the repo alias layer."""
    if raw_name is None:
        return None
    return alias_map.get(str(raw_name).lower(), str(raw_name))


# ---------------------------------------------------------------------------
# matching + AP
# ---------------------------------------------------------------------------
def match_image(gt_items, det_items, iou_thresh):
    """
    Greedy per-class matching of detections to ground truth.

    gt_items / det_items: list of dicts with 'cls' (canonical name) and 'bbox'.
    det_items must be sorted by confidence descending.

    Returns (tp_flags, fp_flags, n_gt_by_class) where tp_flags/fp_flags are
    parallel to det_items.
    """
    gt_by_class = {}
    for g in gt_items:
        gt_by_class.setdefault(g["cls"], []).append({"bbox": g["bbox"], "used": False})

    tp = [False] * len(det_items)
    fp = [False] * len(det_items)
    for di, d in enumerate(det_items):
        candidates = gt_by_class.get(d["cls"], [])
        best_idx, best_iou = -1, 0.0
        for gi, g in enumerate(candidates):
            if g["used"]:
                continue
            iou = bbox_iou(d["bbox"], g["bbox"])
            if iou > best_iou:
                best_iou, best_idx = iou, gi
        if best_idx >= 0 and best_iou >= iou_thresh:
            candidates[best_idx]["used"] = True
            tp[di] = True
        else:
            fp[di] = True
    return tp, fp, {k: len(v) for k, v in gt_by_class.items()}


def average_precision(tp, fp, n_gt):
    """All-point interpolated AP (COCO/VOC-style area under the PR curve)."""
    if n_gt == 0:
        return None
    tp = np.asarray(tp, dtype=float)
    fp = np.asarray(fp, dtype=float)
    cum_tp = np.cumsum(tp)
    cum_fp = np.cumsum(fp)
    recall = cum_tp / n_gt
    precision = cum_tp / np.maximum(cum_tp + cum_fp, 1e-9)
    # make precision monotonically decreasing
    mrec = np.concatenate(([0.0], recall, [1.0]))
    mpre = np.concatenate(([1.0], precision, [0.0]))
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])
    idx = np.where(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[idx + 1] - mrec[idx]) * mpre[idx + 1]))


def compute_prf(tp, fp, n_gt):
    tp_s, fp_s = float(np.sum(tp)), float(np.sum(fp))
    fn = n_gt - tp_s
    prec = tp_s / (tp_s + fp_s) if (tp_s + fp_s) > 0 else 0.0
    rec = tp_s / n_gt if n_gt > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    return {
        "tp": int(tp_s),
        "fp": int(fp_s),
        "fn": int(fn),
        "precision": round(prec, 6),
        "recall": round(rec, 6),
        "f1": round(f1, 6),
    }


# ---------------------------------------------------------------------------
# main evaluation
# ---------------------------------------------------------------------------
def evaluate_split(model, image_dir, label_dir, model_class_names, gt_class_names,
                   model_decode, gt_decode, imgsz, split_label):
    """
    Run the model over one split and return raw per-detection records plus the
    metadata needed to compute any threshold's metrics afterwards.

    `model_class_names` / `gt_class_names` are the checkpoint's and the
    dataset's own id->name tables (kept separate on purpose — decoding the
    dataset's indices with the model's names, e.g. dataset idx 0 "ICs" read as
    model idx 0 "relay", silently mislabels every box and collapses metrics).
    `model_decode`/`gt_decode` are callables (cls_id, raw_name) -> canonical
    name applied ON TOP of those tables:

      * components : both sides name-based via COMPONENT_CLASS_ALIASES (the
        component model's classes match the dataset by NAME, verified
        2026-09-23 on val: 199/218 capacitor detections land on GT capacitors).
      * defects    : model side POSITIONAL by class index (the deployed defect
        checkpoint's name strings are unreliable; alignment verified on val:
        921/923 matched pairs on the diagonal, mean IoU 0.899 — see
        ai/config.py DEFECT_ALIGNMENT_MODE), GT side identity (the dataset's
        own names are already canonical DeepPCB names).
    """
    files = sorted(
        f for f in os.listdir(image_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))
    )
    print(f"[{split_label}] {len(files)} images from {image_dir}")

    per_image = []
    t0 = time.perf_counter()
    for i, fname in enumerate(files, 1):
        img_path = os.path.join(image_dir, fname)
        img = cv2.imread(img_path)
        if img is None:
            print(f"  !! unreadable, skipped: {fname}")
            continue
        h, w = img.shape[:2]

        res = model.predict(
            img, imgsz=imgsz, conf=LOW_CONF_FOR_SWEEP, iou=0.45,
            verbose=False, device="cpu",
        )[0]

        dets = []
        for b in res.boxes:
            cls_id = int(b.cls.item())
            raw = model_class_names.get(cls_id, f"unk_{cls_id}")
            canon = model_decode(cls_id, raw)
            dets.append({
                "cls": canon,
                "raw_cls": raw,
                "raw_cls_id": cls_id,
                "confidence": float(b.conf.item()),
                "bbox": [float(v) for v in b.xyxy[0].tolist()],
            })
        dets.sort(key=lambda d: -d["confidence"])

        stem = os.path.splitext(fname)[0]
        gt_raw = load_yolo_gt(os.path.join(label_dir, stem + ".txt"), w, h)
        gt = []
        for g in gt_raw:
            raw_name = gt_class_names.get(g["cls_id"], f"gtunk_{g['cls_id']}")
            gt.append({
                "cls": gt_decode(g["cls_id"], raw_name),
                "raw_cls": raw_name,
                "raw_cls_id": g["cls_id"],
                "bbox": g["bbox"],
            })

        per_image.append({"file": fname, "detections": dets, "gt": gt})

        if i % 50 == 0 or i == len(files):
            el = time.perf_counter() - t0
            print(f"  {i}/{len(files)}  ({el:.1f}s elapsed, {el / i:.2f}s/img)")

    # An all-empty GT means the label dir was mis-resolved (or the split is
    # unlabeled). Reporting mAP/F1 from that state would be meaningless, so
    # refuse rather than emit a number.
    n_gt_total = sum(len(r["gt"]) for r in per_image)
    n_label_files = sum(
        1 for r in per_image
        if os.path.isfile(os.path.join(label_dir, os.path.splitext(r["file"])[0] + ".txt"))
    )
    if n_gt_total == 0:
        raise SystemExit(
            f"REFUSING to compute metrics for '{split_label}': 0 ground-truth boxes found in "
            f"{label_dir} (label files matched: {n_label_files}/{len(per_image)}). "
            f"This indicates a split/label path problem, not a model result."
        )
    print(f"[{split_label}] GT boxes={n_gt_total} over {len(per_image)} images "
          f"({n_label_files} label files present)")

    return per_image


def metrics_at_threshold(per_image, canonical_classes, threshold, iou_thresh=IOU_MATCH_THRESHOLD):
    """Compute per-class and aggregate metrics at one confidence threshold."""
    all_tp, all_fp = [], []
    gt_counts = {c: 0 for c in canonical_classes}
    det_counts = {c: 0 for c in canonical_classes}

    for rec in per_image:
        dets = [d for d in rec["detections"] if d["confidence"] >= threshold]
        for d in dets:
            det_counts[d["cls"]] = det_counts.get(d["cls"], 0) + 1
        tp, fp, gt_by_class = match_image(rec["gt"], dets, iou_thresh)
        all_tp.extend(tp)
        all_fp.extend(fp)
        for c, n in gt_by_class.items():
            gt_counts[c] = gt_counts.get(c, 0) + n

        # ground truth that was never matched counts as FN -> captured by n_gt
        for d in dets:
            if d["cls"] not in gt_counts:
                gt_counts[d["cls"]] = 0

    per_class = {}
    for c in canonical_classes:
        n_gt = gt_counts.get(c, 0)
        cls_tp, cls_fp = [], []
        for rec in per_image:
            dets = [d for d in rec["detections"] if d["confidence"] >= threshold and d["cls"] == c]
            if not dets:
                continue
            sub_gt = [g for g in rec["gt"] if g["cls"] == c]
            tp, fp, _ = match_image(sub_gt, dets, iou_thresh)
            cls_tp.extend(tp)
            cls_fp.extend(fp)
        if n_gt == 0 and not cls_tp and not cls_fp:
            per_class[c] = {"gt_count": 0, "pred_count": 0, "evaluated": False}
            continue
        m = compute_prf(cls_tp, cls_fp, n_gt)
        m["gt_count"] = n_gt
        m["pred_count"] = det_counts.get(c, 0)
        m["ap50"] = round(average_precision(cls_tp, cls_fp, n_gt), 6) if n_gt > 0 else None
        # A class the model predicts but that has no GT in this split is never
        # allowed into the macro averages: every one of its detections is an FP
        # by construction, which would silently depress the averages.
        m["evaluated"] = n_gt > 0
        m["present_in_gt"] = n_gt > 0
        per_class[c] = m

    scored = [v for v in per_class.values() if v["evaluated"]]
    classes_with_gt = len(scored)

    # micro aggregate (pooled TP/FP/FN over classes that have ground truth)
    tot_tp = sum(v["tp"] for v in scored)
    tot_fp = sum(v["fp"] for v in scored)
    tot_fn = sum(v["fn"] for v in scored)
    micro_p = tot_tp / (tot_tp + tot_fp) if (tot_tp + tot_fp) > 0 else 0.0
    micro_r = tot_tp / (tot_tp + tot_fn) if (tot_tp + tot_fn) > 0 else 0.0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0.0

    aps = [v["ap50"] for v in scored if v["ap50"] is not None]
    predicted_but_absent = [c for c, v in per_class.items()
                            if v.get("gt_count", 0) == 0 and v.get("pred_count", 0) > 0]
    return {
        "confidence_threshold": round(threshold, 3),
        "iou_match_threshold": iou_thresh,
        "per_class": per_class,
        "predicted_classes_absent_from_gt": predicted_but_absent,
        "coverage": {
            "dataset_classes_with_gt_in_this_split": sorted(
                c for c, v in per_class.items() if v.get("gt_count", 0) > 0),
            "dataset_classes_with_zero_gt_in_this_split": sorted(
                c for c, v in per_class.items() if v.get("gt_count", 0) == 0),
        },
        "macro": {
            "classes_with_gt": classes_with_gt,
            "micro_precision": round(micro_p, 6),
            "micro_recall": round(micro_r, 6),
            "micro_f1": round(micro_f1, 6),
            "macro_precision": round(float(np.mean([v["precision"] for v in scored])), 6) if scored else None,
            "macro_recall": round(float(np.mean([v["recall"] for v in scored])), 6) if scored else None,
            "macro_f1": round(float(np.mean([v["f1"] for v in scored])), 6) if scored else None,
            "mAP50": round(float(np.mean(aps)), 6) if aps else None,
        },
    }


def sweep_thresholds(per_image, canonical_classes):
    out = []
    t = SWEEP_START
    while t <= SWEEP_END + 1e-9:
        out.append(metrics_at_threshold(per_image, canonical_classes, round(t, 3)))
        t += SWEEP_STEP
    return out


def map5095(per_image, canonical_classes, threshold):
    """mAP@0.5:0.95 = mean of AP over IoU 0.50..0.95 step 0.05, at a fixed conf."""
    ious = [round(0.5 + 0.05 * i, 2) for i in range(10)]
    mean_aps = []
    for iou in ious:
        m = metrics_at_threshold(per_image, canonical_classes, threshold, iou_thresh=iou)
        aps = [v["ap50"] for v in m["per_class"].values() if v.get("ap50") is not None]
        mean_aps.append(float(np.mean(aps)) if aps else None)
    valid = [v for v in mean_aps if v is not None]
    return {
        "ious": ious,
        "ap_per_iou": [None if v is None else round(v, 6) for v in mean_aps],
        "mAP50_95": round(float(np.mean(valid)), 6) if valid else None,
    }


def run_model(model_key, from_raw=False):
    if model_key == "component":
        model_path = os.path.join(ROOT, "models", "component_best.pt")
        data_yaml = os.path.join(ROOT, "datasets", "components_unified", "data.yaml")
        canonical = CANONICAL_COMPONENT_CLASSES
        alignment = {"mode": "name-based", "decoding": "COMPONENT_CLASS_ALIASES on both sides"}
        model_decode = lambda cid, raw: normalize_name(raw, COMPONENT_CLASS_ALIASES)
        gt_decode = lambda cid, raw: normalize_name(raw, COMPONENT_CLASS_ALIASES)
        imgsz = 1024
        out_json = os.path.join(METRICS_DIR, "component_metrics.json")
        undetectable = list(UNDETECTABLE_CURATED_COMPONENT_CLASSES)
    else:
        model_path = os.path.join(ROOT, "models", "defect_best.pt")
        data_yaml = os.path.join(ROOT, "datasets", "defects", "data.yaml")
        canonical = CANONICAL_DEFECT_CLASSES
        alignment = {
            "mode": DEFECT_ALIGNMENT_MODE,
            "decoding": "model side POSITIONAL by class index (checkpoint name strings "
                        "are unreliable; verified on val 921/923 diagonal pairs, mean IoU "
                        "0.899); GT side identity (dataset names are already canonical)",
            "model_index_to_canonical": dict(DEFECT_MODEL_INDEX_TO_CANONICAL),
        }
        # Index takes precedence; the name table is a fallback only if the index
        # is unknown. GT decode is identity — do NOT route GT names through
        # DEFECT_CLASS_ALIASES, which is keyed on the checkpoint's raw strings.
        model_decode = lambda cid, raw: (
            DEFECT_MODEL_INDEX_TO_CANONICAL.get(int(cid), f"unknown_defect_{cid}"))
        gt_decode = lambda cid, raw: raw
        imgsz = 640
        out_json = os.path.join(METRICS_DIR, "defect_metrics.json")
        undetectable = []

    with open(data_yaml, "r") as f:
        cfg = yaml.safe_load(f)
    root = cfg.get("path", os.path.dirname(data_yaml))
    yaml_names = cfg.get("names", {})
    if isinstance(yaml_names, list):
        yaml_names = {i: n for i, n in enumerate(yaml_names)}
    yaml_names = {int(k): v for k, v in yaml_names.items()}

    split_dirs = {}
    for split in ("val", "test"):
        rel = cfg.get(split)
        if not rel:
            continue
        img_dir = rel if os.path.isabs(rel) else os.path.join(root, rel)
        # data.yaml uses forward slashes; os.sep is "\\" on Windows, so a naive
        # replace(os.sep + "images", ...) silently no-ops and the label dir
        # collapses onto the image dir (every GT becomes empty). Normalize first.
        _norm = img_dir.replace("\\", "/")
        lbl_dir = _norm.replace("/images", "/labels").replace("\\", os.sep)
        if not os.path.isdir(lbl_dir):
            raise SystemExit(f"Label dir not resolved from image dir: {img_dir} -> {lbl_dir}")
        if os.path.isdir(img_dir):
            split_dirs[split] = (img_dir, lbl_dir)
    if "val" not in split_dirs or "test" not in split_dirs:
        raise SystemExit(f"Could not resolve val+test splits from {data_yaml}")

    raw_dir = os.path.join(METRICS_DIR, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    raw_paths = {s: os.path.join(raw_dir, f"{model_key}_{s}_raw.json") for s in ("val", "test")}

    if from_raw:
        print(f"[{model_key}] --from-raw: loading persisted detections/GT, skipping inference")
        val_recs = json.load(open(raw_paths["val"]))
        test_recs = json.load(open(raw_paths["test"]))
        print(f"[{model_key}/val]  {len(val_recs)} images (raw)")
        print(f"[{model_key}/test] {len(test_recs)} images (raw)")
    else:
        from ultralytics import YOLO
        import torch

        print("=" * 72)
        print(f"MODEL EVALUATION — {model_key}")
        print(f"  checkpoint : {model_path}")
        print(f"  data yaml  : {data_yaml}")
        print(f"  alignment  : {alignment['mode']}")
        print(f"  imgsz      : {imgsz}   device: cpu   torch: {torch.__version__}   cuda: {torch.cuda.is_available()}")
        print("=" * 72)

        model = YOLO(model_path)
        model_class_names = {int(k): v for k, v in model.names.items()}
        print(f"  model classes ({len(model_class_names)}): {list(model_class_names.values())}")
        print(f"  GT classes    ({len(yaml_names)}): {list(yaml_names.values())}")

        val_recs = evaluate_split(model, *split_dirs["val"], model_class_names, yaml_names,
                                  model_decode, gt_decode, imgsz, f"{model_key}/val")
        test_recs = evaluate_split(model, *split_dirs["test"], model_class_names, yaml_names,
                                   model_decode, gt_decode, imgsz, f"{model_key}/test")

        # Persist raw detections+GT so any future mapping change can be re-scored
        # deterministically without a CPU re-inference run (~13 min per model).
        for split, recs in (("val", val_recs), ("test", test_recs)):
            with open(raw_paths[split], "w") as f:
                json.dump(recs, f)
            print(f"  raw records written: {raw_paths[split]} "
                  f"({sum(len(r['detections']) for r in recs)} detections, "
                  f"{sum(len(r['gt']) for r in recs)} GT boxes)")

    # The evaluation class space is whatever the union of both decoders can
    # produce, so unmatched predictions stay visible instead of vanishing.
    # GT names are normalized through the GT decoder — the raw yaml names
    # ('ICs', 'capacitors') are not comparable to the canonical ones.
    eval_space = sorted(set(canonical)
                        | {gt_decode(cid, n) for cid, n in yaml_names.items()})
    unknown = [n for n in eval_space if n not in canonical]
    orphan_gt_by_split = {}
    if unknown:
        print(f"  NOTE: GT names outside the canonical space are still scored: {unknown}")

    # GT boxes whose class index is not in the dataset's own data.yaml cannot be
    # scored by anyone. Count them explicitly rather than letting them vanish —
    # an out-of-range index is a dataset defect the reader must know about.
    for split_label, recs in (("val", val_recs), ("test", test_recs)):
        orphan_ids = {}
        for r in recs:
            for g in r["gt"]:
                if str(g["cls"]).startswith("gtunk_"):
                    orphan_ids[g["cls"]] = orphan_ids.get(g["cls"], 0) + 1
        if orphan_ids:
            print(f"  WARNING [{split_label}]: {sum(orphan_ids.values())} GT box(es) carry a class "
                  f"index absent from data.yaml and CANNOT be scored: {orphan_ids}")
        orphan_gt_by_split[split_label] = orphan_ids

    print(f"\n-- threshold sweep on VALIDATION only ({SWEEP_START}..{SWEEP_END} step {SWEEP_STEP}) --")
    val_sweep = sweep_thresholds(val_recs, eval_space)
    best = max(val_sweep, key=lambda m: (m["macro"]["micro_f1"], m["macro"]["micro_precision"]))
    best_t = best["confidence_threshold"]
    print(f"  val-calibrated threshold (best micro-F1) = {best_t}")
    print(f"  val micro-F1 at {best_t} = {best['macro']['micro_f1']}")

    default_metrics = metrics_at_threshold(test_recs, eval_space, 0.25)
    calibrated_metrics = metrics_at_threshold(test_recs, eval_space, best_t)
    default_map = map5095(test_recs, eval_space, 0.25)
    calibrated_map = map5095(test_recs, eval_space, best_t)

    print(f"\n-- TEST metrics (never used for calibration) --")
    print(f"  @conf 0.25 : mAP50={default_map['mAP50_95'] and default_metrics['macro']['mAP50']} "
          f"mAP50-95={default_map['mAP50_95']} microF1={default_metrics['macro']['micro_f1']}")
    print(f"  @conf {best_t} : mAP50={calibrated_metrics['macro']['mAP50']} "
          f"mAP50-95={calibrated_map['mAP50_95']} microF1={calibrated_metrics['macro']['micro_f1']}")

    payload = {
        "generated_at": datetime.now().isoformat(),
        "model_key": model_key,
        "checkpoint_path": os.path.relpath(model_path, ROOT).replace("\\", "/"),
        "checkpoint_md5": _md5(model_path),
        "checkpoint_provenance": _provenance(model_key),
        "dataset_yaml": os.path.relpath(data_yaml, ROOT).replace("\\", "/"),
        "splits_used": {
            "threshold_calibration": "val (only)",
            "reported_metrics": "test (held out from calibration)",
            "val_images": len(val_recs),
            "test_images": len(test_recs),
        },
        "runtime": {
            "device": "cpu",
            "imgsz": imgsz,
            "iou_nms": 0.45,
            "low_conf_floor_for_collection": LOW_CONF_FOR_SWEEP,
        },
        "class_spaces": {
            "model_raw_classes": list(model_class_names.values()) if not from_raw else None,
            "dataset_gt_classes": list(yaml_names.values()),
            "canonical_evaluation_space": eval_space,
            "alignment": alignment,
            "gt_classes_that_no_detection_can_ever_match": undetectable,
            "unscorable_gt_boxes_out_of_range_class_index": orphan_gt_by_split,
        },
        "threshold_sweep_on_val": val_sweep,
        "val_calibrated_threshold": best_t,
        "test_at_default_0.25": {
            "metrics": default_metrics,
            "map_50_95": default_map,
        },
        "test_at_val_calibrated_threshold": {
            "metrics": calibrated_metrics,
            "map_50_95": calibrated_map,
        },
    }

    os.makedirs(METRICS_DIR, exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nWritten: {out_json}")

    sweep_csv = os.path.join(METRICS_DIR, f"threshold_sweep_{model_key}.csv")
    with open(sweep_csv, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["split", "confidence_threshold", "micro_precision", "micro_recall",
                    "micro_f1", "macro_precision", "macro_recall", "macro_f1", "mAP50"])
        for m in val_sweep:
            w.writerow(["val", m["confidence_threshold"], m["macro"]["micro_precision"],
                        m["macro"]["micro_recall"], m["macro"]["micro_f1"],
                        m["macro"]["macro_precision"], m["macro"]["macro_recall"],
                        m["macro"]["macro_f1"], m["macro"]["mAP50"]])
        for m in (default_metrics, calibrated_metrics):
            w.writerow(["test", m["confidence_threshold"], m["macro"]["micro_precision"],
                        m["macro"]["micro_recall"], m["macro"]["micro_f1"],
                        m["macro"]["macro_precision"], m["macro"]["macro_recall"],
                        m["macro"]["macro_f1"], m["macro"]["mAP50"]])
    print(f"Written: {sweep_csv}")

    per_class_csv = os.path.join(METRICS_DIR, f"per_class_{model_key}.csv")
    with open(per_class_csv, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["eval_conf", "class", "gt_count", "pred_count", "tp", "fp", "fn",
                    "precision", "recall", "f1", "ap50"])
        for label, m in (("0.25", default_metrics), (str(best_t), calibrated_metrics)):
            for c, v in m["per_class"].items():
                if not v.get("evaluated"):
                    w.writerow([label, c, v.get("gt_count", 0), v.get("pred_count", 0),
                                "", "", "", "", "", "", ""])
                    continue
                w.writerow([label, c, v["gt_count"], v["pred_count"], v["tp"], v["fp"],
                            v["fn"], v["precision"], v["recall"], v["f1"], v["ap50"]])
    print(f"Written: {per_class_csv}")
    return payload


def _md5(path):
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _provenance(model_key):
    """Record where the checkpoint actually came from (read from the .pt)."""
    import torch
    path = os.path.join(ROOT, "models",
                        "component_best.pt" if model_key == "component" else "defect_best.pt")
    try:
        ck = torch.load(path, map_location="cpu", weights_only=False)
    except Exception as e:  # pragma: no cover
        return {"readable": False, "error": str(e)}
    ta = ck.get("train_args") or {}
    return {
        "readable": True,
        "trained_in_this_repository": False,
        "evidence": "checkpoint train_args point at a Kaggle working directory; "
                    "no in-repo training run produced this file (see FINAL_IMPLEMENTATION_AUDIT.md)",
        "train_args_data": ta.get("data"),
        "train_args_model": ta.get("model"),
        "train_args_epochs": ta.get("epochs"),
        "train_args_imgsz": ta.get("imgsz"),
        "train_args_device": ta.get("device"),
        "train_args_name": ta.get("name"),
        "ckpt_date": ck.get("date"),
        "ckpt_ultralytics_version": ck.get("version"),
        "self_reported_train_metrics": ck.get("train_metrics"),
        "self_reported_metrics_note": "reported by the trainer on ITS OWN split; "
                                      "independently UNVERIFIED by this repository",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["component", "defect", "both"], default="both")
    ap.add_argument("--from-raw", action="store_true",
                    help="re-score from persisted raw detections/GT (skip inference)")
    args = ap.parse_args()

    keys = ["component", "defect"] if args.model == "both" else [args.model]
    for k in keys:
        run_model(k, from_raw=args.from_raw)
        print()


if __name__ == "__main__":
    main()
