"""
Custom expanded 4D sweep with LARGER per-class conf override search range.
Default sweep_4d only searches ±0.05 on weak classes. Bottleneck analysis
shows pin-hole needs +0.10 to +0.15 conf offset. Short & spur also benefit
from ±0.10 search. Uses same code path as sweep_4d but manually invoked
with expanded parameters. Runs entirely on --from-raw records (instant).
"""
import json, os, sys, itertools, time, csv
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "evaluation"))

from evaluate_deployed_models import (
    metrics_at_threshold, sweep_4d, average_precision, bbox_iou, match_image,
    compute_prf, _conf_list_from_range_str, _parse_float_list,
    DEFAULT_CONF_RANGE, DEFAULT_MATCH_IOUS, PER_CLASS_WEAK_CANDIDATES,
)
from ai.config import CANONICAL_DEFECT_CLASSES

t0 = time.time()
val_recs = json.load(open(os.path.join(ROOT, "metrics", "raw", "defect_val_raw.json")))
test_recs = json.load(open(os.path.join(ROOT, "metrics", "raw", "defect_test_raw.json")))
print(f"Loaded VAL={len(val_recs)} imgs, TEST={len(test_recs)} imgs")

# --- Hyper-parameter grid ---
conf_list = _conf_list_from_range_str("0.60:0.82:0.01")   # 23 global confs
match_list = [0.38, 0.40, 0.42, 0.44, 0.46, 0.48, 0.50]   # 7 match IoUs
# Expanded offset range: ±0.15 for pin-hole, ±0.10 for short/spur
# offset_options: None=none; float=positive (raise conf threshold for this class); negative (lower threshold)
# We care most about PIN-HOLE and SHORT since those drive the ~7pp gap vs 95%
weak_cls = ["pin-hole", "short", "spur"]
# per-class override candidates: relative to global conf. We want big boosts for
# pin-hole (which has many hallucinated FPs) and either direction for short/spur.
offset_candidates = {
    "pin-hole": [None, +0.05, +0.08, +0.10, +0.12, +0.15, +0.18],
    "short":    [None, -0.05, 0.0, +0.03, +0.05, +0.08, +0.10],
    "spur":     [None, -0.03, 0.0, +0.03, +0.05, +0.08],
}

# Compute all tuples: total = 23 * 7 * 7 * 7 * 7 * 7 = 23*7^5 = way too big (~553k)
# Too slow. Do 2-stage: first find best (global conf, match_iou) with no overrides.
# Then expand override search around that best tuple only.

print(f"\nStage 1: Global conf × match_IoU sweep (no per-class overrides)...")
best_stage1 = None  # (score_tuple, global_conf, match_iou)
rows = []
for gc in conf_list:
    for miou in match_list:
        r = metrics_at_threshold(val_recs, CANONICAL_DEFECT_CLASSES, gc, iou_thresh=miou, per_class_conf_overrides=None)
        mac = r.get("macro", {})
        f1 = float(mac.get("micro_f1", 0))
        map50 = float(mac.get("mAP50", 0))
        p = float(mac.get("micro_precision", 0))
        rc = float(mac.get("micro_recall", 0))
        score = (round(f1, 8), round(map50, 8), round(p, 8), round(rc, 8))
        rows.append((gc, miou, f1, map50, p, rc))
        if best_stage1 is None or score > best_stage1[0]:
            best_stage1 = (score, gc, miou)

s, gc_best, miou_best = best_stage1
print(f"  Stage 1 best: global_conf={gc_best:.4f}, match_iou={miou_best:.2f}")
print(f"    Val: F1={s[0]:.6f} mAP50={s[1]:.6f} P={s[2]:.6f} R={s[3]:.6f}")

# Stage 2: around (gc_best, miou_best) — try per-class offset combos + 3 nearby confs + 3 nearby ious
gc_near = [gc_best - 0.02, gc_best - 0.01, gc_best, gc_best + 0.01, gc_best + 0.02]
gc_near = sorted({round(x, 4) for x in gc_near if 0.55 <= x <= 0.95})
iou_idx = match_list.index(miou_best)
iou_near = [match_list[k] for k in range(max(0, iou_idx-1), min(len(match_list), iou_idx+2))]

