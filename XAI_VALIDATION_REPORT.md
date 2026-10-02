# XAI VALIDATION REPORT — 2026-09-23

## What the XAI engine actually is

`ai/xai/gradcam.py` (`YOLOGradCAM`) produces an **activation-energy
approximation**, honestly labeled `activation_energy_approximation`:

    cam_{h,w} = mean_channels |activation_{c,h,w}|   (run under torch.no_grad())

optionally masked to the explained defect's bounding box, blended into an
overlay image. It is NOT gradient-weighted Grad-CAM/Grad-CAM++; authentic
gradient attribution is a declared Part 2 target. The module docstring, the
API payload (`attribution_method`, `disclaimer`, `interpretation`), and the
inspection `xai` block all carry this labeling.

## Verified behavior (this machine, CPU)

1. **Runs on real data**: 20 held-out DeepPCB test images
   (`results/final_20_image_validation.json`) — every run produced an
   `xai` block with `explained_class` = highest-severity defect, an
   `overlay_base64` image, and the disclaimer field. 20/20 SUCCESS.
2. **E2E over HTTP**: POST /api/v1/inspect on image 00041200.jpg returned
   `xai.explained_class = open`, method `activation_energy_approximation`,
   overlay attached; xai_ms ≈ 2507 ms of a 6338 ms total.
3. **Timing accounting**: XAI is bracketed as its own bucket inside
   `inference_timing_ms`; the five buckets are disjoint and sum to
   total_ms (asserted by tests/test_inference_engine.py::
   test_timing_buckets_are_disjoint_and_complete).
4. **Failure containment**: XAI exceptions degrade to an `xai.error` block;
   they never fail the inspection.

## NOT VERIFIED (stated, not hidden)

- **Attribution faithfulness**: no insertion/deletion or pointing-game
  evaluation was run; the heuristic's qualitative usefulness is asserted only
  at the level "heatmap highlights bottleneck feature regions near the
  explained defect". Any stronger claim would be fabrication.
- **Class-discriminativity**: the heuristic does not compute per-class
  gradients, so "why this class" is not answerable by the current engine.
- **GPU behavior**: not verified (no CUDA on this machine).

## Reproducibility

- Overlay generation is deterministic for a fixed input image and target box
  (repeat runs on 00041200.jpg produced identical explained_defect_id/class).
- Method identity is static (`YOLOGradCAM.ATTRIBUTION_METHOD =
  XAI_ATTRIBUTION_METHOD` from `ai/config.py`) and flows into every payload.
