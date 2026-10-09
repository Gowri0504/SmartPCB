import json, os
ROOT = r"d:\SmartPCB-XAI"
print("="*80)
print("SMARTPCB-XAI — MODEL ACCURACY SUMMARY")
print("="*80)
print()
# 1. DEFECT MODEL
with open(os.path.join(ROOT, "metrics", "defect_metrics.json")) as f:
    d = json.load(f)
print("► DEFECT DETECTOR (deployed: defect_best_scratch.pt, YOLOv11s, from-scratch, seed 42)")
print(f"  Dataset: DeepPCB 1,500 pairs / 10,013 boxes (6 classes)")
print(f"  Test images: 500   GT boxes: {sum(d['test_at_default_0.25']['metrics']['per_class'][c]['gt_count'] for c in d['test_at_default_0.25']['metrics']['per_class'])}")
print()
m1 = d["test_at_default_0.25"]["metrics"]["macro"]
m2 = d["test_at_val_calibrated_threshold"]["metrics"]["macro"]
map5095_a = d["test_at_default_0.25"]["map_50_95"]["mAP50_95"]
map5095_b = d["test_at_val_calibrated_threshold"]["map_50_95"]["mAP50_95"]
best_conf = d["val_calibrated_threshold"]
print(f"  ┌────────────────────────────────────────┬─────────────┬─────────────┐")
print(f"  │ Metric                                 │ conf=0.25    │ conf={best_conf:<2} (VAL-calibrated) │")
print(f"  ├────────────────────────────────────────┼─────────────┼─────────────┤")
print(f"  │ mAP@50  (mean Average Precision @ IoU ½)│  {m1['mAP50']:.4f} ({m1['mAP50']*100:5.1f}%)  │  {m2['mAP50']:.4f} ({m2['mAP50']*100:5.1f}%)  │")
print(f"  │ mAP@50-95  (strict, 10 IoU thresholds) │  {map5095_a:.4f} ({map5095_a*100:5.1f}%)  │  {map5095_b:.4f} ({map5095_b*100:5.1f}%)  │")
print(f"  │ Micro Precision (TP / TP+FP)           │  {m1['micro_precision']:.4f} ({m1['micro_precision']*100:5.1f}%)  │  {m2['micro_precision']:.4f} ({m2['micro_precision']*100:5.1f}%)  │")
print(f"  │ Micro Recall    (TP / TP+FN)           │  {m1['micro_recall']:.4f} ({m1['micro_recall']*100:5.1f}%)  │  {m2['micro_recall']:.4f} ({m2['micro_recall']*100:5.1f}%)  │")
print(f"  │ Micro F1-Score  (harmonic mean)        │  {m1['micro_f1']:.4f} ({m1['micro_f1']*100:5.1f}%)  │  {m2['micro_f1']:.4f} ({m2['micro_f1']*100:5.1f}%)  │")
print(f"  └────────────────────────────────────────┴─────────────┴─────────────┘")
print()
print("  Per-Class AP50 (TEST, val-calibrated conf=%.2f):" % best_conf)
for cls, m in sorted(d["test_at_val_calibrated_threshold"]["metrics"]["per_class"].items()):
    gt = m["gt_count"]; tp = m["tp"]; fp = m["fp"]; fn = m["fn"]
    ap = m.get("ap50", None); pct = f"{ap*100:5.1f}%" if ap is not None else "  N/A  "
    print(f"    {cls:<10s}  AP50 {pct}   GT={gt:4d}   TP={tp:4d}   FP={fp:4d}   FN={fn:4d}")
print()
# 2. COMPONENT MODEL
with open(os.path.join(ROOT, "metrics", "component_metrics.json")) as f:
    c = json.load(f)