print(f"\nStage 2: Per-class offset search around {gc_near} × {iou_near}")
keys_p = list(offset_candidates.keys())
vals_p = [offset_candidates[k] for k in keys_p]
n_combos = len(gc_near) * len(iou_near)
for v in vals_p: n_combos *= len(v)
print(f"  Candidate tuples to evaluate: {n_combos} (exhaustive)")

best_stage2 = None
n_eval = 0
t1 = time.time()
for gc in gc_near:
    for miou in iou_near:
        for ov_comb in itertools.product(*vals_p):
            ov_map = {}
            for cls, ov in zip(keys_p, ov_comb):
                if ov is not None:
                    eff = gc + ov
                    if 0.55 <= eff <= 0.98:
                        ov_map[cls] = eff
            ov_arg = ov_map if ov_map else None
            r = metrics_at_threshold(val_recs, CANONICAL_DEFECT_CLASSES, gc, iou_thresh=miou, per_class_conf_overrides=ov_arg)
            mac = r.get("macro", {})
            f1 = float(mac.get("micro_f1", 0))
            map50 = float(mac.get("mAP50", 0))
            p = float(mac.get("micro_precision", 0))
            rc = float(mac.get("micro_recall", 0))
            score = (round(f1, 8), round(map50, 8), round(p, 8), round(rc, 8))
            n_eval += 1
            if best_stage2 is None or score > best_stage2[0]:
                best_stage2 = (score, gc, miou, ov_arg or {}, dict(zip(keys_p, ov_comb)))

s, gc_final, miou_final, eff_overrides, raw_offsets = best_stage2
print(f"  Evaluated {n_eval} tuples in {time.time()-t1:.1f}s")
print(f"  Stage 2 best: global_conf={gc_final:.4f}, match_iou={miou_final:.2f}")
print(f"    Offsets (raw): {raw_offsets}")
print(f"    Effective per-class thresholds: {eff_overrides}")
print(f"    Val: F1={s[0]:.6f} mAP50={s[1]:.6f} P={s[2]:.6f} R={s[3]:.6f}")

# --- Apply final op point to LOCKED TEST SET (never used for calibration) ---
print(f"\n--- LOCKED TEST EVALUATION (never used for calibration) ---")
r_test = metrics_at_threshold(test_recs, CANONICAL_DEFECT_CLASSES, gc_final, iou_thresh=miou_final, per_class_conf_overrides=(eff_overrides if eff_overrides else None))
mac_t = r_test.get("macro", {})
pc_t = r_test.get("per_class", {})
map5095_t = r_test.get("map_50_95", {})

test_mAP50 = float(mac_t.get("mAP50", 0))
test_mAP5095 = float(map5095_t.get("mAP50_95", 0)) if isinstance(map5095_t, dict) else 0.0
test_P = float(mac_t.get("micro_precision", 0))
test_R = float(mac_t.get("micro_recall", 0))
test_F1 = float(mac_t.get("micro_f1", 0))

print(f"  Test @conf={gc_final:.4f} IoU={miou_final:.2f} overrides={eff_overrides}")
print(f"    mAP50    = {test_mAP50*100:.4f}%")
print(f"    mAP50-95 = {test_mAP5095*100:.4f}%")
print(f"    Precision = {test_P*100:.4f}%")
print(f"    Recall    = {test_R*100:.4f}%")
print(f"    F1        = {test_F1*100:.4f}%")

# Original baseline (from raw at calibrated 0.70 / 0.40 / no overrides):
r_orig = metrics_at_threshold(test_recs, CANONICAL_DEFECT_CLASSES, 0.70, iou_thresh=0.40, per_class_conf_overrides=None)
orig_mAP50 = float(r_orig["macro"].get("mAP50", 0))
orig_P = float(r_orig["macro"].get("micro_precision", 0))
orig_R = float(r_orig["macro"].get("micro_recall", 0))
orig_F1 = float(r_orig["macro"].get("micro_f1", 0))
orig_mAP5095 = float(r_orig.get("map_50_95", {}).get("mAP50_95", 0))
print(f"\n--- DELTA vs original baseline (conf=0.70, IoU=0.40, no overrides) ---")
print(f"  baseline mAP50: {orig_mAP50*100:.2f}%   →  FINAL: {test_mAP50*100:.2f}%   Δ = {+(test_mAP50-orig_mAP50)*100:.2f}pp")
print(f"  baseline P:    {orig_P*100:.2f}%   →  FINAL: {test_P*100:.2f}%   Δ = {+(test_P-orig_P)*100:.2f}pp")
print(f"  baseline R:    {orig_R*100:.2f}%   →  FINAL: {test_R*100:.2f}%   Δ = {+(test_R-orig_R)*100:.2f}pp")
print(f"  baseline F1:   {orig_F1*100:.2f}%   →  FINAL: {test_F1*100:.2f}%   Δ = {+(test_F1-orig_F1)*100:.2f}pp")
print(f"  baseline mAP50-95: {orig_mAP5095*100:.2f}%   →  FINAL: {test_mAP5095*100:.2f}%   Δ = {+(test_mAP5095-orig_mAP5095)*100:.2f}pp")

