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

# 4D sweep defaults (only for defect model when explicitly requested):
DEFAULT_CONF_RANGE = (0.05, 0.95, 0.025)  # start, end, step
DEFAULT_MATCH_IOUS = [0.40, 0.45, 0.50, 0.55, 0.60]
DEFAULT_NMS_IOUS = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]  # baked into predictions; used only for fresh-inference variant
PER_CLASS_WEAK_CANDIDATES = {"pin-hole", "short", "spur"}  # try ±0.05 conf offsets from global best


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


def metrics_at_threshold(per_image, canonical_classes, threshold, iou_thresh=IOU_MATCH_THRESHOLD,
                         per_class_conf_overrides: dict | None = None):
    """Compute per-class and aggregate metrics at one confidence threshold.

    per_class_conf_overrides: dict[cls_name] -> stricter conf to apply for that
        class only; classes not listed fall back to global `threshold`.
    """
    per_class_conf_overrides = per_class_conf_overrides or {}
    all_tp, all_fp = [], []
    gt_counts = {c: 0 for c in canonical_classes}
    det_counts = {c: 0 for c in canonical_classes}

    for rec in per_image:
        # Apply global OR class-specific conf filter
        def keep(d, t=threshold, overrides=per_class_conf_overrides):
            cls = d["cls"]
            t_eff = float(overrides.get(cls, t))
            return float(d["confidence"]) >= t_eff
        dets = [d for d in rec["detections"] if keep(d)]
        for d in dets:
            det_counts[d["cls"]] = det_counts.get(d["cls"], 0) + 1
        tp, fp, gt_by_class = match_image(rec["gt"], dets, iou_thresh)
        all_tp.extend(tp)
        all_fp.extend(fp)
        for c, n in gt_by_class.items():
            gt_counts[c] = gt_counts.get(c, 0) + n

        for d in dets:
            if d["cls"] not in gt_counts:
                gt_counts[d["cls"]] = 0

    per_class = {}
    for c in canonical_classes:
        n_gt = gt_counts.get(c, 0)
        cls_tp, cls_fp = [], []
        for rec in per_image:
            dets = [d for d in rec["detections"]
                    if (float(d["confidence"]) >=
                        float(per_class_conf_overrides.get(c, threshold)))
                    and d["cls"] == c]
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
        m["evaluated"] = n_gt > 0
        m["present_in_gt"] = n_gt > 0
        per_class[c] = m

    scored = [v for v in per_class.values() if v["evaluated"]]
    classes_with_gt = len(scored)

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
        "confidence_threshold": round(float(threshold), 4),
        "iou_match_threshold": iou_thresh,
        "per_class_conf_overrides": dict(per_class_conf_overrides) if per_class_conf_overrides else None,
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


def map5095(per_image, canonical_classes, threshold, per_class_conf_overrides=None):
    """mAP@0.5:0.95 = mean of AP over IoU 0.50..0.95 step 0.05, at a fixed conf."""
    ious = [round(0.5 + 0.05 * i, 2) for i in range(10)]
    mean_aps = []
    for iou in ious:
        m = metrics_at_threshold(per_image, canonical_classes, threshold,
                                 iou_thresh=iou, per_class_conf_overrides=per_class_conf_overrides)
        aps = [v["ap50"] for v in m["per_class"].values() if v.get("ap50") is not None]
        mean_aps.append(float(np.mean(aps)) if aps else None)
    valid = [v for v in mean_aps if v is not None]
    return {
        "ious": ious,
        "ap_per_iou": [None if v is None else round(v, 6) for v in mean_aps],
        "mAP50_95": round(float(np.mean(valid)), 6) if valid else None,
    }


# ---------------------------------------------------------------------------
# 4D grid search (conf × match_IoU × optional per-class overrides) + TTA/ensemble
# ---------------------------------------------------------------------------

