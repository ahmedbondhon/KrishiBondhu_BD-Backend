import random
import requests

BASE = "http://127.0.0.1:8000"
API = BASE + "/api/v1"

phone = "+8801" + random.choice("3456789") + "".join(random.choices("0123456789", k=8))
pw = "Test@12345"
state = {}


def h():
    return {"Authorization": f"Bearer {state['access']}"}


def test_register_and_login():
    r = requests.post(f"{API}/auth/register", json={
        "phone_number": phone, "password": pw,
        "full_name": "Test Farmer", "role_code": "farmer"})
    assert r.status_code == 201, r.text
    r = requests.post(f"{API}/auth/login",
                      json={"phone_number": phone, "password": pw})
    assert r.status_code == 200, r.text
    body = r.json()
    d = body.get("data") or body
    state["access"] = d.get("access_token")
    assert state["access"], f"access_token নেই: {body}"


def test_diagnosis_without_token():
    r = requests.get(f"{API}/diagnosis-cases")
    assert r.status_code in (401, 403)


def test_list_diagnosis_cases():
    r = requests.get(f"{API}/diagnosis-cases", headers=h())
    assert r.status_code == 200, r.text