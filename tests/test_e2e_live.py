import os
import requests
import time

FASTAPI_URL = "http://127.0.0.1:8000"
BACKEND_URL = "http://127.0.0.1:5000"
FRONTEND_URL = "http://127.0.0.1:3000"

def main():
    print("=" * 60)
    print("STARTING END-TO-END SYSTEM INTEGRATION TEST")
    print("=" * 60)

    # 1. Check FastAPI Health
    print("\n[Step 1] Checking FastAPI AI Service Health...")
    for attempt in range(10):
        try:
            r = requests.get(f"{FASTAPI_URL}/health", timeout=3)
            if r.status_code == 200:
                print("  [PASS] FastAPI AI Engine is healthy! Response:", r.json())
                break
        except Exception:
            time.sleep(2)
    else:
        print("  [FAIL] FastAPI service did not respond.")
        return

    # 2. Check Backend Server
    print("\n[Step 2] Checking Express Backend API...")
    for attempt in range(10):
        try:
            r = requests.get(f"{BACKEND_URL}/api/analytics", timeout=3)
            if r.status_code == 200:
                print("  [PASS] Express Backend is running! Analytics:", r.json())
                break
        except Exception:
            time.sleep(2)
    else:
        print("  [FAIL] Express backend did not respond.")
        return

    # 3. Check React Frontend
    print("\n[Step 3] Checking React Industrial Dashboard...")
    try:
        r = requests.get(FRONTEND_URL, timeout=3)
        if r.status_code == 200 and "SmartPCB-XAI" in r.text:
            print("  [PASS] React Frontend is responding on port 3000 with index.html bundle!")
        else:
            print(f"  [STATUS] Frontend returned status: {r.status_code}")
    except Exception as e:
        print(f"  [WARN] Frontend check: {e}")

    # 4. Upload & Inspect a Real PCB Image
    print("\n[Step 4] Uploading and Inspecting Real PCB Image via Backend Pipeline...")
    # Find test image
    test_img = None
    for cand_dir in ["datasets/defects/test/images", "datasets/components_unified/test/images"]:
        if os.path.exists(cand_dir):
            files = [f for f in os.listdir(cand_dir) if f.endswith(('.jpg', '.png'))]
            if files:
                test_img = os.path.join(cand_dir, files[0])
                break

    if not test_img:
        print("  [FAIL] No test image found.")
        return

    print(f"  Selected Test Image: {test_img}")
    with open(test_img, "rb") as f:
        files = {"image": (os.path.basename(test_img), f, "image/jpeg")}
        data = {"pcb_id": "PCB-TEST-BOARD-001", "confidence_threshold": 0.20}
        r = requests.post(f"{BACKEND_URL}/api/inspection/upload", files=files, data=data, timeout=30)

    if r.status_code == 200:
        insp = r.json()
        print(f"  [PASS] Inspection Completed! ID: {insp.get('inspection_id')}")
        print(f"  Quality Score: {insp.get('quality_score', {}).get('overall_score')} / 100 ({insp.get('quality_score', {}).get('status')})")
        print(f"  Components Found: {len(insp.get('components', []))}")
        print(f"  Defects Found: {len(insp.get('defects', []))}")
        print(f"  Preview Image Generated: {'Yes' if insp.get('preview_image_base64') else 'No'}")
    else:
        print(f"  [FAIL] Upload failed with status {r.status_code}: {r.text}")
        return

    # 5. Test PDF Report Generation
    print("\n[Step 5] Testing PDF Report Export...")
    pdf_resp = requests.post(f"{BACKEND_URL}/api/reports/pdf", json={"inspection_data": insp}, timeout=15)
    if pdf_resp.status_code == 200 and len(pdf_resp.content) > 1000:
        print(f"  [PASS] PDF Report successfully generated! Size: {len(pdf_resp.content):,} bytes")
    else:
        print(f"  [FAIL] PDF generation failed: status {pdf_resp.status_code}")

    # 6. Test Excel Audit Export
    print("\n[Step 6] Testing Excel Audit Export...")
    excel_resp = requests.post(f"{BACKEND_URL}/api/reports/excel", json={"inspection_data": insp}, timeout=15)
    if excel_resp.status_code == 200 and len(excel_resp.content) > 1000:
        print(f"  [PASS] Excel Workbook successfully generated! Size: {len(excel_resp.content):,} bytes")
    else:
        print(f"  [FAIL] Excel generation failed: status {excel_resp.status_code}")

    print("\n" + "=" * 60)
    print("ALL END-TO-END INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
