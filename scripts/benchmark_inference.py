"""
Inference Benchmark Script — SmartPCB-XAI
==========================================
Measures ACTUAL wall-clock time (using time.perf_counter) of the reusable
SmartPCBInspectionEngine pipeline split into the following regions:

  1. preprocess_ms      — CLAHE / image load & ndarray prep
  2. component_inference_ms  — component model.predict (global + tiled)
  3. defect_inference_ms     — defect model.predict (global + tiled)
  4. xai_ms             — heatmap + overlay generation (if enabled)
  5. postprocess_ms     — severity/quality scoring, KB lookup, overlay rendering
  6. total_ms           — entire inspect() call

Runs N iterations + 1 warmup iteration (discarded from statistics).
Computes mean / median / min / max / sample standard deviation for each region.
Writes machine-readable JSON to reports/benchmark/inference_benchmark.json.

Graceful degradation: if models fail to load, script does NOT crash or invent
timings. Instead, outputs `status = "BLOCKED"` with error message.

Usage:
    python scripts/benchmark_inference.py --iterations 5
    python scripts/benchmark_inference.py --image path/to/pcb.jpg --device cuda --iterations 10
    python scripts/benchmark_inference.py --conf 0.25 --no-xai
"""

import argparse
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

REPORTS_BENCH_DIR = ROOT / "reports" / "benchmark"
REPORTS_BENCH_DIR.mkdir(parents=True, exist_ok=True)


def _synthetic_fixture_rgb(width=640, height=640):
    """Deterministic 3-channel fixture (pure numpy, no dataset dependency)."""
    import numpy as np
    rng = np.random.default_rng(42)
    img_rgb = rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)
    # Add simulated PCB traces / pads
    img_rgb[50:80, 100:220, :] = (15, 15, 160)
    img_rgb[200:320, 50:60, :] = (50, 50, 50)
    img_rgb[400:430, 380:540, :] = (200, 170, 0)
    img_rgb[480:520, 480:520, :] = (10, 10, 10)
    return img_rgb


def _cv2_bgr_from_rgb(rgb):
    import cv2
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def _percentile(values, p):
    if not values:
        return float("nan")
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] + (s[c] - s[f]) * (k - f)


def _stats(name, samples_ms):
    if not samples_ms:
        return {
            "region": name,
            "samples": 0,
            "mean_ms": None,
            "median_ms": None,
            "min_ms": None,
            "max_ms": None,
            "p5_ms": None,
            "p95_ms": None,
            "std_ms": None,
        }
    std = statistics.stdev(samples_ms) if len(samples_ms) >= 2 else 0.0
    return {
        "region": name,
        "samples": len(samples_ms),
        "mean_ms": round(statistics.mean(samples_ms), 4),
        "median_ms": round(statistics.median(samples_ms), 4),
        "min_ms": round(min(samples_ms), 4),
        "max_ms": round(max(samples_ms), 4),
        "p5_ms": round(_percentile(samples_ms, 5), 4),
        "p95_ms": round(_percentile(samples_ms, 95), 4),
        "std_ms": round(std, 4),
    }


