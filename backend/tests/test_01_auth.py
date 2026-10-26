import random
import requests

BASE = "http://127.0.0.1:8000"
API = BASE + "/api/v1"

phone = "+8801" + random.choice("3456789") + "".join(random.choices("0123456789", k=8))
pw = "Test@12345"
state = {}


def test_health():
    assert requests.get(f"{BASE}/health").status_code == 200


def test_register():
    r = requests.post(f"{API}/auth/register", json={
        "phone_number": phone, "password": pw,
        "full_name": "Test Farmer", "role_code": "farmer"})
    assert r.status_code == 201, r.text


def test_register_duplicate_rejected():
    r = requests.post(f"{API}/auth/register", json={
        "phone_number": phone, "password": pw,
        "full_name": "Test Farmer", "role_code": "farmer"})
    assert r.status_code in (400, 409, 422), r.text


def test_login_wrong_password():
    r = requests.post(f"{API}/auth/login",
                      json={"phone_number": phone, "password": "wrong"})
    assert r.status_code == 401


def test_login_success():
    r = requests.post(f"{API}/auth/login",
                      json={"phone_number": phone, "password": pw})
    assert r.status_code == 200, r.text
    body = r.json()
    d = body.get("data") or body
    state["access"] = d.get("access_token")
    state["refresh"] = d.get("refresh_token")
    assert state["access"], f"access_token নেই: {body}"


def test_me_without_token():
    assert requests.get(f"{API}/auth/me").status_code in (401, 403)


def test_me_with_token():
    h = {"Authorization": f"Bearer {state['access']}"}
    r = requests.get(f"{API}/auth/me", headers=h)
    assert r.status_code == 200, r.text


def test_refresh_token():
    if not state.get("refresh"):
        return
    r = requests.post(f"{API}/auth/refresh",
                      json={"refresh_token": state["refresh"]})
    assert r.status_code == 200, r.text