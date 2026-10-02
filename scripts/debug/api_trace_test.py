import os
import sys
import json
import time
import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

FASTAPI_URL = "http://127.0.0.1:8000"
DEBUG_DIR = os.path.join(ROOT, "debug_outputs")

def test_health():
    print("=" * 80)
    print("STEP 1: FastAPI /health")
    print("=" * 80)
    try:
        r = requests.get(f"{FASTAPI_URL}/health", timeout=10)
        print(f"Status: {r.status_code}")
        print(json.dumps(r.json(), indent=2))
        return r.status_code == 200
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_inspect_direct(img_path, conf=0.20, label=""):
    print(f"\n{'='*80}")
    print(f"STEP 2: Direct FastAPI /api/v1/inspect — {label}")
    print(f"Image: {img_path}")
    print(f"{'='*80}")

    if not os.path.exists(img_path):
        print(f"[SKIP] File not found: {img_path}")
        return None

    with open(img_path, "rb") as f:
        files = {"file": (os.path.basename(img_path), f, "image/jpeg")}
        data = {"confidence_threshold": str(conf), "iou_threshold": "0.45"}
        t0 = time.perf_counter()
        try:
            r = requests.post(f"{FASTAPI_URL}/api/v1/inspect", files=files, data=data, timeout=120)
        except Exception as e:
            print(f"[FAIL] Request exception: {e}")
            return None
        t1 = time.perf_counter()

    total_s = t1 - t0
    print(f"HTTP status: {r.status_code}")
    print(f"Elapsed: {total_s*1000:.1f} ms")

    if r.status_code != 200:
        print(f"[FAIL] Non-200 response: {r.text[:400]}")
        return None

    result = r.json()
    comps = result.get("components", [])
    defects = result.get("defects", [])
    qs = result.get("quality_score", {})

    print(f"\n  Components detected: {len(comps)}")
    for c in comps[:8]:
        print(f"    COMP: {c['class']:<10} conf={c['confidence']:.4f} bbox={c['bbox']}")
    if len(comps) > 8:
        print(f"    ... (+{len(comps)-8} more components)")

    print(f"\n  Defects detected: {len(defects)}")
    for d in defects[:8]:
        sev = d.get('severity', {})
        print(f"    DEFECT: {d['class']:<15} conf={d['confidence']:.4f} "
              f"sev={sev.get('level')}({sev.get('score')}) bbox={d['bbox']}")

    print(f"\n  Quality Score: {qs.get('overall_score')}  Status: {qs.get('status')}  "
          f"Grade: {qs.get('grade')}  DefectCount: {qs.get('defect_count', 'N/A')}")
    print(f"  XAI generated: {'overlay_base64' in result.get('xai', {})}")
    print(f"  Preview image: {'preview_image_base64' in result and len(result['preview_image_base64']) > 100}")
    print(f"  Recommendations: {len(result.get('recommendations', []))}")

    json_path = os.path.join(DEBUG_DIR, f"API_DIRECT_{os.path.splitext(os.path.basename(img_path))[0]}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in result.items() if k not in ['preview_image_base64',
                   'xai'] or k != 'xai'}, f, indent=2, default=str,
                  ensure_ascii=False)
    # save xai separately since it might be huge
    if 'xai' in result:
        xai_path = os.path.join(DEBUG_DIR, f"API_DIRECT_XAI_{os.path.splitext(os.path.basename(img_path))[0]}.json")
        with open(xai_path, "w", encoding="utf-8") as f:
            json.dump(result['xai'], f, indent=2, default=str, ensure_ascii=False)
    print(f"  -> API response saved to: {json_path}")

    # Compare with baseline (direct engine)
    print(f"\n--- Direct API vs Direct Engine Baseline Comparison ---")
    baseline_pairs = {
        "test.jpg": (109, 2, 94.5),
        "t2.jpg": (36, 0, 100.0),
        "00041200.jpg": (0, 5, 46.4),
    }
    base = os.path.basename(img_path)
    if base in baseline_pairs:
        exp_c, exp_d, exp_s = baseline_pairs[base]
        match_c = len(comps) == exp_c
        match_d = len(defects) == exp_d
        # allow score +/- 1.0
        match_s = abs(qs.get('overall_score', -1) - exp_s) <= 2.0
        status = "✓ MATCH" if (match_c and match_d and match_s) else "⚠ MISMATCH"
        print(f"  {status}: Expected (comps={exp_c}, defects={exp_d}, score={exp_s}) "
              f"→ Got (comps={len(comps)}, defects={len(defects)}, score={qs.get('overall_score')})")

    return result


