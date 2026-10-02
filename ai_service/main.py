import os
import sys
import io
import cv2
import base64
import numpy as np
import torch
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.config import (
    PROJECT_VERSION,
    CANONICAL_COMPONENT_CLASSES,
    CANONICAL_DEFECT_CLASSES,
    CURATED_COMPONENT_CLASSES,
    CURATED_DEFECT_CLASSES,
    DEPLOYED_DEFECT_CLASSES,
    COMPONENT_MAPPING_STATUS,
    COMPONENT_MAPPING_NOTE,
    DEFECT_MAPPING_STATUS,
    DEFECT_MAPPING_NOTE,
    UNMAPPED_COMPONENT_CLASSES,
    UNDETECTABLE_CURATED_COMPONENT_CLASSES,
    COMPONENT_CLASS_ALIASES,
    DEFECT_CLASS_ALIASES,
)
from ai.inference.engine import SmartPCBInspectionEngine, build_error_result
from ai.reports.report_generator import ReportGenerator
from ai.model_safety import verify_checkpoint, taxonomy_alignment_report

app = FastAPI(
    title="SmartPCB-XAI Intelligent Inspection API",
    description="Explainable AI-based PCB Component & Defect Inspection Service",
    version=PROJECT_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instance
print("Initializing SmartPCB Inspection Engine...")
engine = SmartPCBInspectionEngine()
print(f"Inspection Engine Ready on device={engine.device}.")

# Model safety verification layer (runs once at startup — T6)
_COMPONENT_VERIFICATION = {"status": "UNVERIFIED"}
_DEFECT_VERIFICATION = {"status": "UNVERIFIED"}
try:
    _COMPONENT_VERIFICATION = verify_checkpoint(
        getattr(engine, "component_model_path", "models/component_best.pt"),
        CANONICAL_COMPONENT_CLASSES,
        device=getattr(engine, "device", None),
        alias_map=COMPONENT_CLASS_ALIASES,
    )
except Exception as _e:
    _COMPONENT_VERIFICATION = {"status": "BLOCKED", "error": f"verify_checkpoint exception: {_e}"}
try:
    _DEFECT_VERIFICATION = verify_checkpoint(
        getattr(engine, "defect_model_path", "models/defect_best.pt"),
        CANONICAL_DEFECT_CLASSES,
        device=getattr(engine, "device", None),
        alias_map=DEFECT_CLASS_ALIASES,
    )
except Exception as _e:
    _DEFECT_VERIFICATION = {"status": "BLOCKED", "error": f"verify_checkpoint exception: {_e}"}
print(f"[ModelSafety] component={_COMPONENT_VERIFICATION.get('status')} defect={_DEFECT_VERIFICATION.get('status')}")

REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports", "generated"))
os.makedirs(REPORTS_DIR, exist_ok=True)

@app.get("/health")
def health_check():
    xai_method = None
    xai_disclaimer = None
    xai_loaded = False
    try:
        if engine.xai_engine is not None:
            xai_method = getattr(engine.xai_engine, "ATTRIBUTION_METHOD", None)
            xai_disclaimer = getattr(engine.xai_engine, "DISCLAIMER", None)
            xai_loaded = True
    except Exception:
        pass

    status = "ok"
    if not (engine.component_model_loaded and engine.defect_model_loaded):
        status = "degraded"
    if not xai_loaded and (engine.component_model_loaded or engine.defect_model_loaded):
        status = status if status == "degraded" else "degraded"

    try:
        actual_device = str(engine.device) if engine.device else ("cuda" if torch.cuda.is_available() else "cpu")
    except Exception:
        actual_device = "unknown"

    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "version": PROJECT_VERSION,
        "device": actual_device,
        "engine_status": {
            "component_model_loaded": bool(getattr(engine, "component_model_loaded", False)),
            "defect_model_loaded": bool(getattr(engine, "defect_model_loaded", False)),
            "xai_engine_loaded": xai_loaded,
        },
        "model_status": {
            "component_model": {
                "path": getattr(engine, "component_model_path", None),
                "loaded": bool(getattr(engine, "component_model_loaded", False)),
                "classes": CANONICAL_COMPONENT_CLASSES,
                "verification": _COMPONENT_VERIFICATION,
            },
            "defect_model": {
                "path": getattr(engine, "defect_model_path", None),
                "loaded": bool(getattr(engine, "defect_model_loaded", False)),
                "classes": CANONICAL_DEFECT_CLASSES,
                "verification": _DEFECT_VERIFICATION,
            },
            "xai_engine": {
                "method": xai_method,
                "disclaimer": xai_disclaimer,
                "loaded": xai_loaded,
            },
        },
        "canonical_classes": {
            "components": CANONICAL_COMPONENT_CLASSES,
            "defects": CANONICAL_DEFECT_CLASSES,
        },
        # Honest taxonomy reconciliation: which curated-dataset classes the
        # deployed models cannot emit, and which emitted classes have no curated
        # equivalent. Single source of truth: ai.model_safety.taxonomy_alignment_report().
        # See COMPONENT_CLASS_SCHEMA.md / DEFECT_CLASS_SCHEMA.md.
        "class_taxonomy": taxonomy_alignment_report(),
    }