def _conf_list_from_range_str(spec):
    if spec is None:
        start, end, step = DEFAULT_CONF_RANGE
        t = start
        out = []
        while t <= end + 1e-9:
            out.append(round(t, 6))
            t += step
        return out
    parts = [p.strip() for p in spec.split(":")]
    if len(parts) == 1:
        return [float(parts[0])]
    if len(parts) == 2:
        start, end = float(parts[0]), float(parts[1])
        step = 0.025
    else:
        start, end, step = float(parts[0]), float(parts[1]), float(parts[2])
    out = []
    t = start
    while t <= end + 1e-9:
        out.append(round(t, 6))
        t += step
    return out


def _parse_float_list(spec, default):
    if spec is None:
        return list(default)
    return [float(x.strip()) for x in spec.split(",") if x.strip()]


def sweep_4d(per_image, canonical_classes, conf_list, match_iou_list,
             search_per_class_offsets: bool = True,
             per_class_weak_candidates=None):
    """
    Grid search over (conf × match_IoU) tuples, lex-scored on
    (micro_F1, mAP50, micro_precision, micro_recall).

    Optionally tries ±0.05 conf overrides on weak classes against the best
    global tuple; returns the best overall with any override map.
    """
    per_class_weak_candidates = per_class_weak_candidates or PER_CLASS_WEAK_CANDIDATES
    best = None
    best_key = None
    all_rows = []

    for conf in conf_list:
        for iou in match_iou_list:
            m = metrics_at_threshold(per_image, canonical_classes, conf, iou_thresh=iou)
            score_tuple = (
                m["macro"]["micro_f1"] or 0.0,
                m["macro"]["mAP50"] or 0.0,
                m["macro"]["micro_precision"] or 0.0,
                m["macro"]["micro_recall"] or 0.0,
            )
            row = {
                "conf": float(conf),
                "match_iou": float(iou),
                "overrides": None,
                "micro_f1": score_tuple[0],
                "mAP50": score_tuple[1],
                "micro_precision": score_tuple[2],
                "micro_recall": score_tuple[3],
            }
            all_rows.append(row)
            if best is None or score_tuple > best_key:
                best = row
                best_key = score_tuple

    if search_per_class_offsets and best is not None:
        base_conf = best["conf"]
        base_iou = best["match_iou"]
        # Try offsets on each candidate weak class independently, then combinations
        offsets = [-0.05, 0.0, 0.05]
        candidates_sorted = sorted(per_class_weak_candidates)
        # Single-offset sweep (cheap, avoids combinatorial explosion)
        for cls in candidates_sorted:
            for off in offsets:
                if abs(off) < 1e-9:
                    continue
                eff = max(0.0, min(1.0, base_conf + off))
                ov = {cls: eff}
                m = metrics_at_threshold(per_image, canonical_classes, base_conf,
                                         iou_thresh=base_iou, per_class_conf_overrides=ov)
                score_tuple = (
                    m["macro"]["micro_f1"] or 0.0,
                    m["macro"]["mAP50"] or 0.0,
                    m["macro"]["micro_precision"] or 0.0,
                    m["macro"]["micro_recall"] or 0.0,
                )
                row = {
                    "conf": float(base_conf),
                    "match_iou": float(base_iou),
                    "overrides": ov,
                    "micro_f1": score_tuple[0],
                    "mAP50": score_tuple[1],
                    "micro_precision": score_tuple[2],
                    "micro_recall": score_tuple[3],
                }
                all_rows.append(row)
                if score_tuple > best_key:
                    best = row
                    best_key = score_tuple

    return best, all_rows