def test_report_endpoints(result):
    if result is None:
        print("\n[SKIP] Report endpoint test — no result.")
        return
    print(f"\n{'='*80}")
    print("STEP 3: FastAPI /api/v1/report/pdf & /api/v1/report/excel")
    print(f"{'='*80}")

    payload = {"inspection_data": {k: v for k, v in result.items() if k != "preview_image_base64"}}

    # PDF test
    t0 = time.perf_counter()
    try:
        r_pdf = requests.post(f"{FASTAPI_URL}/api/v1/report/pdf", json=payload, timeout=60)
        t1 = time.perf_counter()
        pdf_ok = r_pdf.status_code == 200 and len(r_pdf.content) > 1000
        print(f"PDF: status={r_pdf.status_code} size={len(r_pdf.content)} bytes  time={(t1-t0)*1000:.0f}ms  "
              f"content-type={r_pdf.headers.get('Content-Type')}")
        if pdf_ok:
            pdf_path = os.path.join(DEBUG_DIR, "API_TEST_REPORT.pdf")
            with open(pdf_path, "wb") as f:
                f.write(r_pdf.content)
            print(f"  ✓ PDF saved to {pdf_path}")
        else:
            print(f"  ✗ PDF issue: {r_pdf.text[:200] if not pdf_ok else ''}")
    except Exception as e:
        print(f"  [FAIL] PDF: {e}")

    # Excel test
    t0 = time.perf_counter()
    try:
        r_xlsx = requests.post(f"{FASTAPI_URL}/api/v1/report/excel", json=payload, timeout=60)
        t1 = time.perf_counter()
        xlsx_ok = r_xlsx.status_code == 200 and len(r_xlsx.content) > 1000
        print(f"XLSX: status={r_xlsx.status_code} size={len(r_xlsx.content)} bytes  time={(t1-t0)*1000:.0f}ms  "
              f"content-type={r_xlsx.headers.get('Content-Type')}")
        if xlsx_ok:
            xlsx_path = os.path.join(DEBUG_DIR, "API_TEST_AUDIT.xlsx")
            with open(xlsx_path, "wb") as f:
                f.write(r_xlsx.content)
            print(f"  ✓ XLSX saved to {xlsx_path}")
    except Exception as e:
        print(f"  [FAIL] XLSX: {e}")


def main():
    ok = test_health()
    if not ok:
        print("FastAPI health check failed. Is the server running?")
        sys.exit(1)

    test_images = [
        (os.path.join(ROOT, "test.jpg"), 0.20, "SMT Test Board (Known 109 components)"),
        (os.path.join(ROOT, "t2.jpg"), 0.20, "Large SMT Board (Known 36 components)"),
        (os.path.join(ROOT, "datasets", "defects", "test", "images", "00041200.jpg"), 0.20, "DeepPCB Defect Board (Known 5 defects)"),
        (os.path.join(ROOT, "defect-pcb.jpg"), 0.20, "External Defect-PCB"),
    ]
    results = []
    for path, conf, desc in test_images:
        r = test_inspect_direct(path, conf, desc)
        if r is not None:
            results.append(r)

    if results:
        test_report_endpoints(results[0])

    print(f"\n{'='*80}")
    print("API TRACE COMPLETE.")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