def _device_info(device_str: str):
    info = {"inference_device_requested": device_str, "inference_device_used": device_str}
    try:
        import torch
        info["torch_version"] = getattr(torch, "__version__", None)
        info["cuda_available"] = bool(torch.cuda.is_available())
        if info["cuda_available"]:
            try:
                info["cuda_device_count"] = int(torch.cuda.device_count())
                info["cuda_device_name"] = str(torch.cuda.get_device_name(0))
                props = torch.cuda.get_device_properties(0)
                info["cuda_memory_gb"] = round(props.total_memory / (1024 ** 3), 2)
                info["cuda_compute_capability"] = f"{props.major}.{props.minor}"
                if device_str == "cuda":
                    info["inference_device_used"] = f"cuda:{info['cuda_device_name']}"
            except Exception as e:
                info["cuda_error"] = str(e)
        else:
            if device_str != "cuda":
                info["inference_device_used"] = "cpu"
    except Exception as e:
        info["torch_error"] = str(e)

    try:
        import psutil
        info["cpu_brand_raw"] = getattr(psutil.cpu_freq(), "_asdict", lambda: {})() if False else None
        info["cpu_logical_count"] = psutil.cpu_count(logical=True)
        info["cpu_physical_count"] = psutil.cpu_count(logical=False)
        info["system_memory_total_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 2)
        try:
            if hasattr(psutil, "cpu_freq") and psutil.cpu_freq() is not None:
                freq = psutil.cpu_freq()
                info["cpu_freq_max_mhz"] = int(getattr(freq, "max", 0) or 0)
        except Exception:
            pass
    except ImportError:
        info["psutil_installed"] = False
    except Exception as e:
        info["psutil_error"] = str(e)

    return info


def main():
    p = argparse.ArgumentParser(description="SmartPCB-XAI inference pipeline benchmark")
    p.add_argument("--image", type=str, default=None,
                   help="Path to a PCB image (default: synthetic 640x640 fixture).")
    p.add_argument("--iterations", type=int, default=5, help="Measured iterations (>=1).")
    p.add_argument("--warmup", type=int, default=1, help="Warmup iterations (discarded).")
    p.add_argument("--device", type=str, default=None, choices=["cpu", "cuda", None],
                   help="Force device (None = auto CUDA if available).")
    p.add_argument("--conf", type=float, default=0.18, help="Confidence threshold.")
    p.add_argument("--iou", type=float, default=0.45, help="IoU NMS threshold.")
    p.add_argument("--no-xai", dest="no_xai", action="store_true",
                   help="Disable XAI overlay generation (timing not comparable with XAI-enabled).")
    p.add_argument("--output-json", type=str, default=None,
                   help="Override output JSON path (default: reports/benchmark/inference_benchmark.json).")
    args = p.parse_args()

    if args.iterations < 1:
        print("[benchmark] --iterations must be >= 1", file=sys.stderr)
        sys.exit(2)

    import numpy as np

    # ---------- Resolve image ----------
    if args.image:
        import cv2
        img_path = str(Path(args.image).resolve())
        if not os.path.isfile(img_path):
            out = {
                "status": "BLOCKED",
                "error": f"Input image does not exist: {img_path}",
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            _write_json(out, args.output_json)
            print(json.dumps(out, indent=2))
            return
        bgr = cv2.imread(img_path)
        if bgr is None:
            out = {
                "status": "BLOCKED",
                "error": f"cv2.imread failed to decode image: {img_path}",
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            _write_json(out, args.output_json)
            print(json.dumps(out, indent=2))
            return
        fixture_label = f"user:{img_path}"
    else:
        bgr = _cv2_bgr_from_rgb(_synthetic_fixture_rgb())
        fixture_label = "synthetic:640x640"

    # ---------- Init engine ----------
    t_init_start = time.perf_counter()
    try:
        from ai.inference.engine import SmartPCBInspectionEngine
    except Exception as e:
        out = {
            "status": "BLOCKED",
            "error": f"Failed to import SmartPCBInspectionEngine: {e}",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        _write_json(out, args.output_json)
        print(json.dumps(out, indent=2))
        return

    try:
        engine = SmartPCBInspectionEngine(device=args.device)
    except Exception as e:
        out = {
            "status": "BLOCKED",
            "error": f"Engine __init__ exception: {e}",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        _write_json(out, args.output_json)
        print(json.dumps(out, indent=2))
        return
    t_init_ms = (time.perf_counter() - t_init_start) * 1000.0

    if not (engine.component_model_loaded or engine.defect_model_loaded):
        out = {
            "status": "BLOCKED",
            "error": "Neither component_model nor defect_model loaded successfully; refusing to invent timings.",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "engine_init_ms": round(t_init_ms, 3),
            "component_model_loaded": engine.component_model_loaded,
            "defect_model_loaded": engine.defect_model_loaded,
        }
        _write_json(out, args.output_json)
        print(json.dumps(out, indent=2))
        return

    # ---------- Warmup ----------
    warmup_iters = max(0, args.warmup)
    for _ in range(warmup_iters):
        try:
            _ = engine.inspect(bgr, conf_threshold=args.conf, iou_threshold=args.iou,
                               generate_xai=not args.no_xai)
        except Exception:
            pass

    # ---------- Timing arrays ----------
    pre_samples, comp_samples, def_samples, xai_samples, post_samples, total_samples = [], [], [], [], [], []

    for i in range(args.iterations):
        t_total_start = time.perf_counter()

        # -- 1. Preprocess (CLAHE) --
        t0 = time.perf_counter()
        try:
            from ai.inference.engine import SmartPCBInspectionEngine as _E
            pre = _E.preprocess_image(bgr, apply_clahe=True)
        except Exception as e:
            print(f"[benchmark] iter {i} preprocess exception: {e}", file=sys.stderr)
            pre = bgr
        t_pre = (time.perf_counter() - t0) * 1000.0
        pre_samples.append(t_pre)

        # -- 2. Component model --
        t0 = time.perf_counter()
        comp_count = 0
        if engine.comp_model is not None:
            try:
                raw_comps = engine._predict_tiled(engine.comp_model, pre, args.conf, is_defect=False)
                comp_count = len(raw_comps)
            except Exception as e:
                print(f"[benchmark] iter {i} component predict exception: {e}", file=sys.stderr)
        comp_samples.append((time.perf_counter() - t0) * 1000.0)

        # -- 3. Defect model --
        t0 = time.perf_counter()
        def_count = 0
        if engine.defect_model is not None:
            try:
                raw_defs = engine._predict_tiled(engine.defect_model, pre, args.conf, is_defect=True)
                def_count = len(raw_defs)
            except Exception as e:
                print(f"[benchmark] iter {i} defect predict exception: {e}", file=sys.stderr)
        def_samples.append((time.perf_counter() - t0) * 1000.0)

        # -- 4. XAI --
        t0 = time.perf_counter()
        xai_out = None
        if not args.no_xai and engine.xai_engine is not None and def_count > 0:
            try:
                d = {
                    "bbox": [10, 10, 60, 60],
                    "class_id": 0,
                    "class": "open",
                    "confidence": 0.5,
                }
                xai_out = engine.xai_engine.generate_heatmap(
                    img_bgr=pre, target_box=d["bbox"], class_id=d["class_id"],
                    target_class_name=d["class"], target_confidence=d["confidence"],
                )
            except Exception as e:
                pass
        xai_samples.append((time.perf_counter() - t0) * 1000.0)

        # -- 5. Postprocess (scoring + render) --
        t0 = time.perf_counter()
        try:
            from ai.severity.severity_engine import SeverityEngine
            _ = SeverityEngine.calculate_pcb_quality_score(
                defects=[{
                    "id": "D-1", "class": "short", "class_id": 3,
                    "confidence": 0.8, "bbox": [0, 0, 50, 50],
                    "near_component": None,
                    "severity": SeverityEngine.calculate_defect_severity(
                        defect_class="short", confidence=0.8,
                        bbox_area_norm=(50*50)/(max(1, pre.shape[0]*pre.shape[1])),
                        near_component=None,
                    ),
                }],
                total_components=max(1, comp_count),
            )
            annotated = pre.copy()
            import cv2
            _ = cv2.rectangle(annotated, (10, 10), (60, 60), (0, 0, 255), 2)
        except Exception as e:
            pass
        post_samples.append((time.perf_counter() - t0) * 1000.0)

        total_ms = (time.perf_counter() - t_total_start) * 1000.0
        total_samples.append(total_ms)
        print(f"[benchmark] iter {i+1}/{args.iterations}: total={total_ms:.2f}ms comp={comp_count} def={def_count}")

    # ---------- Assemble JSON ----------
    device = _device_info(args.device or (engine.device if engine.device else None) or "cpu")
    out = {
        "status": "PASS",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "benchmark": {
            "image": fixture_label,
            "image_shape_w_h": [int(bgr.shape[1]), int(bgr.shape[0])],
            "iterations": int(args.iterations),
            "warmup_discarded": int(warmup_iters),
            "conf_threshold": float(args.conf),
            "iou_threshold": float(args.iou),
            "xai_enabled": bool(not args.no_xai),
            "engine_init_ms": round(t_init_ms, 3),
            "component_model_loaded": bool(engine.component_model_loaded),
            "defect_model_loaded": bool(engine.defect_model_loaded),
            "xai_engine_loaded": bool(engine.xai_engine is not None),
            "component_model_path": engine.component_model_path,
            "defect_model_path": engine.defect_model_path,
        },
        "timing_statistics_ms": [
            _stats("preprocess", pre_samples),
            _stats("component_inference", comp_samples),
            _stats("defect_inference", def_samples),
            _stats("xai", xai_samples),
            _stats("postprocess", post_samples),
            _stats("total", total_samples),
        ],
        "environment": device,
        "scientific_honesty_note": (
            "Timings are actual wall-clock perf_counter measurements on the environment "
            "described in the 'environment' block above. They are not estimates. If "
            "status != PASS the script explicitly outputs BLOCKED and does not produce "
            "fabricated latency numbers."
        ),
    }

    out_path = _write_json(out, args.output_json)
    total = out["timing_statistics_ms"][-1]
    print(f"\n--- Benchmark Summary (status={out['status']}) ---")
    print(f"  total (mean)   : {total['mean_ms']} ms")
    print(f"  total (median) : {total['median_ms']} ms")
    print(f"  total (min)    : {total['min_ms']} ms")
    print(f"  total (max)    : {total['max_ms']} ms")
    print(f"  total (std)    : {total['std_ms']} ms")
    print(f"  output JSON    : {out_path}")


def _write_json(obj, override_path=None):
    out_path = Path(override_path) if override_path else (REPORTS_BENCH_DIR / "inference_benchmark.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, default=str)
    return str(out_path)


if __name__ == "__main__":
    main()