def evaluate_split_engine(engine, image_dir, label_dir, is_defect,
                          split_label, conf_thresh):
    """
    Evaluate using SmartPCBInspectionEngine's accuracy-mode path (TTA + ensemble
    + per-class overrides), producing the same record schema as `evaluate_split`.

    Used when --tta/--ensemble flags are set and fresh inference is requested
    (not --from-raw).
    """
    files = sorted(
        f for f in os.listdir(image_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))
    )
    print(f"[{split_label}] {len(files)} images via engine accuracy-mode "
          f"(tta={engine.tta_enabled}, ensemble+{max(0, len(getattr(engine,'defect_models',[]))-1)} ckpts)")

    per_image = []
    t0 = time.perf_counter()
    for i, fname in enumerate(files, 1):
        img_path = os.path.join(image_dir, fname)
        img = cv2.imread(img_path)
        if img is None:
            print(f"  !! unreadable, skipped: {fname}")
            continue
        h, w = img.shape[:2]

        result = engine.inspect(img_path, conf_threshold=conf_thresh, generate_xai=False)

        # Convert engine defect/component output to the canonical schema
        dets = []
        if is_defect:
            for d in result["defects"]:
                dets.append({
                    "cls": d["class"],
                    "raw_cls": d.get("raw_class", d["class"]),
                    "raw_cls_id": d.get("class_id", -1),
                    "confidence": float(d["confidence"]),
                    "bbox": list(d["bbox"]),
                })
        else:
            for c in result["components"]:
                dets.append({
                    "cls": c["class"],
                    "raw_cls": c.get("raw_class", c["class"]),
                    "raw_cls_id": c.get("class_id", -1),
                    "confidence": float(c["confidence"]),
                    "bbox": list(c["bbox"]),
                })
        dets.sort(key=lambda d: -d["confidence"])

        stem = os.path.splitext(fname)[0]
        gt_raw = load_yolo_gt(os.path.join(label_dir, stem + ".txt"), w, h)
        gt = []
        for g in gt_raw:
            # Use gt_decode for canonical names — caller already imported it locally.
            # We resolve names in run_model; here just keep dataset-raw indices.
            gt.append({
                "cls": None,       # filled by caller via gt_decode using yaml_names
                "raw_cls": None,   # placeholder
                "raw_cls_id": g["cls_id"],
                "bbox": g["bbox"],
            })
        per_image.append({"file": fname, "detections": dets, "gt": gt,
                          "_gt_raw_cls_ids_only": True})

        if i % 20 == 0 or i == len(files):
            el = time.perf_counter() - t0
            print(f"  {i}/{len(files)}  ({el:.1f}s elapsed, {el / max(1, i):.2f}s/img)")

    n_gt_total = sum(len(r["gt"]) for r in per_image)
    if n_gt_total == 0:
        raise SystemExit(
            f"REFUSING to compute metrics for '{split_label}': 0 ground-truth boxes "
            f"found via engine path (split/label path problem)."
        )
    print(f"[{split_label}] GT boxes={n_gt_total} over {len(per_image)} images")
    return per_image