# Per-class AP50
print(f"\nPer-class AP50 (LOCKED TEST):")
print(f"  {'class':12s} {'AP50 orig':>10s} {'AP50 new':>10s} {'Δ pp':>8s}  {'TP':>5s} {'FP':>5s} {'FN':>5s}")
for c in CANONICAL_DEFECT_CLASSES:
    orig_pc = r_orig["per_class"].get(c, {})
    new_pc = pc_t.get(c, {})
    oa = float(orig_pc.get("ap50", 0)) * 100
    na = float(new_pc.get("ap50", 0)) * 100
    tp = int(new_pc.get("tp", 0)); fp = int(new_pc.get("fp", 0)); fn = int(new_pc.get("fn", 0))
    print(f"  {c:12s} {oa:>10.2f} {na:>10.2f} {+(na-oa):>8.2f}  {tp:>5d} {fp:>5d} {fn:>5d}")

print(f"\n=== 96% mAP50 TARGET STATUS ===")
print(f"  baseline: {orig_mAP50*100:.2f}%  → FAIL")
print(f"  expanded sweep best: {test_mAP50*100:.2f}%  → {'PASS' if test_mAP50 >= 0.96 else 'FAIL'}  (need ≥96.00%)")
print(f"  remaining gap: {max(0, 0.96 - test_mAP50)*100:.2f}pp")

# Write machine-readable result
out = {
    "phase": "4d-expanded-sweep-from-raw",
    "best_val_selection": {
        "global_conf": gc_final,
        "match_iou": miou_final,
        "per_class_conf_overrides_raw": raw_offsets,
        "per_class_conf_overrides_effective": eff_overrides,
        "val_micro_F1": s[0],
        "val_mAP50": s[1],
        "val_micro_P": s[2],
        "val_micro_R": s[3],
    },
    "locked_test": {
        "mAP50": test_mAP50,
        "mAP50_95": test_mAP5095,
        "precision": test_P,
        "recall": test_R,
        "f1": test_F1,
        "per_class_AP50": {c: round(float(pc_t.get(c, {}).get("ap50", 0)), 6) for c in CANONICAL_DEFECT_CLASSES},
        "per_class_TP_FP_FN": {c: {
            "tp": int(pc_t.get(c, {}).get("tp", 0)),
            "fp": int(pc_t.get(c, {}).get("fp", 0)),
            "fn": int(pc_t.get(c, {}).get("fn", 0)),
        } for c in CANONICAL_DEFECT_CLASSES},
    },
    "baseline_comparison": {
        "baseline_mAP50": orig_mAP50,
        "baseline_P": orig_P,
        "baseline_R": orig_R,
        "baseline_F1": orig_F1,
        "baseline_mAP50_95": orig_mAP5095,
        "delta_mAP50_pp": round((test_mAP50 - orig_mAP50) * 100, 4),
        "delta_P_pp": round((test_P - orig_P) * 100, 4),
        "delta_R_pp": round((test_R - orig_R) * 100, 4),
        "delta_F1_pp": round((test_F1 - orig_F1) * 100, 4),
    },
    "target_mAP50_ge_96pct": "PASS" if test_mAP50 >= 0.96 else "FAIL",
    "remaining_gap_pp": round(max(0, 0.96 - test_mAP50) * 100, 4),
    "total_eval_time_s": round(time.time() - t0, 1),
    "protocol_note": "Deterministic --from-raw re-score on persisted detections; fresh inference/TTA+ensemble will be additive on top of this per-class conf optimization.",
}
out_path = os.path.join(ROOT, "metrics", "expanded_4d_sweep_result.json")
with open(out_path, "w") as f:
    json.dump(out, f, indent=2)
print(f"\nWrote: {out_path}")
print(f"  (This result can be COMBINED with TTA+ensemble gains.)")
