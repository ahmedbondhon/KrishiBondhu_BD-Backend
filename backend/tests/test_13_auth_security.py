import random
import time
import requests

BASE = "http://127.0.0.1:8000"
API = BASE + "/api/v1"


def new_phone():
    return "+8801" + random.choice("3456789") + "".join(random.choices("0123456789", k=8))


def call(method, url, **kw):
    for attempt in range(3):
        try:
            return requests.request(method, url, timeout=10, **kw)
        except requests.exceptions.ConnectionError:
            if attempt == 2:
                raise AssertionError(
                    "BACKEND PROBLEM: server not responding (connection reset 3 times)")
            time.sleep(1)


def expect_rejected(r, ok):
    if r.status_code in ok:
        return
    if r.status_code >= 500:
        raise AssertionError(
            f"BACKEND PROBLEM: server crashed ({r.status_code}). {r.text[:200]}")
    if r.status_code in (200, 201):
        raise AssertionError(
            f"BACKEND PROBLEM: server accepted invalid input ({r.status_code}). {r.text[:200]}")
    raise AssertionError(
        f"TEST PROBLEM: got {r.status_code}, expected {ok}. {r.text[:200]}")


def test_invalid_token_rejected():
    r = call("GET", f"{API}/auth/me",
             headers={"Authorization": "Bearer abc.def.ghi"})
    expect_rejected(r, (401, 403))


def test_malformed_auth_header_rejected():
    r = call("GET", f"{API}/auth/me",
             headers={"Authorization": "Token abc"})
    expect_rejected(r, (401, 403))


def test_refresh_with_garbage_token_rejected():
    r = call("POST", f"{API}/auth/refresh",
             json={"refresh_token": "garbage"})
    expect_rejected(r, (400, 401, 422))


def test_login_unknown_user_rejected():
    r = call("POST", f"{API}/auth/login",
             json={"phone_number": new_phone(), "password": "Test@12345"})
    expect_rejected(r, (401, 404))


def test_register_missing_fields_rejected():
    r = call("POST", f"{API}/auth/register", json={})
    expect_rejected(r, (400, 422))


def test_register_invalid_phone_rejected():
    r = call("POST", f"{API}/auth/register", json={
        "phone_number": "123", "password": "Test@12345",
        "full_name": "Test", "role_code": "farmer"})
    print("\nSTATUS:", r.status_code)
    expect_rejected(r, (400, 422))


def test_register_short_password_rejected():
    r = call("POST", f"{API}/auth/register", json={
        "phone_number": new_phone(), "password": "1",
        "full_name": "Test", "role_code": "farmer"})
    print("\nSTATUS:", r.status_code)
    expect_rejected(r, (400, 422))


def test_register_admin_role_rejected():
    r = call("POST", f"{API}/auth/register", json={
        "phone_number": new_phone(), "password": "Test@12345",
        "full_name": "Test", "role_code": "admin"})
    print("\nSTATUS:", r.status_code)
    assert r.status_code == 403, r.text
    assert r.json()["error"]["code"] == "ROLE_NOT_PERMITTED", r.text
    
    