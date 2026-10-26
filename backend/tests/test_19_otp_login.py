import random
import re
import time

import requests

BASE = "http://127.0.0.1:8000"
API = BASE + "/api/v1"
PW = "Test@12345"
phone = "+8801" + random.choice("3456789") + "".join(random.choices("0123456789", k=8))
state = {}


def find_key(obj, key):
    if isinstance(obj, dict):
        if key in obj and obj[key] is not None:
            return obj[key]
        for v in obj.values():
            found = find_key(v, key)
            if found is not None:
                return found
    if isinstance(obj, list):
        for v in obj:
            found = find_key(v, key)
            if found is not None:
                return found
    return None


def read_otp(ph):
    last = ""
    for _ in range(10):
        r = requests.get(f"{BASE}/demo/sms-inbox", params={"phone": ph}, timeout=10)
        assert r.status_code == 200, r.text[:200]
        last = r.text
        otp = find_key(r.json(), "latest_otp")
        if otp:
            return str(otp)
        time.sleep(1)
    assert False, last


def test_01_register_farmer():
    r = requests.post(f"{API}/auth/register", json={
        "phone_number": phone, "password": PW,
        "full_name": "Otp Login Tester", "role_code": "farmer"}, timeout=30)
    assert r.status_code == 201, r.text
    state["registered"] = True


def test_02_otp_login_request():
    assert state.get("registered"), "test_01 must pass first"
    r = requests.post(f"{API}/auth/login/otp-request",
                      json={"phone_number": phone}, timeout=30)
    print("\nOTP LOGIN REQUEST:", r.status_code, r.text[:300])
    assert r.status_code == 200, r.text
    state["otp"] = read_otp(phone)


def test_03_otp_login_verify():
    assert state.get("otp"), "test_02 must pass first"
    r = requests.post(f"{API}/auth/login/otp-verify", json={
        "phone_number": phone, "otp_code": state["otp"]}, timeout=30)
    print("\nOTP LOGIN VERIFY:", r.status_code, r.text[:200])
    assert r.status_code == 200, r.text
    token = find_key(r.json(), "access_token")
    assert token, r.text
    state["token"] = token


def test_04_token_from_otp_login_works():
    assert state.get("token"), "test_03 must pass first"
    r = requests.get(f"{API}/auth/me",
                     headers={"Authorization": f"Bearer {state['token']}"}, timeout=30)
    assert r.status_code == 200, r.text


def test_05_same_otp_cannot_be_reused():
    assert state.get("token"), "test_03 must pass first"
    r = requests.post(f"{API}/auth/login/otp-verify", json={
        "phone_number": phone, "otp_code": state["otp"]}, timeout=30)
    assert r.status_code in (400, 401), r.text
