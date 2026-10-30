import os
import sys
import time
import threading
import uvicorn
import httpx as requests

# Ensure unbuffered output
sys.stdout.reconfigure(line_buffering=True)

from app.main import app
from app.database.session import Base, engine
from app.models import *

def run_server():
    try:
        config = uvicorn.Config(
            app=app,
            host="127.0.0.1",
            port=8001,
            log_level="error",
        )
        server = uvicorn.Server(config)
        server.install_signal_handlers = lambda: None
        server.run()
    except Exception as e:
        print(f"[!] Server exception: {e}", flush=True)

def run_checks():
    print("[1] Starting background Uvicorn test server on port 8001...", flush=True)
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    base_url = "http://127.0.0.1:8001"
    for i in range(15):
        try:
            r = requests.get(f"{base_url}/health", timeout=1)
            if r.status_code == 200:
                print(f"[2] Server is UP! Health check response: {r.json()}", flush=True)
                break
        except Exception:
            time.sleep(0.5)
    else:
        print("[!] Server failed to respond in time", flush=True)
        sys.exit(1)

    # 1. Test Patient Registration
    print("[3] Testing Patient Registration API...", flush=True)
    patient_payload = {
        "email": f"testpatient_{int(time.time())}@example.com",
        "password": "StrongPassword123!",
        "full_name": "Aarav Sharma",
        "date_of_birth": "1995-04-12",
        "gender": "Male",
        "phone": "+91 9876543210",
        "blood_group": "B+",
    }
    reg_res = requests.post(f"{base_url}/api/v1/auth/register/patient", json=patient_payload)
    print(f"    Status: {reg_res.status_code}", flush=True)
    assert reg_res.status_code == 201, f"Expected 201, got {reg_res.text}"
    token_data = reg_res.json()
    token = token_data["access_token"]
    print(f"    Registered successfully! Token received for: {token_data['email']}, Role: {token_data['role']}", flush=True)

    # 2. Test Doctor Registration
    print("[4] Testing Doctor Registration API...", flush=True)
    doctor_payload = {
        "email": f"testdoc_{int(time.time())}@hospital.org",
        "password": "DocSecurePassword123!",
        "full_name": "Dr. Priya Patel",
        "specialization": "Cardiologist",
        "license_number": f"MED-{int(time.time())}",
        "hospital": "Apex Heart Institute",
    }
    doc_res = requests.post(f"{base_url}/api/v1/auth/register/doctor", json=doctor_payload)
    print(f"    Status: {doc_res.status_code}", flush=True)
    assert doc_res.status_code == 201, f"Expected 201, got {doc_res.text}"
    doc_token = doc_res.json()["access_token"]
    print(f"    Doctor registered successfully! Role: {doc_res.json()['role']}", flush=True)

    # 3. Test Login
    print("[5] Testing Patient Login...", flush=True)
    login_res = requests.post(
        f"{base_url}/api/v1/auth/login",
        json={"email": patient_payload["email"], "password": patient_payload["password"]},
    )
    assert login_res.status_code == 200
    print("    Login successful! JWT verified.", flush=True)

    # 4. Test Authenticated Profile Route (/auth/me)
    print("[6] Testing /auth/me with Bearer token...", flush=True)
    headers = {"Authorization": f"Bearer {token}"}
    me_res = requests.get(f"{base_url}/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    print(f"    Identity verified: {me_data['email']}, Name: {me_data['patient_profile']['full_name']}", flush=True)

    # 5. Test Role-Based Protection
    print("[7] Testing Role Guard (Patient attempting Doctor-only profile)...", flush=True)
    doc_profile_res = requests.get(f"{base_url}/api/v1/users/profile/doctor", headers=headers)
    assert doc_profile_res.status_code == 403
    print(f"    Correctly Forbidden (403): {doc_profile_res.json()['detail']}", flush=True)

    # 6. Test Doctor Accessing Doctor Profile
    print("[8] Testing Doctor accessing Doctor profile...", flush=True)
    doc_headers = {"Authorization": f"Bearer {doc_token}"}
    doc_p_res = requests.get(f"{base_url}/api/v1/users/profile/doctor", headers=doc_headers)
    assert doc_p_res.status_code == 200
    print(f"    Doctor authorized! Specialization: {doc_p_res.json()['specialization']}", flush=True)

    print("\n>>> ALL PHASE 1 INTEGRATION TESTS PASSED 100% SUCCESSFULLY! <<<", flush=True)

if __name__ == "__main__":
    run_checks()
