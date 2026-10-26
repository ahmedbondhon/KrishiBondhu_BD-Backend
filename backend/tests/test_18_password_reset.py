import random
import re
import time

import requests

BASE = "http://127.0.0.1:8000"
API = BASE + "/api/v1"
OLD_PW = "Test@12345"
NEW_PW = "482915"
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
        found = re.findall(r"\b\d{6}\b", r.text)
        if found:
            return found[0]
        time.sleep(1)
    assert False, last


def login(password):
    return requests.post(f"{API}/auth/login",
                         json={"phone_number": phone, "password": password}, timeout=30)


def test_01_register_and_login_with_old_password():
    r = requests.post(f"{API}/auth/register", json={
        "phone_number": phone, "password": OLD_PW,
        "full_name": "Reset Tester", "role_code": "farmer"}, timeout=30)
    assert r.status_code == 201, r.text
    r = login(OLD_PW)
    assert r.status_code == 200, r.text
    state["registered"] = True


def test_02_forgot_password_sends_otp():
    assert state.get("registered"), "test_01 must pass first"
    r = requests.post(f"{API}/auth/password/forgot",
                      json={"phone_number": phone}, timeout=30)
    print("\nFORGOT:", r.status_code, r.text[:300])
    assert r.status_code == 200, r.text
    state["otp"] = read_otp(phone)
    assert state["otp"]


def test_03_reset_password_with_otp():
    assert state.get("otp"), "test_02 must pass first"
    r = requests.post(f"{API}/auth/password/reset", json={
        "phone_number": phone, "otp_code": state["otp"],
        "new_password": NEW_PW}, timeout=30)
    print("\nRESET:", r.status_code, r.text[:300])
    assert r.status_code == 200, r.text
    state["reset_done"] = True


def test_04_old_password_no_longer_works():
    assert state.get("reset_done"), "test_03 must pass first"
    r = login(OLD_PW)
    assert r.status_code in (400, 401), r.text


def test_05_new_password_works():
    assert state.get("reset_done"), "test_03 must pass first"
    r = login(NEW_PW)
    assert r.status_code == 200, r.text
    assert find_key(r.json(), "access_token"), r.text