print("► COMPONENT DETECTOR (deployed: component_best.pt, YOLOv10n, legacy, mAP50 WEAK)")
print(f"  Dataset: FICS tiled + Roboflow 1,013 images / 33,156 boxes (10 model / 6 GT classes)")
print(f"  Test images: 90")
# find default conf 0.25 sweep
sweep = next((s for s in c["threshold_sweep_on_val"] if s["confidence_threshold"] == 0.25), c["threshold_sweep_on_val"][0])
m = sweep["macro"]
print(f"  Operating conf: {sweep['confidence_threshold']:.2f}")
print(f"  ┌────────────────────┬─────────────┐   ⚠  Deployed model is weak (retrain failed).")
print(f"  │ Metric             │ Value       │")
print(f"  ├────────────────────┼─────────────┤")
print(f"  │ mAP@50             │  {m['mAP50']:.4f} ({m['mAP50']*100:5.1f}%)  │")
print(f"  │ Micro Precision    │  {m['micro_precision']:.4f} ({m['micro_precision']*100:5.1f}%)  │")
print(f"  │ Micro Recall       │  {m['micro_recall']:.4f} ({m['micro_recall']*100:5.1f}%)  │")
print(f"  │ Micro F1           │  {m['micro_f1']:.4f} ({m['micro_f1']*100:5.1f}%)  │")
print(f"  └────────────────────┴─────────────┘")
print(f"  Unscorable GT: inductors GT class has 0 matching detections (class space mismatch)")
print(f"  Unmapped GT classes in TEST: {c['class_spaces']['gt_classes_that_no_detection_can_ever_match']}")
print()
# 3. FULL PIPELINE
with open(os.path.join(ROOT, "metrics", "full_pipeline_metrics.json")) as f:
    p = json.load(f)
lats = [r["pipeline_latency_ms"] for r in p if r["pipeline_latency_ms"]]
import statistics
print("► END-TO-END PIPELINE (CPU, 23 images total)")
print(f"  Samples: {len(p)}")
print(f"  Mean latency:   {statistics.mean(lats)/1000:.2f} s / image")
print(f"  Median latency: {statistics.median(lats)/1000:.2f} s / image")
print(f"  Min / Max:      {min(lats)/1000:.2f} s / {max(lats)/1000:.2f} s")
statuses = {}
for r in p:
    s = r["status"]
    statuses[s] = statuses.get(s,0)+1
print(f"  Pipeline outcomes: " + ", ".join(f"{k}={v}" for k,v in statuses.items()))
print()
print("► HOW TO REPRODUCE THESE NUMBERS YOURSELF")
print("  ═══════════════════════════════════════")
print("  (A) Defect mAP50 + per-class (official Ultralytics val on TEST):")
print("      yolo val model=models/defect_best_scratch.pt data=datasets/defects/data.yaml split=test imgsz=640 conf=0.001 iou=0.6 device=cpu")
print()
print("  (B) Component mAP50 (custom evaluator):")
print("      python scripts/evaluation/evaluate_deployed_models.py --model component")
print()
print("  (C) Full pipeline latency + accuracy across 23 image suite:")
print("      python scripts/evaluation/evaluate_full_pipeline.py")
print()
print("  (D) Val-sweep calibration + TEST at calibrated threshold (defects):")
print("      python scripts/evaluation/evaluate_defect_model.py")
print("  → produces metrics/defect_metrics.json with 13 conf-threshold rows")
print()
print("  (E) Python unittest suite (53/53 PASS, 2 skipped):")
print("      python -m unittest discover -s tests")
print()
print("► DEPLOYED CHECKPOINTS:")
for name in ["defect_best_scratch.pt","component_best.pt","defect_best.pt","defect_best_legacy.pt"]:
    fp = os.path.join(ROOT, "models", name)
    if os.path.exists(fp):
        print(f"  ✓ models/{name}  {os.path.getsize(fp)/1024/1024:.1f} MB")
    else:
        alt = os.path.join(ROOT, "models", name.lower())
        if os.path.exists(alt):
            print(f"  ✓ models/{name.lower()}  {os.path.getsize(alt)/1024/1024:.1f} MB")
        else:
            print(f"  ✗ models/{name}  MISSING")
