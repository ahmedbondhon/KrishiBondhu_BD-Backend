import random
import time

import requests

BASE = "http://127.0.0.1:8000"
API = BASE + "/api/v1"
PW = "Test@12345"
phone = "+8801" + random.choice("3456789") + "".join(random.choices("0123456789", k=8))
stranger = "+8801" + random.choice("3456789") + "".join(random.choices("0123456789", k=8))
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


def test_01_register_and_request_otp():
    r = requests.post(f"{API}/auth/register", json={
        "phone_number": phone, "password": PW,
        "full_name": "Otp Negative Tester", "role_code": "farmer"}, timeout=30)
    assert r.status_code == 201, r.text
    r = requests.post(f"{API}/auth/login/otp-request",
                      json={"phone_number": phone}, timeout=30)
    assert r.status_code == 200, r.text
    state["otp"] = read_otp(phone)


def test_02_wrong_otp_rejected():
    assert state.get("otp"), "test_01 must pass first"
    wrong = "000000" if state["otp"] != "000000" else "111111"
    r = requests.post(f"{API}/auth/login/otp-verify", json={
        "phone_number": phone, "otp_code": wrong}, timeout=30)
    print("\nWRONG OTP:", r.status_code, r.text[:200])
    assert r.status_code in (400, 401), r.text
    assert find_key(r.json(), "access_token") is None, r.text


def test_03_unrequested_phone_cannot_login_with_otp():
    r = requests.post(f"{API}/auth/login/otp-verify", json={
        "phone_number": stranger, "otp_code": "123456"}, timeout=30)
    print("\nSTRANGER:", r.status_code, r.text[:200])
    assert r.status_code != 200, r.text
    assert find_key(r.json(), "access_token") is None, r.text


def test_04_too_many_wrong_otps_blocks_correct_otp():
    assert state.get("otp"), "test_01 must pass first"
    wrong = "000000" if state["otp"] != "000000" else "111111"
    statuses = []
    for _ in range(8):
        r = requests.post(f"{API}/auth/login/otp-verify", json={
            "phone_number": phone, "otp_code": wrong}, timeout=30)
        statuses.append(r.status_code)
        if r.status_code not in (400, 401):
            break
    print("\nWRONG ATTEMPT STATUSES:", statuses)
    r = requests.post(f"{API}/auth/login/otp-verify", json={
        "phone_number": phone, "otp_code": state["otp"]}, timeout=30)
    print("CORRECT OTP AFTER ATTEMPTS:", r.status_code, r.text[:200])
    assert r.status_code != 200, r.text
    assert find_key(r.json(), "access_token") is None, r.text
