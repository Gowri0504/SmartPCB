import os
import sys
import json
import time
import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

DEBUG_DIR = os.path.join(ROOT, "debug_outputs")
EXPRESS_URL = "http://127.0.0.1:5000"


def test_express_health():
    print("=" * 80)
    print("EXPRESS FULL CHAIN TEST: /api/auth/demo + /api/history + upload")
    print("=" * 80)

    # Step 1: Get demo auth token
    print("\n[1/4] Getting demo auth token...")
    try:
        r = requests.post(f"{EXPRESS_URL}/api/auth/demo", timeout=10)
        print(f"  status={r.status_code}")
        if r.status_code != 200:
            print(f"  FAIL: {r.text[:300]}")
            return None
        auth = r.json()
        token = auth.get("token")
        user = auth.get("user")
        print(f"  ✓ Token obtained for user: {user.get('name')} ({user.get('role')})")
    except Exception as e:
        print(f"  FAIL: {e}")
        return None

    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: Get history (before upload)
    print("\n[2/4] Fetching inspection history...")
    try:
        r = requests.get(f"{EXPRESS_URL}/api/history?limit=3", headers=headers, timeout=10)
        print(f"  status={r.status_code} len={len(r.content)}")
        hist = r.json() if r.status_code == 200 else []
        print(f"  ✓ History returned {len(hist)} records")
    except Exception as e:
        print(f"  FAIL: {e}")
        hist = []

    # Step 3: Upload and inspect
    print("\n[3/4] Upload + Inspect test PCB images via Express → FastAPI")
    test_images = [
        (os.path.join(ROOT, "test.jpg"), "PCB-TEST-01", 0.20, "SMT Board w/ 104 comps + 1 defect"),
        (os.path.join(ROOT, "datasets", "defects", "test", "images", "00041200.jpg"),
         "PCB-DEFECT-01", 0.20, "DeepPCB w/ 5 known defects"),
        (os.path.join(ROOT, "t2.jpg"), "PCB-CLEAN-01", 0.20, "Clean SMT 36 comps"),
    ]
    results = []
    for img_path, pcb_id, conf, desc in test_images:
        if not os.path.exists(img_path):
            print(f"  [SKIP] {desc} — not found")
            continue
        print(f"\n  -> Uploading {os.path.basename(img_path)}  ({desc})")
        with open(img_path, "rb") as f:
            files = {"image": (os.path.basename(img_path), f, "image/jpeg")}
            data = {"pcb_id": pcb_id, "confidence_threshold": str(conf)}
            t0 = time.perf_counter()
            try:
                r = requests.post(f"{EXPRESS_URL}/api/inspection/upload",
                                  files=files, data=data, headers=headers, timeout=180)
            except Exception as e:
                print(f"    [FAIL] Exception: {e}")
                continue
            t1 = time.perf_counter()

        print(f"    status={r.status_code}  total={(t1-t0)*1000:.0f}ms")
        if r.status_code != 200:
            print(f"    [FAIL] Response: {r.text[:400]}")
            continue

        res = r.json()
        comps = res.get("components", [])
        defects = res.get("defects", [])
        qs = res.get("quality_score", {})
        insp_id = res.get("inspection_id")
        status = res.get("inspection_status", "UNKNOWN")
        comp_count = res.get("component_count", len(comps))
        defect_count = res.get("defect_count", len(defects))

        print(f"    inspection_id: {insp_id}")
        print(f"    inspection_status: {status}")
        print(f"    components: {comp_count}  (raw list len={len(comps)})")
        print(f"    defects:    {defect_count}  (raw list len={len(defects)})")
        print(f"    QS: score={qs.get('overall_score') if qs else 'null'} "
              f"grade={qs.get('grade') if qs else 'null'} "
              f"status={qs.get('status') if qs else 'null'} "
              f"qdefect_count={qs.get('defect_count') if qs else 'null'}")
        print(f"    preview_base64 present: {bool(res.get('preview_image_base64'))}")
        print(f"    DB _id present: {bool(res.get('_id'))}")
        print(f"    DB createdAt present: {bool(res.get('createdAt'))}")

        # 5-way cross check: components, defect_count match API vs DB
        cross_ok = (comp_count == len(comps) and defect_count == len(defects)
                    and (qs is None or qs.get('defect_count') == len(defects)))
        print(f"    Cross-contract check: {'✓ PASS' if cross_ok else '✗ FAIL'}")

        # Verify we can read it back from DB
        try:
            r2 = requests.get(f"{EXPRESS_URL}/api/inspection/{insp_id}", headers=headers, timeout=20)
            if r2.status_code == 200:
                db = r2.json()
                db_match = (len(db.get("components", [])) == comp_count and
                            len(db.get("defects", [])) == defect_count)
                print(f"    DB roundtrip: status={r2.status_code}  match={'✓' if db_match else '✗'}  "
                      f"DB.comps={len(db.get('components',[]))}  DB.defects={len(db.get('defects',[]))}")
        except Exception as e:
            print(f"    DB roundtrip failed: {e}")

        results.append(res)

    # Step 4: Analytics endpoint
    print("\n[4/4] Analytics endpoint (aggregated from MongoDB)")
    try:
        r = requests.get(f"{EXPRESS_URL}/api/analytics", headers=headers, timeout=10)
        print(f"  status={r.status_code}")
        if r.status_code == 200:
            a = r.json()
            print(f"  Total inspections: {a.get('total_inspections')}")
            print(f"  Pass/Rework/Fail: {a.get('pass_count')}/{a.get('rework_count')}/{a.get('fail_count')}")
            print(f"  Avg quality score: {a.get('average_quality_score')}")
            print(f"  Yield rate: {a.get('yield_rate')}")
            print(f"  Defect distribution: {a.get('defect_distribution')}")
        else:
            print(f"  Response: {r.text[:300]}")
    except Exception as e:
        print(f"  FAIL: {e}")

    return results


if __name__ == "__main__":
    r = test_express_health()
    if r:
        print(f"\n{'='*80}")
        print(f"Full chain test complete. {len(r)} inspections processed.")
        print(f"{'='*80}")
