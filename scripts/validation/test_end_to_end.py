"""
Test end-to-end pipeline with real data flow: upload -> AI -> database -> analytics.

This validates that the complete inspection pipeline works with real data
flowing through all components without mock data.
"""

import os
import time
import requests
import json

BACKEND_URL = "http://localhost:5000"
TEST_IMAGE = "datasets/defects/test/images/00041200.jpg"

print("=" * 80)
print("END-TO-END PIPELINE VALIDATION")
print("=" * 80)
print(f"Backend URL: {BACKEND_URL}")
print(f"Test image: {TEST_IMAGE}")
print()

# Test 1: System health check
print("Test 1: System health check")
try:
    response = requests.get(f"{BACKEND_URL}/api/system-status", timeout=10)
    if response.status_code == 200:
        status = response.json()
        print("PASS System status:")
        print(f"  Express: {status['express']}")
        print(f"  MongoDB: {status['mongodb']}")
        print(f"  AI Engine: {status['ai_engine']}")
    else:
        print(f"FAIL Health check failed: {response.status_code}")
except Exception as e:
    print(f"FAIL Health check error: {e}")

print()

# Test 2: Upload and inspect real PCB image
print("Test 2: Upload and inspect real PCB image")
if os.path.exists(TEST_IMAGE):
    try:
        # First, register a test user (or use existing)
        auth_response = requests.post(f"{BACKEND_URL}/api/auth/register", json={
            "name": "Test Engineer",
            "email": "test@smartpcb-xai.local",
            "password": "test123",
            "role": "ENGINEER"
        }, timeout=10)
        
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            token = auth_data["token"]
            print(f"PASS Authenticated as: {auth_data['user']['name']}")
        else:
            print("FAIL Auth failed, trying demo login")
            demo_response = requests.post(f"{BACKEND_URL}/api/auth/demo", timeout=10)
            if demo_response.status_code == 200:
                demo_data = demo_response.json()
                token = demo_data["token"]
                print(f"PASS Demo login successful")
            else:
                print("FAIL All auth methods failed")
                token = None
        
        if token:
            # Upload and inspect
            print(f"Uploading {TEST_IMAGE}...")
            with open(TEST_IMAGE, "rb") as f:
                files = {"image": (os.path.basename(TEST_IMAGE), f, "image/jpeg")}
                data = {
                    "confidence_threshold": 0.25,
                    "pcb_id": "TEST-PCB-001"
                }
                headers = {"Authorization": f"Bearer {token}"}
                
                start_time = time.time()
                upload_response = requests.post(
                    f"{BACKEND_URL}/api/inspection/upload",
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=120  # 2 minute timeout for inference
                )
                upload_time = time.time() - start_time
            
            if upload_response.status_code == 200:
                result = upload_response.json()
                print(f"PASS Inspection completed in {upload_time:.2f}s")
                print(f"  Inspection ID: {result.get('inspection_id')}")
                print(f"  Status: {result.get('inspection_status')}")
                print(f"  Components: {result.get('component_count')}")
                print(f"  Defects: {result.get('defect_count')}")
                print(f"  Quality Score: {result.get('quality_score', {}).get('overall_score')}")
                
                # Test 3: Verify data was stored in MongoDB
                print()
                print("Test 3: Verify data stored in MongoDB")
                inspection_id = result.get('inspection_id')
                if inspection_id:
                    get_response = requests.get(
                        f"{BACKEND_URL}/api/inspection/{inspection_id}",
                        headers=headers,
                        timeout=10
                    )
                    if get_response.status_code == 200:
                        stored_data = get_response.json()
                        print(f"PASS Retrieved from MongoDB:")
                        print(f"  Components: {len(stored_data.get('components', []))}")
                        print(f"  Defects: {len(stored_data.get('defects', []))}")
                        print(f"  Quality score: {stored_data.get('quality_score', {}).get('overall_score')}")
                    else:
                        print(f"FAIL Failed to retrieve from MongoDB: {get_response.status_code}")
                
                # Test 4: Analytics with real data
                print()
                print("Test 4: Analytics with real MongoDB data")
                analytics_response = requests.get(
                    f"{BACKEND_URL}/api/analytics",
                    headers=headers,
                    timeout=10
                )
                if analytics_response.status_code == 200:
                    analytics = analytics_response.json()
                    print(f"PASS Analytics from real data:")
                    print(f"  Total inspections: {analytics.get('total_inspections')}")
                    print(f"  Pass count: {analytics.get('pass_count')}")
                    print(f"  Fail count: {analytics.get('fail_count')}")
                    print(f"  Average quality: {analytics.get('average_quality_score')}")
                    print(f"  Defect distribution: {analytics.get('defect_distribution')}")
                else:
                    print(f"FAIL Analytics failed: {analytics_response.status_code}")
                
                # Test 5: Model evaluation artifacts
                print()
                print("Test 5: Model evaluation artifacts")
                eval_response = requests.get(
                    f"{BACKEND_URL}/api/model-evaluation",
                    timeout=10
                )
                if eval_response.status_code == 200:
                    eval_data = eval_response.json()
                    print(f"PASS Model evaluation artifacts available:")
                    for key, artifact in eval_data.get('artifacts', {}).items():
                        if artifact.get('available'):
                            print(f"  {key}: YES (modified: {artifact.get('modified_at')})")
                        else:
                            print(f"  {key}: NO ({artifact.get('reason')})")
                else:
                    print(f"FAIL Model evaluation failed: {eval_response.status_code}")
                
            else:
                print(f"FAIL Upload failed: {upload_response.status_code}")
                print(f"  Error: {upload_response.text}")
        
    except Exception as e:
        print(f"FAIL Upload/inference error: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"FAIL Test image not found: {TEST_IMAGE}")

print()
print("=" * 80)
print("END-TO-END VALIDATION COMPLETE")
print("=" * 80)