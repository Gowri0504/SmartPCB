"""
TTA (Test-Time Augmentation) + Weighted Boxes Fusion (WBF) utilities.

Pure-numpy implementation (no extra pip dependencies).

References:
  * TTA standard strategies: original, H/V/HV-flip, scale perturbation, small rotations.
  * WBF: Zverev et al., "Weighted Boxes Fusion: ensembling boxes for object detection models", 2020.
    Class-aware fusion buckets prevent mixing classes.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Tuple

import cv2
import numpy as np

Box = Dict
BoxList = List[Box]

BOX_FORMAT = dict  # {bbox: [x1,y1,x2,y2], class: str, confidence: float, ...}


# ---------------------------------------------------------------------------
# TTA transforms
# ---------------------------------------------------------------------------

def _rotate_point(x: float, y: float, cx: float, cy: float, angle_deg: float) -> Tuple[float, float]:
    r = math.radians(-angle_deg)  # inverse direction
    cos, sin = math.cos(r), math.sin(r)
    dx, dy = x - cx, y - cy
    return cx + dx * cos - dy * sin, cy + dx * sin + dy * cos


def run_tta_8view(img_bgr: np.ndarray) -> List[Tuple[str, np.ndarray, Callable[[BoxList], BoxList]]]:
    """
    Produce 8 views of the same image and corresponding inverse-mapping
    callables that translate detections on the augmented view back to the
    original image coordinates.

    Each entry: (aug_name, transformed_img, inverse_fn(list_of_boxes))

    Augmentations:
      0. original
      1. horizontal flip
      2. vertical flip
      3. horizontal + vertical flip
      4. scale 0.85x (pad to original size)
      5. scale 1.15x (center-crop to original size)
      6. rotate +5 degrees (pad/crop keep size)
      7. rotate -5 degrees (pad/crop keep size)
    """
    H, W = img_bgr.shape[:2]
    views: List[Tuple[str, np.ndarray, Callable[[BoxList], BoxList]]] = []

    # 0. original
    views.append(("orig", img_bgr, lambda bs: [dict(b) for b in bs]))

    # 1. horizontal flip
    flipped_h = cv2.flip(img_bgr, 1)
    def inv_h(boxes, W=W):
        out = []
        for b in boxes:
            b = dict(b)
            x1, y1, x2, y2 = b["bbox"]
            b["bbox"] = [W - x2, y1, W - x1, y2]
            out.append(b)
        return out
    views.append(("hflip", flipped_h, inv_h))

    # 2. vertical flip
    flipped_v = cv2.flip(img_bgr, 0)
    def inv_v(boxes, H=H):
        out = []
        for b in boxes:
            b = dict(b)
            x1, y1, x2, y2 = b["bbox"]
            b["bbox"] = [x1, H - y2, x2, H - y1]
            out.append(b)
        return out
    views.append(("vflip", flipped_v, inv_v))

    # 3. horizontal + vertical flip
    flipped_hv = cv2.flip(img_bgr, -1)
    def inv_hv(boxes, W=W, H=H):
        out = []
        for b in boxes:
            b = dict(b)
            x1, y1, x2, y2 = b["bbox"]
            b["bbox"] = [W - x2, H - y2, W - x1, H - y1]
            out.append(b)
        return out
    views.append(("hvflip", flipped_hv, inv_hv))

    # 4. scale 0.85 -> center into canvas of original size
    s = 0.85
    new_w, new_h = max(1, int(W * s)), max(1, int(H * s))
    small = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
    canvas_s = np.zeros_like(img_bgr)
    ox, oy = (W - new_w) // 2, (H - new_h) // 2
    canvas_s[oy:oy + new_h, ox:ox + new_w] = small
    def inv_s085(boxes, s=s, ox=ox, oy=oy):
        out = []
        for b in boxes:
            b = dict(b)
            x1, y1, x2, y2 = b["bbox"]
            b["bbox"] = [(x1 - ox) / s, (y1 - oy) / s, (x2 - ox) / s, (y2 - oy) / s]
            out.append(b)
        return out
    views.append(("scale085", canvas_s, inv_s085))

    # 5. scale 1.15 -> center crop to original size
    s = 1.15
    new_w, new_h = max(1, int(W * s)), max(1, int(H * s))
    big = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    cx, cy = new_w // 2, new_h // 2
    x1_c = max(0, cx - W // 2)
    y1_c = max(0, cy - H // 2)
    canvas_l = big[y1_c:y1_c + H, x1_c:x1_c + W]
    if canvas_l.shape[:2] != (H, W):
        canvas_l = cv2.resize(canvas_l, (W, H), interpolation=cv2.INTER_LINEAR)
    def inv_s115(boxes, s=s, x1_c=x1_c, y1_c=y1_c):
        out = []
        for b in boxes:
            b = dict(b)
            x1, y1, x2, y2 = b["bbox"]
            b["bbox"] = [(x1 + x1_c) / s, (y1 + y1_c) / s, (x2 + x1_c) / s, (y2 + y1_c) / s]
            out.append(b)
        return out
    views.append(("scale115", canvas_l, inv_s115))

    # 6. rotate +5
    for angle in (+5, -5):
        M = cv2.getRotationMatrix2D((W / 2, H / 2), angle, 1.0)
        rotated = cv2.warpAffine(img_bgr, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        def inv_rot(boxes, angle=angle, W=W, H=H):
            cx, cy = W / 2, H / 2
            out = []
            for b in boxes:
                b = dict(b)
                x1, y1, x2, y2 = b["bbox"]
                nx1, ny1 = _rotate_point(x1, y1, cx, cy, -angle)
                nx2, ny2 = _rotate_point(x2, y2, cx, cy, -angle)
                pts = [_rotate_point(x, y, cx, cy, -angle) for x, y in [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]]
                nxs = [p[0] for p in pts]
                nys = [p[1] for p in pts]
                b["bbox"] = [min(nxs), min(nys), max(nxs), max(nys)]
                out.append(b)
            return out
        views.append((f"rot{'p' if angle > 0 else 'm'}{abs(angle)}", rotated, inv_rot))

    return views


# ---------------------------------------------------------------------------
# Weighted Boxes Fusion (WBF)
# ---------------------------------------------------------------------------

def _iou(box_a: List[float], box_b: List[float]) -> float:
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    if x2 - x1 <= 0 or y2 - y1 <= 0:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    a1 = max(0.0, (box_a[2] - box_a[0]) * (box_a[3] - box_a[1]))
    a2 = max(0.0, (box_b[2] - box_b[0]) * (box_b[3] - box_b[1]))
    return inter / (a1 + a2 - inter + 1e-12)


def weighted_boxes_fusion(boxes_list: BoxList, iou_thresh: float = 0.5,
                          conf_type: str = "avg", skip_box_thresh: float = 0.0001,
                          class_aware: bool = True) -> BoxList:
    """
    Weighted Boxes Fusion — class-aware.

    boxes_list: [ {bbox:[x1,y1,x2,y2], class: str, confidence: float, ...}, ... ]
    iou_thresh: IoU threshold to group overlapping boxes.
    conf_type : "avg"  -> weighted average confidence of fused cluster, scaled by cluster size.
                "max"  -> max confidence of cluster.
    skip_box_thresh: discard incoming boxes below this confidence.

    Returns list of fused boxes with same schema.
    """
    if not boxes_list:
        return []

    filtered: BoxList = []
    for b in boxes_list:
        try:
            if b is None or not isinstance(b, dict):
                continue
            c = float(b.get("confidence", 0.0))
            if c >= skip_box_thresh:
                filtered.append(b)
        except (TypeError, ValueError):
            continue
    if not filtered:
        return []

    # Class-aware fusion buckets
    buckets: Dict[str, BoxList] = {}
    for b in filtered:
        cls = (b.get("class") if class_aware else "__all__") or "__all__"
        buckets.setdefault(cls, []).append(b)

    fused_all: BoxList = []
    for cls, bucket in buckets.items():
        # Sort by confidence descending
        bucket_sorted = sorted(bucket, key=lambda x: float(x.get("confidence", 0.0)), reverse=True)
        clusters: List[List[Box]] = []  # each cluster = list of boxes to fuse
        for box in bucket_sorted:
            matched = False
            for cluster in clusters:
                # Compare with the cluster's "main" box (first/highest conf)
                rep = cluster[0]
                if _iou(box["bbox"], rep["bbox"]) > iou_thresh:
                    cluster.append(box)
                    matched = True
                    break
            if not matched:
                clusters.append([box])

        # For each cluster -> fused box
        for cluster in clusters:
            confs = np.array([float(b.get("confidence", 0.0)) for b in cluster], dtype=np.float64)
            coords = np.array([b["bbox"] for b in cluster], dtype=np.float64)
            T = len(cluster)
            if conf_type == "max":
                fused_conf = float(confs.max())
                weights = np.ones_like(confs)
            else:  # avg (weighted average scaled by cluster size)
                weights = confs.copy()
                fused_conf = float(weights.sum() / max(1, weights.sum()))  # placeholder, overwritten next

            # Weighted average coordinates
            wsum = float(weights.sum()) if weights.sum() > 0 else 1.0
            fused_coords = (coords * weights[:, None]).sum(axis=0) / wsum
            fused_coords = [float(v) for v in fused_coords.tolist()]

            # Final confidence per WBF paper formula for "avg":
            #   C_fused = (sum C_i) * min(T, N_models) / N_models
            # Since we may not know N_models here, use cluster-length scaling:
            if conf_type != "max":
                fused_conf = float(confs.sum() * min(T, 8) / max(1, 8))
                fused_conf = float(min(1.0, fused_conf))

            fused_box = dict(cluster[0])
            fused_box["bbox"] = fused_coords
            fused_box["confidence"] = round(fused_conf, 4)
            fused_box["_cluster_size"] = T
            fused_all.append(fused_box)

    # Sort final list by confidence descending for downstream NMS stability
    fused_all.sort(key=lambda x: float(x.get("confidence", 0.0)), reverse=True)
    return fused_all


# ---------------------------------------------------------------------------
# Ensemble prediction helper (consumed by engine.py)
# ---------------------------------------------------------------------------

def ensemble_predict(models: List,  # list of YOLO model instances
                     img_bgr: np.ndarray,
                     predict_fn: Callable,
                     tta_enabled: bool = False,
                     wbf_iou: float = 0.5) -> BoxList:
    """
    Runs every model against the image (with optional 8-view TTA).
    Gathers all boxes across all models × all views → maps back to original
    coordinates → class-aware WBF fusion.

    predict_fn(model, img) -> list[Box]
      caller must wrap model.predict() and produce normalized boxes with
      keys bbox=[x1,y1,x2,y2] in input-img coords, class, confidence.
    """
    all_boxes: BoxList = []

    if tta_enabled:
        views = run_tta_8view(img_bgr)
    else:
        views = [("orig", img_bgr, lambda bs: [dict(b) for b in bs])]

    for aug_name, aug_img, inv_fn in views:
        for m_idx, model in enumerate(models):
            detections = predict_fn(model, aug_img)
            for d in detections:
                d = dict(d)
                d.setdefault("_source", {}).update({})
                d["_view"] = aug_name
                d["_model_idx"] = m_idx
            # map coords back to original image space
            mapped = inv_fn(detections)
            all_boxes.extend(mapped)

    # Weighted box fusion across all sources & views
    fused = weighted_boxes_fusion(all_boxes, iou_thresh=wbf_iou, conf_type="avg")

    # Strip internal bookkeeping before returning to engine
    for b in fused:
        for k in ("_view", "_model_idx", "_cluster_size"):
            b.pop(k, None)
    return fused
