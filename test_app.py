import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8080"

def test_submit():
    print("Testing POST /api/applicants...")
    url = f"{BASE_URL}/api/applicants"
    payload = {
        "name": "Jane Doe",
        "income": 80000.0,
        "loan_amount": 20000.0,
        "credit_score": 750,
        "existing_monthly_debt": 500.0,
        "employment_status": "Employed",
        "notes": "Requesting loan for home renovation. No offshore assets.",
        "tenure": 5
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            app_id = res.get("id")
            assert app_id is not None, "Applicant ID missing"
            print(f"  -> SUCCESS. Created applicant ID: {app_id}")
            return app_id
    except Exception as e:
        print(f"  -> FAILED: {e}")
        sys.exit(1)

def test_list():
    print("Testing GET /api/applicants...")
    url = f"{BASE_URL}/api/applicants"
    try:
        with urllib.request.urlopen(url) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            assert isinstance(res, list), "List endpoint must return a list"
            assert len(res) > 0, "No applicants found in list"
            print(f"  -> SUCCESS. Mapped {len(res)} applicant records.")
    except Exception as e:
        print(f"  -> FAILED: {e}")
        sys.exit(1)

def test_details(app_id: int):
    print(f"Testing GET /api/applicants/{app_id}...")
    url = f"{BASE_URL}/api/applicants/{app_id}"
    try:
        with urllib.request.urlopen(url) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            assert res.get("name") == "Jane Doe", "Name mismatch"
            assert len(res.get("compliance_logs", [])) > 0, "Compliance logs missing"
            assert "audit_report" in res, "Audit report missing"
            assert res.get("audit_mode") in ("ai", "rule_based"), "Audit mode missing or invalid"
            print(f"  -> Audit mode: {res.get('audit_mode', 'unknown')}")
            print("  -> SUCCESS. Found compliance logs and audit reports.")
            print("  -> Report snippet:")
            snippet = "\n".join(res["audit_report"].split("\n")[:8]) + "\n..."
            try:
                print(snippet)
            except UnicodeEncodeError:
                print(snippet.encode('ascii', errors='replace').decode('ascii'))
    except Exception as e:
        print(f"  -> FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("           FinGuard-AI Verification Integration Test            ")
    print("=" * 60)
    app_id = test_submit()
    print("-" * 50)
    test_list()
    print("-" * 50)
    test_details(app_id)
    print("=" * 60)
    print("ALL API INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
