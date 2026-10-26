import random
import re
import requests

BASE = "http://127.0.0.1:8000"
API = BASE + "/api/v1"

suffix = "".join(random.choices("0123456789", k=8))
phone = "+8801" + random.choice("3456789") + suffix
email = f"expert{suffix}@test.example.com"
pw = "Test@12345"
state = {}


def get_otp(ph):
    r = requests.get(f"{BASE}/demo/sms-inbox", params={"phone": ph}, timeout=10)
    assert r.status_code == 200, f"TEST PROBLEM: inbox {r.status_code} {r.text[:200]}"
    m = re.search(r'otp_code"\s*:\s*"?(\d{4,10})', r.text) or re.search(r"\b(\d{6})\b", r.text)
    assert m, f"TEST PROBLEM: OTP পাওয়া যায়নি. inbox: {r.text[:300]}"
    return m.group(1)


def test_expert_register_pending_approval():
    r = requests.post(f"{API}/auth/request-otp",
                      json={"phone_number": phone, "purpose": "registration"})
    assert r.status_code in (200, 201), r.text
    code = get_otp(phone)

    r = requests.post(f"{API}/auth/verify-otp", json={
        "phone_number": phone, "otp_code": code, "purpose": "registration"})
    assert r.status_code == 200, r.text
    body = r.json()
    token = (body.get("data") or body).get("verification_token")
    assert token, f"verification_token নেই: {body}"

    r = requests.post(f"{API}/auth/register/expert", json={
        "phone_number": phone, "verification_token": token,
        "password": pw, "full_name": "Test Expert", "email": email,
        "specialization": "Plant Pathology",
        "credentials": "PhD in Agriculture"})
    assert r.status_code == 201, r.text
    d = r.json()
    d = d.get("data") or d
    assert d.get("status") == "pending_approval", d
    state["registered"] = True


def test_pending_expert_cannot_login():
    assert state.get("registered"), "TEST PROBLEM: আগের ধাপ ব্যর্থ"
    r = requests.post(f"{API}/auth/login",
                      json={"phone_number": phone, "password": pw})
    if r.status_code == 200:
        raise AssertionError(
            "BACKEND PROBLEM (security): অনুমোদনহীন এক্সপার্ট লগইন করতে পেরেছে")
    assert r.status_code in (401, 403), f"TEST PROBLEM: {r.status_code} {r.text[:200]}"