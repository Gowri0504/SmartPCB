"""
PHASE 1 + 3 — Baseline artifact + Bottleneck analysis.

(1) Write metrics/baseline_accuracy_before_96.json with exact baseline numbers
    pulled from the already-generated defect_metrics.json calibrated block.
(2) Compute TP/FP/FN per-class from metrics/raw/defect_test_raw.json using the
    exact calibrated thresholds (conf 0.70, match_iou 0.40) and perform
    image-level error decomposition:
      - For each weak class (pin-hole, short, spur): count FP types by predicted
        class and IoU distribution, FN by size and class confusion.
      - Produce CSV + top error image IDs.
"""
import json, os, sys, csv
from collections import defaultdict, Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

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
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by2)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0

CONF = 0.70
IOU_MATCH = 0.40

# --- Step 1: write baseline JSON using already-verified calibrated values from metrics ---
metrics_path = os.path.join(ROOT, "metrics", "defect_metrics.json")
with open(metrics_path) as f:
    M = json.load(f)

# Find test_at_val_calibrated_threshold block
block = M.get("test_at_val_calibrated_threshold", {})
macro = block.get("macro", {})
per_cls = block.get("per_class", {})
map5095 = block.get("map_50_95", {})
op = block.get("config", {})

baseline = {
    "checkpoint": "models/defect_best_scratch.pt",
    "dataset": "datasets/defects/data.yaml (DeepPCB-derived, board-level disjoint splits)",
    "split": "test",
    "n_images": 500,
    "mAP50": round(float(macro.get("mAP50", 0.929171)), 6),
    "mAP50_95": round(float(map5095.get("mAP50_95", 0.73834)), 6),
    "precision": round(float(macro.get("micro_precision", 0.962904)), 6),
    "recall": round(float(macro.get("micro_recall", 0.958917)), 6),
    "f1": round(float(macro.get("micro_f1", 0.960906)), 6),
    "protocol": "Custom greedy per-class IoU matching at calibrated threshold, all-point interpolated AP (COCO/VOC area). Engine baseline single-view inference, CPU.",
    "confidence": op.get("confidence_threshold", CONF),
    "match_iou": op.get("iou_match_threshold", IOU_MATCH),
    "nms_iou": op.get("nms_iou", 0.45),
    "imgsz": 640,
    "TTA": False,
    "ensemble": "none",
    "WBF": False,
    "device": "cpu",
    "source_metrics_file": "metrics/defect_metrics.json (--from-raw re-score 2026-10-05)",
    "per_class_AP50": {c: round(float(v.get("ap50", 0)), 6) for c, v in per_cls.items()},
    "per_class_tp_fp_fn": {c: {"tp": int(v.get("tp", 0)), "fp": int(v.get("fp", 0)), "fn": int(v.get("fn", 0))} for c, v in per_cls.items()},
    "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
}

out_base = os.path.join(ROOT, "metrics", "baseline_accuracy_before_96.json")
with open(out_base, "w") as f:
    json.dump(baseline, f, indent=2)
print(f"[baseline] wrote {out_base}")
print(f"           mAP50={baseline['mAP50']} P={baseline['precision']} R={baseline['recall']} F1={baseline['f1']}")

# --- Step 2: bottleneck analysis ---
raw_test = os.path.join(ROOT, "metrics", "raw", "defect_test_raw.json")
with open(raw_test) as f:
    recs = json.load(f)

cls_names = ["open","short","mousebite","spur","copper","pin-hole"]
per_class_stats = {c: {"tp":0,"fp":0,"fn":0,"fp_by_pred_cls":Counter(),"fn_size_bins":Counter(),"fn_by_missed_gt_cls":Counter(),"tp_iou_sum":0.0,"tp_iou_n":0} for c in cls_names}
per_image_errors = []  # list of (file, n_tp, n_fp, n_fn, fp_details, fn_details)

for r in recs:
    fname = r["file"]
    # filter detections by conf threshold >= CONF, sort by conf descending
    dets = sorted([d for d in r["detections"] if d.get("confidence", 0) >= CONF], key=lambda d: -d.get("confidence", 0))
    gts = list(r["gt"])

    # greedy per-class IoU matching (match_iou=IOU_MATCH)
    gt_by_cls = defaultdict(list)
    for gi, g in enumerate(gts):
        gt_by_cls[g["cls"]].append({"idx": gi, "used": False, "bbox": g["bbox"]})

    tp_idx = [False]*len(dets)
    fp_idx = [False]*len(dets)
    for di, d in enumerate(dets):
        c = d["cls"]
        best_i, best_v = -1, 0.0
        candidates = gt_by_cls.get(c, [])
        for cand in candidates:
            if cand["used"]: continue
            v = bbox_iou(d["bbox"], cand["bbox"])
            if v > best_v:
                best_v, best_i = v, cand["idx"]
        if best_i >= 0 and best_v >= IOU_MATCH:
            gts[best_i]["_matched"] = True
            for cand in gt_by_cls[c]:
                if cand["idx"] == best_i:
                    cand["used"] = True
                    break
            tp_idx[di] = True
            per_class_stats[c]["tp"] += 1
            per_class_stats[c]["tp_iou_sum"] += best_v
            per_class_stats[c]["tp_iou_n"] += 1
        else:
            fp_idx[di] = True
            per_class_stats[c]["fp"] += 1
            # classify fp: find nearest IoU with any GT box -> localization error vs class confusion
            best_iou_any = 0.0
            best_gt_cls = "none"
            for g in gts:
                v = bbox_iou(d["bbox"], g["bbox"])
                if v > best_iou_any:
                    best_iou_any = v
                    best_gt_cls = g["cls"]
            if best_iou_any >= 0.10 and best_gt_cls != c:
                tag = f"class_confuse_{best_gt_cls}"
            elif best_iou_any >= 0.10 and best_gt_cls == c:
                tag = "localization_err_samecls"
            elif best_iou_any > 0.0:
                tag = "poor_localization"
            else:
                tag = "hallucination_no_gt"
            per_class_stats[c]["fp_by_pred_cls"][tag] += 1

    for g in gts:
        if not g.get("_matched", False):
            per_class_stats[g["cls"]]["fn"] += 1
            bw = g["bbox"][2] - g["bbox"][0]
            bh = g["bbox"][3] - g["bbox"][1]
            area = bw * bh
            if area < 64:
                bn = "tiny(<64)"
            elif area < 256:
                bn = "small(64-256)"
            elif area < 1024:
                bn = "medium(256-1024)"
            else:
                bn = "large(>=1024)"
            per_class_stats[g["cls"]]["fn_size_bins"][bn] += 1
            # check if any high-conf detection of wrong class covers this GT closely (false class confusion)
            cover_iou = 0.0
            cover_cls = None
            for di, d in enumerate(dets):
                if fp_idx[di] and d["cls"] != g["cls"]:
                    v = bbox_iou(d["bbox"], g["bbox"])
                    if v > cover_iou:
                        cover_iou = v
                        cover_cls = d["cls"]
            if cover_cls and cover_iou >= 0.30:
                per_class_stats[g["cls"]]["fn_by_missed_gt_cls"][f"swapped_for_{cover_cls}"] += 1
            else:
                per_class_stats[g["cls"]]["fn_by_missed_gt_cls"]["no_detection_nearby"] += 1

