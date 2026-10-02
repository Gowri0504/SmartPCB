import hashlib
import os
import time
import cv2
import torch
import numpy as np
from datetime import datetime
from PIL import Image
from ultralytics import YOLO

from ai.config import (
    CANONICAL_COMPONENT_CLASSES,
    CANONICAL_DEFECT_CLASSES,
    PROJECT_VERSION,
    normalize_component_class,
    normalize_defect_class,
)
from ai.severity.severity_engine import SeverityEngine
from ai.recommendation.repair_kb import RepairKnowledgeBase
from ai.xai.gradcam import YOLOGradCAM

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODELS_DIR = os.path.join(ROOT, "models")

CONTRACT_VERSION = "1.0"


def build_error_result(warnings=None, image_id=None, inspection_id=None):
    """
    Contract-shaped failure payload (state (c) of the zero-detection safety rule).

    Every transport uses this so a failed inspection can never be rendered as a
    clean board: components/defects are empty, quality_score is None.
    """
    now = datetime.now()
    return {
        "contract_version": CONTRACT_VERSION,
        "inspection_status": "ERROR",
        "inspection_id": inspection_id or f"INSP-ERR-{int(now.timestamp())}",
        "image_id": image_id or "",
        "timestamp": now.isoformat(),
        "image_dimensions": {"width": 0, "height": 0},
        "components": [],
        "component_count": 0,
        "defects": [],
        "defect_count": 0,
        "quality_score": None,
        "xai": {},
        "severity": [],
        "recommendations": [],
        "pipeline_warnings": list(warnings or []),
        "suspicious_zero_detection": False,
        "review_required": False,
        "models_available": False,
        "model_version": None,
        "inference_time_ms": 0,
        "inference_timing_ms": {},
    }


def _normalize_class_name(model_names_dict, class_id, is_defect):
    """
    Resolve a raw model class id to (canonical_name, is_mapped, raw_name).

    Never coerces a class into an unrelated canonical class: unknown labels are
    returned verbatim with is_mapped=False (see COMPONENT_CLASS_SCHEMA.md).
    """
    direct = None
    if isinstance(model_names_dict, dict):
        direct = model_names_dict.get(class_id)
    elif isinstance(model_names_dict, (list, tuple)) and 0 <= class_id < len(model_names_dict):
        direct = model_names_dict[class_id]
    if direct is None:
        direct = f"item_{class_id}"

    if is_defect:
        # Index decoding takes precedence: the deployed defect checkpoint's
        # name strings belong to a different taxonomy than its indices
        # (positional alignment, verified 2026-09-23 — see ai/config.py).
        return normalize_defect_class(direct, class_id=class_id)
    return normalize_component_class(direct)