def run_model(model_key, from_raw=False, tta=False, ensemble=None,
              checkpoint_override=None, conf_range_spec=None, match_iou_spec=None,
              nms_iou_spec=None, per_class_conf_search=True):
    ensemble_parts = [p.strip() for p in (ensemble or "").split("+") if p.strip()]
    ensemble_requested = bool(ensemble_parts)

    if model_key == "component":
        model_path = checkpoint_override or os.path.join(ROOT, "models", "component_best.pt")
        data_yaml = os.path.join(ROOT, "datasets", "components_unified", "data.yaml")
        canonical = CANONICAL_COMPONENT_CLASSES
        alignment = {"mode": "name-based", "decoding": "COMPONENT_CLASS_ALIASES on both sides"}
        model_decode = lambda cid, raw: normalize_name(raw, COMPONENT_CLASS_ALIASES)
        gt_decode = lambda cid, raw: normalize_name(raw, COMPONENT_CLASS_ALIASES)
        imgsz = 1024
        out_json = os.path.join(METRICS_DIR, "component_metrics.json")
        undetectable = list(UNDETECTABLE_CURATED_COMPONENT_CLASSES)
        extra_model_paths = []
        use_accuracy_mode_engine = tta or False  # components: tta-only for now
    else:
        scratch = os.path.join(ROOT, "models", "defect_best_scratch.pt")
        legacy = os.path.join(ROOT, "models", "defect_best_legacy.pt")
        primary = checkpoint_override or scratch if os.path.exists(scratch) else os.path.join(ROOT, "models", "defect_best.pt")
        model_path = primary
        data_yaml = os.path.join(ROOT, "datasets", "defects", "data.yaml")
        canonical = CANONICAL_DEFECT_CLASSES
        alignment = {
            "mode": DEFECT_ALIGNMENT_MODE,
            "decoding": "model side POSITIONAL by class index (checkpoint name strings "
                        "are unreliable; verified on val 921/923 diagonal pairs, mean IoU "
                        "0.899); GT side identity (dataset names are already canonical)",
            "model_index_to_canonical": dict(DEFECT_MODEL_INDEX_TO_CANONICAL),
            "accuracy_mode": {
                "tta_requested": tta,
                "ensemble_requested": ensemble_requested,
                "ensemble_recipe": ensemble_parts,
            },
        }
        model_decode = lambda cid, raw: (
            DEFECT_MODEL_INDEX_TO_CANONICAL.get(int(cid), f"unknown_defect_{cid}"))
        gt_decode = lambda cid, raw: raw
        imgsz = 640
        out_json = os.path.join(METRICS_DIR, "defect_metrics.json")
        undetectable = []

        # Resolve ensemble extras
        extra_model_paths = []
        for tag in ensemble_parts:
            tag = tag.lower()
            if tag == "scratch":
                p = scratch
            elif tag == "legacy":
                p = legacy
            elif tag == "best":
                p = os.path.join(ROOT, "models", "defect_best.pt")
            else:
                p = os.path.join(ROOT, "models", tag) if not os.path.isabs(tag) else tag
            if p and os.path.exists(p) and p != model_path and p not in extra_model_paths:
                extra_model_paths.append(p)
        use_accuracy_mode_engine = tta or bool(extra_model_paths)

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
        if use_accuracy_mode_engine:
            print(f"  [{model_key}] NOTE: --from-raw re-uses baseline single-pass raw records. "
                  f"TTA/ensemble gains will NOT appear in fresh from-raw; for TTA+ensemble gains "
                  f"run without --from-raw on CPU (~40-90 min).")
        model_class_names = None
    else:
        from ultralytics import YOLO
        import torch

        print("=" * 72)
        print(f"MODEL EVALUATION — {model_key}")
        print(f"  checkpoint : {model_path}")
        print(f"  ensemble   : {[os.path.basename(p) for p in extra_model_paths] if extra_model_paths else 'none'}")
        print(f"  TTA 8-view : {tta}")
        print(f"  data yaml  : {data_yaml}")
        print(f"  alignment  : {alignment['mode']}")
        print(f"  imgsz      : {imgsz}   device: cpu   torch: {torch.__version__}   cuda: {torch.cuda.is_available()}")
        print("=" * 72)

        if use_accuracy_mode_engine:
            # Use SmartPCBInspectionEngine's accuracy-mode path (TTA + WBF fusion)
            from ai.inference.engine import SmartPCBInspectionEngine

            # Resolve nms_iou (wbf) from CLI or default
            nms_iou_list = _parse_float_list(nms_iou_spec, DEFAULT_NMS_IOUS)
            wbf_iou_default = nms_iou_list[len(nms_iou_list) // 2]  # median-ish

            comp_path = None if model_key == "defect" else model_path
            defect_path = None if model_key == "component" else model_path

            engine = SmartPCBInspectionEngine(
                component_model_path=comp_path,
                defect_model_path=defect_path,
                device="cpu",
                defect_ensemble_paths=extra_model_paths if model_key == "defect" else None,
                tta_enabled=tta,
                per_class_defect_conf_overrides=None,
                wbf_iou=wbf_iou_default,
            )
            # Use primary YOLO class names table for provenance
            if model_key == "defect" and engine.defect_models:
                model_class_names = {int(k): v for k, v in engine.defect_models[0].names.items()}
            elif engine.comp_model is not None:
                model_class_names = {int(k): v for k, v in engine.comp_model.names.items()}
            else:
                model_class_names = None

            # When using engine, detection classes are already normalized (the
            # engine's internal `_normalize_class_name` is idempotent).
            is_defect_side = (model_key == "defect")
            _low_conf = LOW_CONF_FOR_SWEEP  # engine inspect() clamps; collect loose
            val_recs_raw = evaluate_split_engine(
                engine, *split_dirs["val"], is_defect=is_defect_side,
                split_label=f"{model_key}/val_engine", conf_thresh=_low_conf,
            )
            test_recs_raw = evaluate_split_engine(
                engine, *split_dirs["test"], is_defect=is_defect_side,
                split_label=f"{model_key}/test_engine", conf_thresh=_low_conf,
            )
            # Attach canonical cls name to GT (was None in evaluate_split_engine)
            for recs in (val_recs_raw, test_recs_raw):
                for r in recs:
                    if not r.get("_gt_raw_cls_ids_only"):
                        continue
                    for g in r["gt"]:
                        cid = int(g["raw_cls_id"])
                        raw_name = yaml_names.get(cid, f"gtunk_{cid}")
                        g["raw_cls"] = raw_name
                        g["cls"] = gt_decode(cid, raw_name)
                    r.pop("_gt_raw_cls_ids_only", None)
            val_recs, test_recs = val_recs_raw, test_recs_raw
        else:
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

    # ------------------------------------------------------------------
    # Calibration sweep on VALIDATION: coarse 1D OR 4D (with per-class search)
    # ------------------------------------------------------------------
    do_4d = (model_key == "defect") or bool(conf_range_spec) or bool(match_iou_spec)
    conf_list = _conf_list_from_range_str(conf_range_spec if conf_range_spec else (
        f"{SWEEP_START}:{SWEEP_END}:{SWEEP_STEP}" if not do_4d else None
    ))
    match_iou_list = _parse_float_list(match_iou_spec,
                                       [IOU_MATCH_THRESHOLD] if not do_4d else DEFAULT_MATCH_IOUS)

    print(f"\n-- calibration sweep on VALIDATION only "
          f"(conf={min(conf_list):.3f}..{max(conf_list):.3f} step ~{np.mean(np.diff(conf_list)):.3f}, "
          f"match_IoU={match_iou_list}, 4D={do_4d}, per_class_conf_search={per_class_conf_search}) --")

    if do_4d:
        best_4d, sweep_all_rows = sweep_4d(
            val_recs, eval_space, conf_list, match_iou_list,
            search_per_class_offsets=per_class_conf_search,
            per_class_weak_candidates=PER_CLASS_WEAK_CANDIDATES if model_key == "defect" else set(),
        )
        # Re-score VAL at best 4D point for full metrics
        best_t = best_4d["conf"]
        best_match_iou = best_4d["match_iou"]
        best_overrides = best_4d["overrides"] or {}
        calibrated_val = metrics_at_threshold(
            val_recs, eval_space, best_t, iou_thresh=best_match_iou,
            per_class_conf_overrides=best_overrides,
        )
        # Flatten 4D rows into the same schema as legacy 1D (for csv writer compat)
        val_sweep = []
        seen = set()
        for row in sweep_all_rows:
            key = (round(row["conf"], 4), round(row["match_iou"], 4),
                   tuple(sorted((row["overrides"] or {}).items())) if row["overrides"] else ())
            if key in seen:
                continue
            seen.add(key)
            m = metrics_at_threshold(
                val_recs, eval_space, row["conf"], iou_thresh=row["match_iou"],
                per_class_conf_overrides=row["overrides"] or None,
            )
            val_sweep.append(m)
        print(f"  val-calibrated 4D best: conf={best_t}, match_iou={best_match_iou}, "
              f"overrides={best_overrides or 'none'}")
        print(f"  val micro-F1 = {calibrated_val['macro']['micro_f1']}, mAP50 = {calibrated_val['macro']['mAP50']}")
    else:
        val_sweep = sweep_thresholds(val_recs, eval_space)
        best = max(val_sweep, key=lambda m: (m["macro"]["micro_f1"], m["macro"]["micro_precision"]))
        best_t = best["confidence_threshold"]
        best_match_iou = IOU_MATCH_THRESHOLD
        best_overrides = None
        calibrated_val = best
        print(f"  val-calibrated threshold (best micro-F1) = {best_t}")
        print(f"  val micro-F1 at {best_t} = {best['macro']['micro_f1']}")

    default_metrics = metrics_at_threshold(test_recs, eval_space, 0.25)
    calibrated_metrics = metrics_at_threshold(
        test_recs, eval_space, best_t, iou_thresh=best_match_iou,
        per_class_conf_overrides=best_overrides,
    )
    default_map = map5095(test_recs, eval_space, 0.25)
    calibrated_map = map5095(
        test_recs, eval_space, best_t, per_class_conf_overrides=best_overrides,
    )

    print(f"\n-- TEST metrics (never used for calibration) --")
    print(f"  @conf 0.25 default match_iou=0.50 : "
          f"mAP50={default_metrics['macro']['mAP50']} mAP50-95={default_map['mAP50_95']} "
          f"microF1={default_metrics['macro']['micro_f1']}")
    print(f"  @conf {best_t} match_iou={best_match_iou} overrides={best_overrides or 'none'} : "
          f"mAP50={calibrated_metrics['macro']['mAP50']} mAP50-95={calibrated_map['mAP50_95']} "
          f"microF1={calibrated_metrics['macro']['micro_f1']}")

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
            "tta": bool(tta),
            "ensemble": bool(extra_model_paths),
            "ensemble_paths": [os.path.relpath(p, ROOT).replace("\\", "/") for p in extra_model_paths],
            "sweep_mode": "4D (conf × match_IoU × per_class)" if do_4d else "1D (conf)",
            "conf_range_spec": conf_range_spec,
            "match_iou_list": match_iou_list,
        },
        "best_operating_point_val": {
            "global_confidence": best_t,
            "match_iou": best_match_iou,
            "per_class_conf_overrides": best_overrides or None,
            "calibrated_on": "val_split",
            "selection_objective": "(micro_F1, mAP50, micro_precision, micro_recall) lex",
            "val_metrics": {
                "micro_f1": calibrated_val["macro"]["micro_f1"],
                "mAP50": calibrated_val["macro"]["mAP50"],
                "micro_precision": calibrated_val["macro"]["micro_precision"],
                "micro_recall": calibrated_val["macro"]["micro_recall"],
            },
        },
        "class_spaces": {
            "model_raw_classes": list(model_class_names.values()) if (not from_raw) and model_class_names else None,
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

    # ------------------------------------------------------------------
    # Machine-readable: best operating point JSON + improvement delta JSON
    # ------------------------------------------------------------------
    if model_key == "defect":
        bop = {
            "generated_at": datetime.now().isoformat(),
            "split_calibrated_on": "val",
            "model_checkpoints": [
                os.path.relpath(model_path, ROOT).replace("\\", "/"),
            ] + [os.path.relpath(p, ROOT).replace("\\", "/") for p in extra_model_paths],
            "tta_enabled": bool(tta),
            "global_confidence_threshold": best_t,
            "match_iou_threshold": best_match_iou,
            "per_class_conf_overrides": best_overrides or {},
            "val_metrics": payload["best_operating_point_val"]["val_metrics"],
            "test_metrics": {
                "micro_precision": calibrated_metrics["macro"]["micro_precision"],
                "micro_recall": calibrated_metrics["macro"]["micro_recall"],
                "micro_f1": calibrated_metrics["macro"]["micro_f1"],
                "mAP50": calibrated_metrics["macro"]["mAP50"],
                "mAP50_95": calibrated_map["mAP50_95"],
            },
            "per_class_AP50_test": {
                c: v["ap50"] for c, v in calibrated_metrics["per_class"].items()
                if v.get("evaluated") and v.get("ap50") is not None
            },
        }
        bop_path = os.path.join(METRICS_DIR, "best_operating_point_defect.json")
        with open(bop_path, "w") as f:
            json.dump(bop, f, indent=2)
        print(f"Written: {bop_path}")

        # Improvement delta: baseline (coarse sweep default conf=0.25 / 0.50 IoU) vs best
        baseline_test_metrics = default_metrics["macro"]
        baseline_map5095 = default_map["mAP50_95"]
        delta = {
            "generated_at": datetime.now().isoformat(),
            "deterministic_comparison_from_same_raw_records": True,
            "baseline_label": "test @ conf=0.25, match_iou=0.50 (legacy default)",
            "improved_label": (f"test @ conf={best_t}, match_iou={best_match_iou}, "
                              f"overrides={best_overrides or 'none'}, TTA={tta}, "
                              f"ensemble+{len(extra_model_paths)}"),
            "baseline": {
                "micro_precision": baseline_test_metrics["micro_precision"],
                "micro_recall": baseline_test_metrics["micro_recall"],
                "micro_f1": baseline_test_metrics["micro_f1"],
                "mAP50": baseline_test_metrics["mAP50"],
                "mAP50_95": baseline_map5095,
            },
            "improved": {
                "micro_precision": calibrated_metrics["macro"]["micro_precision"],
                "micro_recall": calibrated_metrics["macro"]["micro_recall"],
                "micro_f1": calibrated_metrics["macro"]["micro_f1"],
                "mAP50": calibrated_metrics["macro"]["mAP50"],
                "mAP50_95": calibrated_map["mAP50_95"],
            },
            "delta_percentage_points": {
                "micro_precision_pp": round(
                    (calibrated_metrics["macro"]["micro_precision"] - baseline_test_metrics["micro_precision"]) * 100, 2),
                "micro_recall_pp": round(
                    (calibrated_metrics["macro"]["micro_recall"] - baseline_test_metrics["micro_recall"]) * 100, 2),
                "micro_f1_pp": round(
                    (calibrated_metrics["macro"]["micro_f1"] - baseline_test_metrics["micro_f1"]) * 100, 2),
                "mAP50_pp": round(
                    (calibrated_metrics["macro"]["mAP50"] - (baseline_test_metrics["mAP50"] or 0.0)) * 100, 2),
                "mAP50_95_pp": round(
                    (calibrated_map["mAP50_95"] - (baseline_map5095 or 0.0)) * 100, 2),
            },
            "honest_status_vs_95pct_targets": {
                "target_defect_mAP50_ge_95pct": (
                    "PASS" if calibrated_metrics["macro"]["mAP50"] and calibrated_metrics["macro"]["mAP50"] >= 0.95
                    else "FAIL" if calibrated_metrics["macro"]["mAP50"] is not None else "UNVERIFIED"),
                "measured_defect_mAP50_pct": None if calibrated_metrics["macro"]["mAP50"] is None else
                    round(calibrated_metrics["macro"]["mAP50"] * 100, 2),
                "target_defect_mAP5095_ge_95pct": (
                    "FAIL (explicitly unreachable per plan; max 1-5pp gain from inference tricks)"),
                "target_defect_precision_recall_f1_all_ge_95pct": {
                    "precision_ge_95": "PASS" if calibrated_metrics["macro"]["micro_precision"] >= 0.95 else "FAIL",
                    "recall_ge_95": "PASS" if calibrated_metrics["macro"]["micro_recall"] >= 0.95 else "FAIL",
                    "f1_ge_95": "PASS" if calibrated_metrics["macro"]["micro_f1"] >= 0.95 else "FAIL",
                },
            },
        }
        delta_path = os.path.join(METRICS_DIR, "improvement_delta_defect.json")
        with open(delta_path, "w") as f:
            json.dump(delta, f, indent=2)
        print(f"Written: {delta_path}")
        print(f"\n-- IMPROVEMENT DELTA vs baseline (same raw records, deterministic) --")
        for k, v in delta["delta_percentage_points"].items():
            print(f"  {k:30s}: {v:+.2f} pp")
        status = delta["honest_status_vs_95pct_targets"]
        print(f"  mAP50 ≥95%: {status['target_defect_mAP50_ge_95pct']} "
              f"(measured={status['measured_defect_mAP50_pct']}%)")
        for k, v in status["target_defect_precision_recall_f1_all_ge_95pct"].items():
            print(f"  {k}: {v}")

    # ------------------------------------------------------------------
    # CSV outputs (threshold sweep, per-class)
    # ------------------------------------------------------------------
    sweep_csv = os.path.join(METRICS_DIR, f"threshold_sweep_{model_key}.csv")
    with open(sweep_csv, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["split", "confidence_threshold", "match_iou", "per_class_overrides",
                    "micro_precision", "micro_recall",
                    "micro_f1", "macro_precision", "macro_recall", "macro_f1", "mAP50"])
        for m in val_sweep:
            ov_str = ""
            if m.get("per_class_conf_overrides"):
                ov_str = json.dumps(m["per_class_conf_overrides"], sort_keys=True)
            w.writerow(["val", m["confidence_threshold"], m["iou_match_threshold"], ov_str,
                        m["macro"]["micro_precision"],
                        m["macro"]["micro_recall"], m["macro"]["micro_f1"],
                        m["macro"]["macro_precision"], m["macro"]["macro_recall"],
                        m["macro"]["macro_f1"], m["macro"]["mAP50"]])
        for label, m in (("default_0.25", default_metrics), ("calibrated", calibrated_metrics)):
            ov_str = ""
            if m.get("per_class_conf_overrides"):
                ov_str = json.dumps(m["per_class_conf_overrides"], sort_keys=True)
            w.writerow(["test", m["confidence_threshold"], m["iou_match_threshold"], ov_str,
                        m["macro"]["micro_precision"],
                        m["macro"]["micro_recall"], m["macro"]["micro_f1"],
                        m["macro"]["macro_precision"], m["macro"]["macro_recall"],
                        m["macro"]["macro_f1"], m["macro"]["mAP50"]])
    print(f"Written: {sweep_csv}")

    per_class_csv = os.path.join(METRICS_DIR, f"per_class_{model_key}.csv")
    with open(per_class_csv, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["eval_conf", "match_iou", "overrides", "class", "gt_count", "pred_count", "tp", "fp", "fn",
                    "precision", "recall", "f1", "ap50"])
        for label, m in (("0.25", default_metrics), (f"calibrated@{best_t}", calibrated_metrics)):
            ov_str = ""
            if m.get("per_class_conf_overrides"):
                ov_str = json.dumps(m["per_class_conf_overrides"], sort_keys=True)
            for c, v in m["per_class"].items():
                if not v.get("evaluated"):
                    w.writerow([label, m["iou_match_threshold"], ov_str, c,
                                v.get("gt_count", 0), v.get("pred_count", 0),
                                "", "", "", "", "", "", ""])
                    continue
                w.writerow([label, m["iou_match_threshold"], ov_str, c,
                            v["gt_count"], v["pred_count"], v["tp"], v["fp"],
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
                    help="re-score from persisted raw detections/GT (skip inference). "
                         "If combined with --tta/--ensemble, re-score uses baseline raw records; "
                         "new TTA/ensemble gains require fresh inference (omit --from-raw).")
    ap.add_argument("--tta", action="store_true",
                    help="enable 8-view Test-Time Augmentation (orig, H/V/HV-flip, 0.85×, 1.15×, ±5° rot)")
    ap.add_argument("--ensemble", default=None,
                    help="defect ensemble recipe, '+'-separated tags. Example: 'scratch+legacy' "
                         "for defect_best_scratch + defect_best_legacy via WBF fusion. Tags: scratch, legacy, best, or basename in models/.")
    ap.add_argument("--checkpoint-override", default=None,
                    help="override deployed checkpoint path for --model.")
    ap.add_argument("--conf-range", default=None, dest="conf_range",
                    help="confidence sweep as 'start:end:step'. Defaults for defect: 0.05:0.95:0.025 (4D sweep), "
                         "component: 0.10:0.70:0.05 (coarse).")
    ap.add_argument("--nms-iou-list", default=None, dest="nms_iou_list",
                    help="comma-separated NMS/WBF IoU thresholds to try in fresh inference mode (used for WBF IoU).")
    ap.add_argument("--match-iou-list", default=None, dest="match_iou_list",
                    help="comma-separated match IoU thresholds for scoring. Defaults defect: 0.40,0.45,0.50,0.55,0.60")
    ap.add_argument("--no-per-class-conf", dest="per_class_conf", action="store_false", default=True,
                    help="disable per-class ±0.05 conf offset search for weak classes.")
    args = ap.parse_args()

    keys = ["component", "defect"] if args.model == "both" else [args.model]
    for k in keys:
        run_model(
            k,
            from_raw=args.from_raw,
            tta=bool(args.tta),
            ensemble=args.ensemble,
            checkpoint_override=args.checkpoint_override,
            conf_range_spec=args.conf_range,
            match_iou_spec=args.match_iou_list,
            nms_iou_spec=args.nms_iou_list,
            per_class_conf_search=bool(args.per_class_conf),
        )
        print()


if __name__ == "__main__":
    main()