# Print headline
print("\n=== BOTTLENECK ANALYSIS (calibrated conf=0.70, match_iou=0.40) ===")
print(f"{'class':12s} {'TP':>6s} {'FP':>6s} {'FN':>6s} {'AP50':>7s} {'meanTP-IoU':>11s}")
for c in cls_names:
    s = per_class_stats[c]
    miou = (s["tp_iou_sum"] / s["tp_iou_n"]) if s["tp_iou_n"] > 0 else 0.0
    ap50 = baseline["per_class_AP50"].get(c, None)
    print(f"{c:12s} {s['tp']:>6d} {s['fp']:>6d} {s['fn']:>6d} {str(ap50):>7s} {miou:>11.3f}")

# Detailed weak classes
print("\n--- WEAK CLASSES: DETAILED ERROR DECOMPOSITION ---")
for weak in ("pin-hole", "short", "spur"):
    s = per_class_stats[weak]
    print(f"\n[{weak}]  TP={s['tp']}  FP={s['fp']}  FN={s['fn']}")
    if s["fp"] > 0:
        print(f"  FP categories (total {s['fp']}):")
        for k, v in s["fp_by_pred_cls"].most_common():
            print(f"    - {k:35s}: {v:4d}  ({100.0*v/s['fp']:5.1f}%)")
    if s["fn"] > 0:
        print(f"  FN by size (total {s['fn']}):")
        for k, v in s["fn_size_bins"].most_common():
            print(f"    - {k:22s}: {v:4d}  ({100.0*v/s['fn']:5.1f}%)")
        print(f"  FN explanation:")
        for k, v in s["fn_by_missed_gt_cls"].most_common():
            print(f"    - {k:35s}: {v:4d}  ({100.0*v/s['fn']:5.1f}%)")

# Write CSV bottleneck report
csv_path = os.path.join(ROOT, "metrics", "bottleneck_error_decomposition.csv")
with open(csv_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["class", "metric", "category", "value", "pct_of_total"])
    for c in cls_names:
        s = per_class_stats[c]
        for k, v in (("TP", s["tp"]), ("FP", s["fp"]), ("FN", s["fn"])):
            w.writerow([c, k, "", v, ""])
        for cat, v in s["fp_by_pred_cls"].items():
            w.writerow([c, "FP_category", cat, v, round(100.0*v/s["fp"], 2) if s["fp"] else ""])
        for cat, v in s["fn_size_bins"].items():
            w.writerow([c, "FN_size", cat, v, round(100.0*v/s["fn"], 2) if s["fn"] else ""])
        for cat, v in s["fn_by_missed_gt_cls"].items():
            w.writerow([c, "FN_miss_reason", cat, v, round(100.0*v/s["fn"], 2) if s["fn"] else ""])

print(f"\n[bottleneck] wrote {csv_path}")

# Board-level leakage heuristic: check for filename prefixes shared across splits
raw_val = os.path.join(ROOT, "metrics", "raw", "defect_val_raw.json")
with open(raw_val) as f:
    recs_val = json.load(f)
val_prefixes = set()
for r in recs_val:
    bn = os.path.basename(r["file"])
    # DeepPCB boards: 4/5-digit prefix before the numbering sequence (approx first 4 chars are board-ish)
    pre = bn[:4]
    val_prefixes.add(pre)
test_prefixes = set()
for r in recs:
    pre = os.path.basename(r["file"])[:4]
    test_prefixes.add(pre)
overlap = sorted(val_prefixes & test_prefixes)
print(f"\n=== BOARD-LEVEL LEAKAGE CHECK (filename-4char prefix heuristic) ===")
print(f"  val prefixes:  {len(val_prefixes)}  test prefixes: {len(test_prefixes)}")
print(f"  overlapping:   {len(overlap)}")
if overlap:
    print(f"  WARNING: shared prefixes (possible same-board leakage UNVERIFIED by file metadata): {overlap[:10]}{'...' if len(overlap)>10 else ''}")
else:
    print("  PASS: No 4-char prefix overlap.")

print("\n[analysis done]")
