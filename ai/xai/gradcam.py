import os
import cv2
import torch
import numpy as np
from PIL import Image

from ai.config import (
    XAI_ATTRIBUTION_METHOD,
    XAI_DISCLAIMER,
)

class YOLOGradCAM:
    """
    Activation Energy Attribution (HONESTLY LABELED APPROXIMATION, not true
    gradient-based Grad-CAM++).

    Why "approximation": The forward pass is intentionally run under
    `torch.no_grad()` because authentic gradient-weighted Grad-CAM on YOLO
    detection heads requires a carefully chosen objective (not the multi-task
    detection loss naively) plus per-channel alpha computation from second /
    first order gradients of that specific objective. That authentic variant
    is targeted for Part 2 of SmartPCB-XAI.

    The visual produced here is a feature-map energy heuristic:
        cam_{h,w} = mean_{channels} | activation_{c, h, w} |
    optionally masked to a user-supplied detection box. It is useful for
    qualitative interpretability but MUST NOT be cited as Grad-CAM++ gradient
    attribution in any academic submission.
    """

    # Static identity: honestly reported by API / health endpoints
    ATTRIBUTION_METHOD = XAI_ATTRIBUTION_METHOD
    DISCLAIMER = XAI_DISCLAIMER
    def __init__(self, yolo_model, target_layer=None):
        self.yolo_model = yolo_model
        self.model = yolo_model.model
        self.model.eval()

        self.gradients = None
        self.activations = None

        # Auto-select target bottleneck layer if not specified
        if target_layer is None:
            # Typically layer 9 or 10 in YOLOv11 backbone (SPPF / Bottleneck)
            for i in range(len(self.model.model) - 2, -1, -1):
                layer = self.model.model[i]
                if hasattr(layer, 'cv2') or hasattr(layer, 'm') or 'SPP' in layer.__class__.__name__:
                    target_layer = layer
                    break
            if target_layer is None:
                target_layer = self.model.model[-2]

        self.target_layer = target_layer

        # Register hooks
        self.target_layer.register_forward_hook(self._forward_hook)
        self.target_layer.register_full_backward_hook(self._backward_hook)

    def _forward_hook(self, module, input, output):
        self.activations = output

    def _backward_hook(self, module, grad_in, grad_out):
        self.gradients = grad_out[0]

    def generate_heatmap(self, img_bgr, target_box=None, class_id=None,
                         target_class_name=None, target_confidence=None):
        """
        Generates activation-energy heatmap (honest approximation, not Grad-CAM++).
        Args:
            img_bgr: input BGR image (H, W, 3)
            target_box: optional [x1, y1, x2, y2] region of interest
            class_id: target class index (for metadata only)
            target_class_name: optional class name string for metadata
            target_confidence: optional float [0,1] for metadata
        Returns:
            result dict:
                heatmap_norm: (H, W) float32 in [0, 1]
                overlay_bgr: (H, W, 3) blended visualization
                attribution_method: str (honest label)
                disclaimer: str
                target_class: str or None
                target_confidence: float or None
                target_bbox: target_box copy or None
                overlay_shape: [H, W, 3]
        """
        orig_h, orig_w = img_bgr.shape[:2]

        # Preprocess for YOLO CAM (standard 640x640)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_cam = cv2.resize(img_rgb, (640, 640))
        input_tensor = torch.from_numpy(img_cam).permute(2, 0, 1).float().unsqueeze(0) / 255.0

        self.activations = None

        # NOTE: explicitly torch.no_grad(). This is NOT true gradient Grad-CAM.
        # See class docstring and DISCLAIMER.
        with torch.no_grad():
            try:
                self.model(input_tensor)
            except Exception:
                # Some model variants fail with no tensor requirement; safe fallback.
                pass

        if self.activations is not None:
            act = self.activations[0] if isinstance(self.activations, (tuple, list)) else self.activations
            if torch.is_tensor(act):
                # Standard YOLO activations shape: [N, C, H, W] or [C, H, W] or [H, W].
                # Reduce spatial dimensions to [H, W] energy map.
                if act.ndim == 4:
                    # [1, C, H, W] or [N, C, H, W]. Mean first over batch dim, then channel dim.
                    if act.shape[0] == 1:
                        cam = torch.mean(torch.abs(act[0]), dim=0).detach().cpu().numpy()
                    else:
                        cam = torch.mean(torch.abs(act), dim=(0, 1)).detach().cpu().numpy()
                elif act.ndim == 3:
                    cam = torch.mean(torch.abs(act), dim=0).detach().cpu().numpy()
                elif act.ndim == 2:
                    cam = torch.abs(act).detach().cpu().numpy()
                else:
                    cam = np.ones((max(1, orig_h // 32), max(1, orig_w // 32)), dtype=np.float32)
            else:
                cam = np.ones((max(1, orig_h // 32), max(1, orig_w // 32)), dtype=np.float32)
        else:
            cam = np.ones((max(1, orig_h // 32), max(1, orig_w // 32)), dtype=np.float32)

        if not np.all(np.isfinite(cam)):
            cam = np.nan_to_num(cam, nan=0.0, posinf=0.0, neginf=0.0)

        # ReLU and normalize
        cam = np.maximum(cam, 0)
        cam_max = float(cam.max()) if cam.size else 0.0
        if cam_max > 0:
            cam = cam / cam_max
        else:
            cam = np.zeros_like(cam)

        # Resize heatmap to original image dimensions
        heatmap_resized = cv2.resize(cam, (orig_w, orig_h))

        # Focus attention within target box if supplied
        if target_box is not None:
            mask = np.zeros_like(heatmap_resized)
            bx1, by1, bx2, by2 = map(int, target_box)
            bx1, by1 = max(0, bx1), max(0, by1)
            bx2, by2 = min(orig_w, bx2), min(orig_h, by2)
            if by2 > by1 and bx2 > bx1:
                mask[by1:by2, bx1:bx2] = 1.0
            # Gaussian smooth the boundary
            try:
                mask = cv2.GaussianBlur(mask, (31, 31), 0)
            except Exception:
                pass
            heatmap_resized = heatmap_resized * (0.3 + 0.7 * mask)
            hm_max = float(heatmap_resized.max()) if heatmap_resized.size else 0.0
            if hm_max > 0:
                heatmap_resized /= hm_max

        if not np.all(np.isfinite(heatmap_resized)):
            heatmap_resized = np.nan_to_num(heatmap_resized, nan=0.0, posinf=0.0, neginf=0.0)

        # Color map overlay — enforce single-channel uint8 of correct shape for OpenCV
        heatmap_uint8 = np.uint8(np.clip(255.0 * heatmap_resized, 0, 255))
        if heatmap_uint8.ndim != 2:
            heatmap_uint8 = np.squeeze(heatmap_uint8)
        if heatmap_uint8.ndim != 2:
            heatmap_uint8 = heatmap_uint8[:, :, 0] if heatmap_uint8.ndim == 3 else np.zeros((orig_h, orig_w), dtype=np.uint8)
        try:
            colormap = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        except Exception:
            # Fallback grayscale-to-color conversion if any remaining shape issue
            colormap = cv2.cvtColor(heatmap_uint8, cv2.COLOR_GRAY2BGR)
        overlay_bgr = cv2.addWeighted(img_bgr, 0.6, colormap, 0.4, 0)

        return {
            "heatmap_norm": heatmap_resized,
            "overlay_bgr": overlay_bgr,
            "attribution_method": self.ATTRIBUTION_METHOD,
            "disclaimer": self.DISCLAIMER,
            "target_class": target_class_name,
            "target_confidence": float(target_confidence) if target_confidence is not None else None,
            "target_bbox": list(target_box) if target_box is not None else None,
            "overlay_shape": [int(overlay_bgr.shape[0]), int(overlay_bgr.shape[1]), int(overlay_bgr.shape[2])],
            "class_id": int(class_id) if class_id is not None else None,
        }
