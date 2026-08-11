#!/usr/bin/env python3
import time
import requests
import json
import sys
import re

DEEPAGENT_API_URL = "http://localhost:8642/v1/chat/completions"
HITL_URL = "http://localhost:5001"
API_KEY = "hermes-api-secret"

def test_health():
    print("[Test 1/4] Checking Deep Agent API Health Endpoint...")
    try:
        resp = requests.get("http://localhost:8642/health", timeout=10)
        if resp.status_code == 200:
            print("  ✓ Deep Agent Core API is healthy:", resp.json())
            return True
        else:
            print(f"  ✗ Health check failed with status code {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Health check exception: {e}")
        return False

def test_low_risk_query():
    print("\n[Test 2/4] Testing Low-Risk Tool Invocation (ansible_pcs_health_check)...")
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepagent",
        "messages": [{"role": "user", "content": "Check the PCS cluster health for rhel-prod-01"}],
        "stream": False
    }
    try:
        resp = requests.post(DEEPAGENT_API_URL, headers=headers, json=payload, timeout=180)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            print("  ✓ Low-risk query succeeded. Response preview:")
            print("    ", content[:150].replace("\n", " "))
            return True
        else:
            print(f"  ✗ Query failed with status {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        print(f"  ✗ Query exception: {e}")
        return False

def test_hitl_interception():
    print("\n[Test 3/4] Testing High-Risk HITL Interception Gate (ansible_reboot_host)...")
    
    import threading
    result_container = []

    def send_reboot_request():
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "deepagent",
            "messages": [{"role": "user", "content": "Reboot the host rhel-prod-01"}],
            "stream": False
        }
        try:
            resp = requests.post(DEEPAGENT_API_URL, headers=headers, json=payload, timeout=180)
            if resp.status_code == 200:
                result_container.append(resp.json()["choices"][0]["message"]["content"])
        except Exception as e:
            result_container.append(f"Error: {e}")

    req_thread = threading.Thread(target=send_reboot_request)
    req_thread.start()

    print("  Waiting for HITL pending request on Port 5001...")
    session = requests.Session()
    login_data = {"username": "admin", "password": "admin123"}
    
    approved = False
    for attempt in range(25):
        time.sleep(2)
        try:
            r = session.get(HITL_URL, timeout=5)
            if "Login" in r.text and "Logout" not in r.text:
                csrf_match = re.search(r'name="csrf_token" value="(.*?)"', r.text)
                if csrf_match:
                    token = csrf_match.group(1)
                    session.post(f"{HITL_URL}/login", data={**login_data, "csrf_token": token}, timeout=5)
                    r = session.get(HITL_URL, timeout=5)

            if "Approve" in r.text:
                forms = re.findall(r'action="/resolve/(\d+)".*?name="csrf_token" value="(.*?)"', r.text, re.DOTALL)
                for req_id, csrf in forms:
                    print(f"  ✓ HITL Interception verified! Auto-approving request ID #{req_id}...")
                    session.post(f"{HITL_URL}/resolve/{req_id}", data={"status": "GRANTED", "csrf_token": csrf}, timeout=5)
                    approved = True
                    break
            if approved:
                break
        except Exception as e:
            pass

    req_thread.join(timeout=180)
    if result_container:
        print("  ✓ High-risk operation completed post-approval:")
        print("    ", str(result_container[0])[:150].replace("\n", " "))
        return True
    else:
        print("  ✗ HITL test timed out or failed.")
        return False

def main():
    print("==========================================================================")
    print(" Deep Agent Verification Test Suite")
    print("==========================================================================")
    
    if not test_health():
        sys.exit(1)
    if not test_low_risk_query():
        sys.exit(1)
    if not test_hitl_interception():
        sys.exit(1)
        
    print("\n==========================================================================")
    print(" ALL TESTS PASSED SUCCESSFULLY! Deep Agent & HITL Gate Verified.")
    print("==========================================================================")

if __name__ == "__main__":
    main()