@app.post("/api/v1/inspect")
async def inspect_pcb(
    file: UploadFile = File(...),
    confidence_threshold: float = Form(0.25),
    iou_threshold: float = Form(0.45)
):
    def _error_payload(warnings):
        payload = build_error_result(warnings=warnings)
        payload["preview_image_base64"] = None
        return payload

    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_bgr is None:
            return _error_payload(["Image decode failed: invalid or corrupted image bytes."])

        result = engine.inspect(
            image_input=img_bgr,
            conf_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
            generate_xai=True
        )

        annotated_bgr = result.pop("annotated_image", None)
        preview_base64 = None
        if annotated_bgr is not None:
            _, buffer = cv2.imencode(".jpg", annotated_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
            preview_base64 = base64.b64encode(buffer).decode("utf-8")

        result["preview_image_base64"] = f"data:image/jpeg;base64,{preview_base64}" if preview_base64 else None

        xai_overlay_bgr = result.pop("xai_overlay_image", None)
        if xai_overlay_bgr is not None and "xai" in result and isinstance(result["xai"], dict):
            _, xai_buffer = cv2.imencode(".jpg", xai_overlay_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
            result["xai"]["overlay_base64"] = f"data:image/jpeg;base64,{base64.b64encode(xai_buffer).decode('utf-8')}"

        if "inspection_status" not in result:
            result["inspection_status"] = "SUCCESS"

        return result

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[INFERENCE ERROR] {e}")
        print(tb)
        # Only the exception type/message is surfaced; the traceback stays in
        # server logs so internal paths are never exposed to API clients.
        return _error_payload([
            f"Inference exception: {type(e).__name__}: {e}",
            "See server logs for full traceback.",
        ])

class ReportRequest(BaseModel):
    inspection_data: dict

@app.post("/api/v1/report/pdf")
async def generate_pdf_report(req: ReportRequest):
    try:
        insp_id = req.inspection_data.get("inspection_id", f"INSP-{int(datetime.now().timestamp())}")
        out_path = os.path.join(REPORTS_DIR, f"{insp_id}_report.pdf")
        ReportGenerator.generate_pdf(req.inspection_data, out_path)
        return FileResponse(
            out_path,
            media_type="application/pdf",
            filename=f"{insp_id}_report.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF Generation Error: {e}")

@app.post("/api/v1/report/excel")
async def generate_excel_report(req: ReportRequest):
    try:
        insp_id = req.inspection_data.get("inspection_id", f"INSP-{int(datetime.now().timestamp())}")
        out_path = os.path.join(REPORTS_DIR, f"{insp_id}_audit.xlsx")
        ReportGenerator.generate_excel(req.inspection_data, out_path)
        return FileResponse(
            out_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"{insp_id}_audit.xlsx"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel Generation Error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