class SmartPCBInspectionEngine:
    """
    Unified Industry 4.0 PCB Inspection Engine with:
    1. Multi-Scale & Tiled Sliding-Window Inference (for ultra-high-res PCBs)
    2. Dual-Head YOLOv11 Object Detectors (Components & Defects)
    3. Spatial Detection Fusion & Non-Maximum Suppression (NMS)
    4. Activation-Energy XAI Approximation (see ai/xai/gradcam.py; Part 2 target: true Grad-CAM++)
    5. Deterministic project-defined defect Severity & PCB Quality Scoring
    6. Prescriptive rule-based Repair Knowledge Base (IPC-A-610 as guidance only)
    """

    def __init__(self, component_model_path=None, defect_model_path=None, device=None):
        if component_model_path is None:
            cand = os.path.join(MODELS_DIR, "component_best.pt")
            component_model_path = cand if os.path.exists(cand) else "yolo11n.pt"

        if defect_model_path is None:
            cand = os.path.join(MODELS_DIR, "defect_best.pt")
            defect_model_path = cand if os.path.exists(cand) else "yolo11n.pt"

        # Graceful device selection: use CUDA if available AND explicitly requested/detected; else CPU.
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cuda" and not torch.cuda.is_available():
            device = "cpu"
        self.device = device

        self.component_model_path = component_model_path
        self.defect_model_path = defect_model_path

        print(f"[Engine] device: {device}")
        print(f"Loading Component Detector: {component_model_path}")
        try:
            self.comp_model = YOLO(component_model_path)
            self.component_model_loaded = True
        except Exception as e:
            print(f"WARNING: Component model failed to load, fallback skipped. {e}")
            self.comp_model = None
            self.component_model_loaded = False

        print(f"Loading Defect Detector: {defect_model_path}")
        try:
            self.defect_model = YOLO(defect_model_path)
            self.defect_model_loaded = True
        except Exception as e:
            print(f"WARNING: Defect model failed to load, fallback skipped. {e}")
            self.defect_model = None
            self.defect_model_loaded = False

        try:
            self.xai_engine = YOLOGradCAM(self.defect_model) if self.defect_model_loaded else None
        except Exception as e:
            print(f"Warning: XAI engine init deferred: {e}")
            self.xai_engine = None

    @staticmethod
    def preprocess_image(img_bgr, apply_clahe=True):
        if not apply_clahe:
            return img_bgr
        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        enhanced = cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)
        return enhanced

    @staticmethod
    def apply_nms(boxes_list, iou_thresh=0.45):
        """
        Applies Non-Maximum Suppression across list of dict boxes:
        [{'bbox': [x1, y1, x2, y2], 'confidence': conf, 'class': cls, ...}]
        """
        if not boxes_list:
            return []

        boxes = np.array([b['bbox'] for b in boxes_list], dtype=np.float32)
        scores = np.array([b['confidence'] for b in boxes_list], dtype=np.float32)

        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]

        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)

            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h

            ovr = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
            inds = np.where(ovr <= iou_thresh)[0]
            order = order[inds + 1]

        return [boxes_list[k] for k in keep]

    def _predict_tiled(self, model, img_bgr, conf_thresh, is_defect=False):
        """
        Performs multi-scale sliding-window inference optimized for tiny object detection.
        
        Uses high-resolution tiled inference with significant overlap to handle
        the 94.2% tiny objects in the component dataset.
        """
        orig_h, orig_w = img_bgr.shape[:2]
        all_detections = []

        # For components, use higher resolution due to tiny objects
        # For defects, standard resolution is sufficient
        if is_defect:
            tile_size = 640
            stride = 480  # 25% overlap
            downscale_max = 1920
        else:
            # Components: Use higher resolution for tiny objects
            tile_size = 960  # Increased from 640
            stride = 640    # 33% overlap for better edge coverage
            downscale_max = 2560  # Allow higher resolution for components

        # Downscale ultra-high-resolution boards for CPU performance
        scale = 1.0
        proc_img = img_bgr
        if max(orig_h, orig_w) > downscale_max:
            scale = downscale_max / float(max(orig_h, orig_w))
            proc_w = int(orig_w * scale)
            proc_h = int(orig_h * scale)
            proc_img = cv2.resize(img_bgr, (proc_w, proc_h), interpolation=cv2.INTER_AREA)
        else:
            proc_w, proc_h = orig_w, orig_h

        # 1. Global forward pass (always run to catch large structures)
        try:
            global_res = model.predict(source=proc_img, conf=conf_thresh, verbose=False, device=self.device)
        except Exception:
            # Graceful fallback if CUDA tensors failed: retry on CPU
            global_res = model.predict(source=proc_img, conf=conf_thresh, verbose=False, device="cpu")
        for r in global_res:
            for i in range(len(r.boxes)):
                xyxy = r.boxes.xyxy[i].cpu().numpy().tolist()
                conf = float(r.boxes.conf[i].cpu().numpy())
                cls_id = int(r.boxes.cls[i].cpu().numpy())
                cls_name, cls_mapped, cls_raw = _normalize_class_name(r.names, cls_id, is_defect)
                all_detections.append({
                    "class": cls_name,
                    "class_id": cls_id,
                    "class_mapped": cls_mapped,
                    "raw_class": cls_raw,
                    "confidence": round(conf, 4),
                    "bbox": [
                        round(xyxy[0] / scale, 1),
                        round(xyxy[1] / scale, 1),
                        round(xyxy[2] / scale, 1),
                        round(xyxy[3] / scale, 1)
                    ]
                })

        # 2. Tiled inference for all images to catch small objects
        # Use the same tile size for all images to ensure consistency
        if proc_w > tile_size or proc_h > tile_size:
            x_steps = list(range(0, proc_w - tile_size + 1, stride))
            if not x_steps or x_steps[-1] < proc_w - tile_size:
                x_steps.append(max(0, proc_w - tile_size))

            y_steps = list(range(0, proc_h - tile_size + 1, stride))
            if not y_steps or y_steps[-1] < proc_h - tile_size:
                y_steps.append(max(0, proc_h - tile_size))

            for ty in y_steps:
                for tx in x_steps:
                    tile = proc_img[ty:ty+tile_size, tx:tx+tile_size]
                    if tile.shape[0] < 50 or tile.shape[1] < 50:
                        continue

                    tile_res = model.predict(source=tile, conf=conf_thresh, verbose=False, device="cpu")
                    for r in tile_res:
                        for i in range(len(r.boxes)):
                            bx = r.boxes.xyxy[i].cpu().numpy().tolist()
                            conf = float(r.boxes.conf[i].cpu().numpy())
                            cls_id = int(r.boxes.cls[i].cpu().numpy())
                            cls_name, cls_mapped, cls_raw = _normalize_class_name(r.names, cls_id, is_defect)

                            # Remap tile coordinates back to global canvas and invert downscale
                            gx1 = (bx[0] + tx) / scale
                            gy1 = (bx[1] + ty) / scale
                            gx2 = (bx[2] + tx) / scale
                            gy2 = (bx[3] + ty) / scale

                            all_detections.append({
                                "class": cls_name,
                                "class_id": cls_id,
                                "class_mapped": cls_mapped,
                                "raw_class": cls_raw,
                                "confidence": round(conf, 4),
                                "bbox": [round(gx1, 1), round(gy1, 1), round(gx2, 1), round(gy2, 1)]
                            })

        # 3. Suppress overlapping detections using NMS
        cleaned = self.apply_nms(all_detections, iou_thresh=0.45)
        return cleaned

    def inspect(self, image_input, conf_threshold=0.18, iou_threshold=0.45, generate_xai=True):
        _t_total_start = time.perf_counter()
        timestamp = datetime.now().isoformat()
        inspection_id = f"INSP-{int(datetime.now().timestamp())}"

        if isinstance(image_input, str):
            img_bgr = cv2.imread(image_input)
            img_path = image_input
        else:
            img_bgr = image_input
            img_path = "memory_buffer.jpg"

        if img_bgr is None:
            raise ValueError(f"Failed to read image from input: {image_input}")

        orig_h, orig_w = img_bgr.shape[:2]

        # --- Preprocessing timing ---
        _t_pre_start = time.perf_counter()
        _ = SmartPCBInspectionEngine.preprocess_image(img_bgr, apply_clahe=True)
        _preprocess_ms = (time.perf_counter() - _t_pre_start) * 1000.0

        # 1. Multi-Scale Component Detection
        _t_comp_start = time.perf_counter()
        actual_comp_thresh = max(0.12, min(0.60, conf_threshold))
        if self.comp_model is None:
            raw_components = []
            pipeline_warnings_pre = ["Component model not loaded; skipping component detection."]
        else:
            pipeline_warnings_pre = []
            raw_components = self._predict_tiled(self.comp_model, img_bgr, actual_comp_thresh, is_defect=False)
        _component_inference_ms = (time.perf_counter() - _t_comp_start) * 1000.0

        detected_components = []
        for idx, c in enumerate(raw_components, 1):
            xyxy = c["bbox"]
            detected_components.append({
                "id": f"C-{idx}",
                "class": c["class"],
                "class_id": c["class_id"],
                "class_mapped": c.get("class_mapped", True),
                "raw_class": c.get("raw_class", c["class"]),
                "confidence": c["confidence"],
                "bbox": xyxy,
                "center": [round((xyxy[0] + xyxy[2]) / 2.0, 1), round((xyxy[1] + xyxy[3]) / 2.0, 1)]
            })

        # 2. Multi-Scale Defect Detection
        _t_def_start = time.perf_counter()
        actual_defect_thresh = max(0.12, min(0.60, conf_threshold))
        if self.defect_model is None:
            raw_defects = []
            pipeline_warnings_pre_defect = ["Defect model not loaded; skipping defect detection."]
        else:
            pipeline_warnings_pre_defect = []
            raw_defects = self._predict_tiled(self.defect_model, img_bgr, actual_defect_thresh, is_defect=True)
        _defect_inference_ms = (time.perf_counter() - _t_def_start) * 1000.0

        # Postprocess region: defect assembly, severity scoring, KB recommendations,
        # annotated rendering, zero-detection status logic. Bracketed as one window
        # MINUS the XAI window measured inside it, so the five bucket rows stay
        # disjoint and sum to ~total_ms instead of leaving render/scoring time
        # accounted only in the total.
        _t_post_start = time.perf_counter()

        detected_defects = []
        for idx, d in enumerate(raw_defects, 1):
            xyxy = d["bbox"]
            dx1, dy1, dx2, dy2 = xyxy
            d_area = (dx2 - dx1) * (dy2 - dy1) / max(1.0, (orig_w * orig_h))
            near_comp = None

            # Spatial association with nearest component
            for c in detected_components:
                cx1, cy1, cx2, cy2 = c["bbox"]
                if (dx1 - 40 <= cx2 and dx2 + 40 >= cx1 and dy1 - 40 <= cy2 and dy2 + 40 >= cy1):
                    near_comp = c["class"]
                    break

            severity = SeverityEngine.calculate_defect_severity(
                defect_class=d["class"],
                confidence=d["confidence"],
                bbox_area_norm=d_area,
                near_component=near_comp
            )

            detected_defects.append({
                "id": f"D-{idx}",
                "class": d["class"],
                "class_id": d["class_id"],
                "class_mapped": d.get("class_mapped", True),
                "raw_class": d.get("raw_class", d["class"]),
                "confidence": d["confidence"],
                "bbox": xyxy,
                "near_component": near_comp,
                "severity": severity
            })

        # 4. Overall PCB Quality Score Calculation
        quality_score = SeverityEngine.calculate_pcb_quality_score(
            defects=detected_defects,
            total_components=len(detected_components)
        )

        # 5. Prescriptive Repair Recommendations
        recommendations = []
        seen_classes = set()
        for d in detected_defects:
            c_name = d["class"]
            if c_name not in seen_classes:
                seen_classes.add(c_name)
                rec = RepairKnowledgeBase.get_recommendation(c_name)
                recommendations.append(rec)

        # 6. Render Composite Annotated Image
        annotated_bgr = img_bgr.copy()
        
        # Draw components (soft blue boxes)
        for c in detected_components:
            bx1, by1, bx2, by2 = map(int, c["bbox"])
            cv2.rectangle(annotated_bgr, (bx1, by1), (bx2, by2), (235, 99, 37), 2)
            cv2.putText(annotated_bgr, f"{c['class']} {c['confidence']:.2f}",
                        (bx1, max(14, by1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (235, 99, 37), 2)

        # Draw defects (prominent colored boxes with severity badges)
        for d in detected_defects:
            bx1, by1, bx2, by2 = map(int, d["bbox"])
            sev = d["severity"]
            box_color = (38, 38, 220) if sev["level"] == "CRITICAL" else (14, 88, 234)
            cv2.rectangle(annotated_bgr, (bx1, by1), (bx2, by2), box_color, 3)
            cv2.putText(annotated_bgr, f"{d['class'].upper()} [{sev['level']}] {d['confidence']:.2f}",
                        (bx1, max(16, by1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

        # 7. XAI Visual Attribution (honestly labeled approximation)
        xai_data = {}
        xai_overlay_bgr = None
        _t_xai_start = time.perf_counter()
        if generate_xai and self.xai_engine and detected_defects:
            try:
                top_defect = max(detected_defects, key=lambda x: x["severity"]["score"])
                xai_result = self.xai_engine.generate_heatmap(
                    img_bgr=img_bgr,
                    target_box=top_defect["bbox"],
                    class_id=top_defect.get("class_id"),
                    target_class_name=top_defect["class"],
                    target_confidence=top_defect["confidence"],
                )
                xai_overlay_bgr = xai_result["overlay_bgr"]
                xai_data = {
                    "explained_defect_id": top_defect["id"],
                    "explained_class": top_defect["class"],
                    "target_class": xai_result["target_class"],
                    "target_confidence": xai_result["target_confidence"],
                    "target_bbox": xai_result["target_bbox"],
                    "overlay_shape": xai_result["overlay_shape"],
                    "attribution_method": xai_result["attribution_method"],
                    "disclaimer": xai_result["disclaimer"],
                    "interpretation": (
                        "Qualitative activation-energy heatmap highlights bottleneck feature regions near "
                        f"'{top_defect['class']}' detection. This is a visualization heuristic, not a "
                        "gradient proof. See DISCLAIMER field."
                    ),
                }
            except Exception as e:
                xai_data = {
                    "error": f"XAI computation skipped: {e}",
                    "attribution_method": "skipped",
                    "disclaimer": "XAI did not run.",
                }
        _xai_ms = (time.perf_counter() - _t_xai_start) * 1000.0

        # 8. Pipeline status and warnings (CRITICAL: distinguish real zero-detections from failures)
        pipeline_warnings = list(pipeline_warnings_pre) + list(pipeline_warnings_pre_defect)
        n_comps = len(detected_components)
        n_defects = len(detected_defects)
        total_pixels = orig_w * orig_h
        # Three mutually exclusive states (see STEP 2 of the acceptance contract):
        #   (a) genuine clean board : components > 0, defects == 0  -> PASS
        #   (b) suspicious zero     : components == 0 AND defects == 0 on a
        #                             non-trivial image -> REVIEW_REQUIRED
        #   (c) actual failure      : model(s) unavailable / exception -> ERROR
        suspiciously_empty = (n_comps == 0 and n_defects == 0 and total_pixels >= 200 * 200)
        models_available = (self.comp_model is not None) and (self.defect_model is not None)
        if suspiciously_empty:
            pipeline_warnings.append(
                "Both component and defect detectors returned zero detections on a non-trivial image. "
                "This may indicate a genuine clean board but could also signal a model/domain shift, "
                "class mismatch, or preprocessing issue. Verify with a known-defect reference image."
            )

        review_required = bool(suspiciously_empty and models_available)
        if review_required:
            quality_score = {
                **quality_score,
                "overall_score": None,
                "grade": "UNVERIFIED",
                "status": "REVIEW_REQUIRED",
                "defect_risk": "UNKNOWN",
                "flagged_reason": (
                    "Zero detections from both detectors on a non-trivial image. The score is "
                    "deliberately withheld rather than reported as a perfect 100."
                ),
                "formula": "Not computed — zero-detection safety override applied (see suspicious_zero_detection).",
                "summary": (
                    "No components and no defects were detected. A genuinely clean board and a silent "
                    "detection failure are indistinguishable here, so the quality score is withheld and "
                    "manual review is required."
                ),
            }
        # Subtract the XAI sub-window so no wall time is double-counted across buckets.
        _postprocess_ms = (time.perf_counter() - _t_post_start) * 1000.0 - _xai_ms
        _total_ms = (time.perf_counter() - _t_total_start) * 1000.0

        # Deterministic content-derived image id (traceable across systems)
        try:
            _image_id = "IMG-" + hashlib.sha1(
                np.ascontiguousarray(img_bgr).tobytes()
            ).hexdigest()[:12]
        except Exception:
            _image_id = f"IMG-{int(datetime.now().timestamp())}"

        try:
            _mv_component = os.path.basename(self.component_model_path)
        except Exception:
            _mv_component = None
        try:
            _mv_defect = os.path.basename(self.defect_model_path)
        except Exception:
            _mv_defect = None

        severity_summary = [
            {
                "defect_id": d["id"],
                "class": d["class"],
                "level": d["severity"].get("level"),
                "score": d["severity"].get("score"),
                "color": d["severity"].get("color"),
                "explanation": d["severity"].get("explanation"),
            }
            for d in detected_defects
        ]

        timing_ms = {
            "preprocess_ms": round(_preprocess_ms, 4),
            "component_inference_ms": round(_component_inference_ms, 4),
            "defect_inference_ms": round(_defect_inference_ms, 4),
            "xai_ms": round(_xai_ms, 4),
            "postprocess_ms": round(_postprocess_ms, 4),
            "total_ms": round(_total_ms, 4),
        }

        return {
            # --- SmartPCB-XAI unified inspection contract (v1.0) ---
            "contract_version": CONTRACT_VERSION,
            "inspection_status": "SUCCESS",
            "inspection_id": inspection_id,
            "image_id": _image_id,
            "timestamp": timestamp,
            "image_dimensions": {"width": orig_w, "height": orig_h},
            "components": detected_components,
            "component_count": n_comps,
            "defects": detected_defects,
            "defect_count": n_defects,
            "quality_score": quality_score,
            "xai": xai_data,
            "severity": severity_summary,
            "recommendations": recommendations,
            "pipeline_warnings": pipeline_warnings,
            "suspicious_zero_detection": suspiciously_empty,
            "review_required": review_required,
            "models_available": models_available,
            "model_version": {
                "component": _mv_component,
                "defect": _mv_defect,
                "engine_version": PROJECT_VERSION,
                "inference_device": getattr(self, "device", None),
            },
            # `inference_time_ms` is the contract field; `inference_timing_ms`
            # is retained unchanged for older callers.
            "inference_time_ms": timing_ms["total_ms"],
            "inference_timing_ms": timing_ms,
            # --- transport attachments (not part of the JSON contract) ---
            "annotated_image": annotated_bgr,
            "xai_overlay_image": xai_overlay_bgr,
        }
