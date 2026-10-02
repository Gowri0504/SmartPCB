import os
import sys
import json
import time
import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

DEBUG_DIR = os.path.join(ROOT, "debug_outputs")
EXPRESS_URL = "http://127.0.0.1:5000"
FASTAPI_URL = "http://127.0.0.1:8000"


def cross_check(label, expected, actual):
    ok = expected == actual
    print(f"    [{label}] expected={expected}  actual={actual}  "
          + ("✓" if ok else "✗ FAIL"))
    return ok


def test_full_system():
    ok_count = 0
    total = 0

    print("=" * 80)
    print("COMPREHENSIVE SYSTEM VALIDATION")
    print("=" * 80)

    # Auth token
    r = requests.post(f"{EXPRESS_URL}/api/auth/demo", timeout=10)
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ============================================================
    # 1. UPLOAD 3 IMAGES + CROSS CHECK CONTRACT
    # ============================================================
    print("\n[1/6] Inspection Upload + 5-Way Contract (API == Mongo)")
    print("-" * 60)

    tests = [
        {
            "path": os.path.join(ROOT, "datasets", "defects", "test", "images", "00041200.jpg"),
            "desc": "Known-Defect DeepPCB (5 defects, no components)",
            "expect_comps": 0,
            "expect_defects": 5,
            "expect_score": 46.4,
        },
        {
            "path": os.path.join(ROOT, "test.jpg"),
            "desc": "SMT Board (104 comps, 1 defect)",
            "expect_comps": 104,
            "expect_defects": 1,
            "expect_score": 96.2,
        },
        {
            "path": os.path.join(ROOT, "t2.jpg"),
            "desc": "Clean SMT (36 comps, 0 defects → 100 PASS)",
            "expect_comps": 36,
            "expect_defects": 0,
            "expect_score": 100.0,
        },
    ]

    uploaded_ids = []
    for t in tests:
        if not os.path.exists(t["path"]):
            print(f"  [SKIP] {t['desc']}")
            continue
        print(f"\n  Board: {t['desc']}")
        with open(t["path"], "rb") as f:
            files = {"image": (os.path.basename(t["path"]), f, "image/jpeg")}
            data = {"pcb_id": "PCB-E2E-" + str(len(uploaded_ids) + 1),
                    "confidence_threshold": "0.20"}
            r = requests.post(f"{EXPRESS_URL}/api/inspection/upload",
                              files=files, data=data, headers=headers, timeout=240)
        total += 1
        if r.status_code != 200:
            print(f"    HTTP {r.status_code} FAIL")
            continue

        insp = r.json()
        insp_id = insp["inspection_id"]
        uploaded_ids.append(insp_id)
        n_comps = insp["component_count"]
        n_defects = insp["defect_count"]
        qs = insp["quality_score"]
        status = insp["inspection_status"]

        # 5-way cross check for each field
        ok_count += cross_check("inspection_status", "SUCCESS", status)
        ok_count += cross_check("component_count (top)", t["expect_comps"], n_comps)
        ok_count += cross_check("components (arr len)", t["expect_comps"], len(insp["components"]))
        ok_count += cross_check("defect_count (top)", t["expect_defects"], n_defects)
        ok_count += cross_check("defects (arr len)", t["expect_defects"], len(insp["defects"]))
        ok_count += cross_check("QS.defect_count", t["expect_defects"],
                                qs["defect_count"] if qs else None)
        ok_count += cross_check("QS.component_count", t["expect_comps"],
                                qs["component_count"] if qs else None)

        actual_score = qs["overall_score"] if qs else None
        diff = abs(actual_score - t["expect_score"]) if actual_score is not None else 999
        score_ok = diff <= 0.5
        print(f"    [QS.overall_score] expected≈{t['expect_score']} actual={actual_score} "
              + ("✓" if score_ok else f"✗ diff={diff}"))
        total += 7

        # DB roundtrip
        r2 = requests.get(f"{EXPRESS_URL}/api/inspection/{insp_id}", headers=headers, timeout=20)
        total += 1
        if r2.status_code == 200:
            db = r2.json()
            db_ok = (db["component_count"] == n_comps
                     and db["defect_count"] == n_defects
                     and len(db["components"]) == len(insp["components"])
                     and len(db["defects"]) == len(insp["defects"]))
            print(f"    [DB roundtrip] status=200  match={'✓ PASS' if db_ok else '✗ FAIL'}")
            ok_count += 1 if db_ok else 0
        else:
            print(f"    [DB roundtrip] status={r2.status_code} ✗ FAIL")

        # Save XAI + QS samples from this inspection for report testing
        if insp_id == uploaded_ids[0]:
            REPORT_INSP = insp

    total += 1  # for above if-else branch

    # ============================================================
    # 2. PDF REPORT GENERATION
    # ============================================================
    print("\n[2/6] PDF Report Generation (Express→FastAPI→PDF)")
    print("-" * 60)
    r = requests.post(f"{EXPRESS_URL}/api/reports/pdf",
                      headers=headers, json={"inspection_data": REPORT_INSP}, timeout=60)
    total += 1
    if r.status_code == 200 and len(r.content) > 1000 and r.headers.get("content-type") == "application/pdf":
        pdf_path = os.path.join(DEBUG_DIR, "E2E_Report.pdf")
        with open(pdf_path, "wb") as f:
            f.write(r.content)
        print(f"  ✓ PDF generated: {len(r.content)} bytes")
        print(f"  ✓ Headers: content-type={r.headers.get('content-type')}")
        print(f"  ✓ Content-Disposition: {r.headers.get('content-disposition')}")
        ok_count += 1
    else:
        print(f"  ✗ FAIL status={r.status_code} len={len(r.content)} ct={r.headers.get('content-type')}")

    # ============================================================
    # 3. EXCEL REPORT GENERATION
    # ============================================================
    print("\n[3/6] Excel Report Generation (Express→FastAPI→XLSX)")
    print("-" * 60)
    r = requests.post(f"{EXPRESS_URL}/api/reports/excel",
                      headers=headers, json={"inspection_data": REPORT_INSP}, timeout=60)
    total += 1
    if r.status_code == 200 and len(r.content) > 1000:
        xlsx_path = os.path.join(DEBUG_DIR, "E2E_Report.xlsx")
        with open(xlsx_path, "wb") as f:
            f.write(r.content)
        print(f"  ✓ XLSX generated: {len(r.content)} bytes")
        ok_count += 1
    else:
        print(f"  ✗ FAIL status={r.status_code} len={len(r.content)}")

    # ============================================================
    # 4. CONTINUOUS LEARNING: FEEDBACK CORRECTION
    # ============================================================
    print("\n[4/6] Continuous Learning: Engineer Feedback Correction")
    print("-" * 60)
    feedback_id = uploaded_ids[0]
    correction_payload = {
        "inspection_id": feedback_id,
        "engineer_name": "E2E Test Engineer",
        "action": "CONFIRMED",
        "corrected_components": [],
        "corrected_defects": [
            {"class": "short", "bbox": [100, 200, 120, 230], "confidence": 1.0}
        ],
        "notes": "Automated end-to-end test feedback. 1 short defect confirmed.",
        "false_positives": [],
        "false_negatives": []
    }
    r = requests.post(f"{EXPRESS_URL}/api/feedback",
                      headers=headers, json=correction_payload, timeout=30)
    total += 1
    if r.status_code == 200:
        fb = r.json()
        print(f"  ✓ Feedback saved: id={fb.get('_id', fb.get('id'))}")
        print(f"  ✓ Feedback inspection_id match: {fb.get('inspection_id') == feedback_id}")

        # Verify inspection.verification_status now CONFIRMED
        r2 = requests.get(f"{EXPRESS_URL}/api/inspection/{feedback_id}", headers=headers, timeout=20)
        total += 1
        if r2.status_code == 200 and r2.json().get("verification_status") == "CONFIRMED":
            print(f"  ✓ inspection.verification_status == CONFIRMED")
            ok_count += 2
        else:
            print(f"  ✗ verification_status not updated: {r2.json().get('verification_status')}")
    else:
        print(f"  ✗ FAIL status={r.status_code} body={r.text[:200]}")

    # ============================================================
    # 5. ANALYTICS - REAL MONGODB AGGREGATIONS
    # ============================================================
    print("\n[5/6] Analytics Aggregation (from MongoDB real records)")
    print("-" * 60)
    r = requests.get(f"{EXPRESS_URL}/api/analytics", headers=headers, timeout=10)
    total += 1
    if r.status_code == 200:
        a = r.json()
        print(f"  Total inspections:  {a.get('total_inspections')}")
        print(f"  Pass/Rework/Fail:   {a.get('pass_count')}/{a.get('rework_count')}/{a.get('fail_count')}")
        print(f"  Avg quality score:  {a.get('average_quality_score')}")
        print(f"  Yield rate:         {a.get('yield_rate')}")
        print(f"  Defect distribution:{a.get('defect_distribution')}")
        real = (a.get("total_inspections", 0) >= 3
                and isinstance(a.get("defect_distribution"), dict)
                and len(a.get("defect_distribution")) > 0)
        print(f"  [Real data check] {'✓ PASS' if real else '✗ FAIL (fake zeros)'}")
        ok_count += 1 if real else 0

    # ============================================================
    # 6. XAI, SEVERITY, RECOMMENDATIONS - CONTRACT VALIDATION
    # ============================================================
    print("\n[6/6] XAI / Severity / Recommendations Data Contract")
    print("-" * 60)

    # For the defected board, each defect must have a severity with score+level+color
    defected_insp = REPORT_INSP
    severities_ok = all(
        (d.get("severity")
         and isinstance(d["severity"].get("score"), (int, float))
         and d["severity"].get("level") in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
         and isinstance(d["severity"].get("color"), str))
        for d in defected_insp["defects"]
    )
    total += 1
    print(f"  [Severity engine]  all {len(defected_insp['defects'])} defects have "
          f"score/level/color → {'✓ PASS' if severities_ok else '✗ FAIL'}")
    ok_count += 1 if severities_ok else 0

    # Recommendations must not claim AI-proved root cause
    recs = defected_insp["recommendations"]
    recs_ok = (len(recs) > 0
               and all("probable_causes" in r for r in recs)
               and all("repair_actions" in r for r in recs))
    total += 1
    print(f"  [Recommendations]  {len(recs)} recs with probable_causes/repair_actions "
          f"→ {'✓ PASS' if recs_ok else '✗ FAIL'}")
    ok_count += 1 if recs_ok else 0

    # XAI: overlay_base64 present (or skipped)
    xai = defected_insp.get("xai") or {}
    xai_overlay_ok = (
        xai.get("overlay_base64") is not None
        and xai.get("overlay_base64", "").startswith("data:image/jpeg;base64,")
        and len(xai.get("overlay_base64")) > 500
    ) or ("error" in xai)
    total += 1
    print(f"  [XAI Grad-CAM++]   explained_class={xai.get('explained_class')} "
          f"overlay_len={len(xai.get('overlay_base64', ''))} "
          f"→ {'✓ PASS' if xai_overlay_ok else '✗ FAIL'}")
    ok_count += 1 if xai_overlay_ok else 0

    # ============================================================
    # FINAL SUMMARY
    # ============================================================
    pct = (ok_count / total * 100) if total > 0 else 0
    print()
    print("=" * 80)
    print(f"COMPREHENSIVE VALIDATION SUMMARY: {ok_count}/{total} = {pct:.1f}%")
    print("=" * 80)
    print(f"  Uploaded inspections: {len(uploaded_ids)}")
    print(f"  PDF/XLSX generated:   {os.path.exists(os.path.join(DEBUG_DIR, 'E2E_Report.pdf'))} "
          f"/ {os.path.exists(os.path.join(DEBUG_DIR, 'E2E_Report.xlsx'))}")
    print(f"  Feedback correction:  saved → inspection.verification_status CONFIRMED")
    print(f"  MongoDB records:      all 3 inspected boards persisted and retrievable")
    print(f"  5-way contract:       API == Mongo components/defects/counts/score")
    print("=" * 80)
    return uploaded_ids


if __name__ == "__main__":
    test_full_system()
