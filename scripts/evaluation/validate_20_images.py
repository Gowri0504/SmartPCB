"""
STEP 16 — 20-image held-out validation through the full engine pipeline.

Runs SmartPCBInspectionEngine.inspect() on 20 real images drawn from the
official DeepPCB test split (datasets/defects/test/images) and persists:
  results/final_20_image_validation.csv   — one row per image
  results/final_20_image_validation.json  — full per-image payloads
  results/annotated/NNNN_annotated.jpg    — composite annotated renders

Every number in the outputs comes from an actual engine run on this machine
(CPU, torch 2.13.0+cpu). Nothing is estimated or copied from training logs.

Usage: python scripts/evaluation/validate_20_images.py [--n 20]
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

RESULTS_DIR = ROOT / "results"
ANNOTATED_DIR = RESULTS_DIR / "annotated"
TEST_IMG_DIR = ROOT / "datasets" / "defects" / "test" / "images"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--conf", type=float, default=0.25)
    args = ap.parse_args()

    ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)

    images = sorted(TEST_IMG_DIR.glob("*.jpg"))[: args.n]
    if len(images) < args.n:
        raise SystemExit(f"Only {len(images)} test images available, need {args.n}")

    from ai.inference.engine import SmartPCBInspectionEngine

    engine = SmartPCBInspectionEngine()

    rows = []
    payloads = []
    for img_path in images:
        result = engine.inspect(
            image_input=str(img_path),
            conf_threshold=args.conf,
            generate_xai=True,
        )

        annotated = result.pop("annotated_image", None)
        xai_overlay = result.pop("xai_overlay_image", None)

        stem = img_path.stem
        annotated_path = ""
        if annotated is not None:
            import cv2

            out = ANNOTATED_DIR / f"{stem}_annotated.jpg"
            cv2.imwrite(str(out), annotated)
            annotated_path = str(out.relative_to(ROOT))

        defect_classes = [d["class"] for d in result.get("defects", [])]
        comp_classes = [c["class"] for c in result.get("components", [])]
        timing = result.get("inference_timing_ms", {})

        rows.append({
            "image": img_path.name,
            "inspection_status": result.get("inspection_status"),
            "component_count": result.get("component_count"),
            "defect_count": result.get("defect_count"),
            "defect_classes": ";".join(defect_classes),
            "component_classes": ";".join(comp_classes),
            "quality_overall_score": (result.get("quality_score") or {}).get("overall_score"),
            "xai_explained_class": (result.get("xai") or {}).get("explained_class"),
            "suspicious_zero_detection": result.get("suspicious_zero_detection"),
            "review_required": result.get("review_required"),
            "preprocess_ms": timing.get("preprocess_ms"),
            "component_inference_ms": timing.get("component_inference_ms"),
            "defect_inference_ms": timing.get("defect_inference_ms"),
            "xai_ms": timing.get("xai_ms"),
            "postprocess_ms": timing.get("postprocess_ms"),
            "total_ms": result.get("inference_time_ms"),
            "annotated_image": annotated_path,
        })

        result["source_image"] = img_path.name
        result["annotated_image_path"] = annotated_path
        payloads.append(result)
        print(f"[validate] {img_path.name}: comps={result.get('component_count')} "
              f"defs={result.get('defect_count')} total={result.get('inference_time_ms')}ms")

    csv_path = RESULTS_DIR / "final_20_image_validation.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path = RESULTS_DIR / "final_20_image_validation.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": __import__("datetime").datetime.now().isoformat(),
            "n_images": len(rows),
            "conf_threshold": args.conf,
            "device": engine.device,
            "component_model_path": engine.component_model_path,
            "defect_model_path": engine.defect_model_path,
            "images": payloads,
        }, f, indent=2, default=str)

    n_review = sum(1 for r in rows if r["review_required"])
    n_zero = sum(1 for r in rows if r["suspicious_zero_detection"])
    print(f"\n[validate] {len(rows)} images -> {csv_path}")
    print(f"[validate] review_required={n_review} suspicious_zero={n_zero}")
    print(f"[validate] JSON -> {json_path}")


if __name__ == "__main__":
    main()
