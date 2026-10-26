import json
import random
import requests

BASE = "http://127.0.0.1:8000"
API = BASE + "/api/v1"

phone = "+8801" + random.choice("3456789") + "".join(random.choices("0123456789", k=8))
pw = "Test@12345"
state = {}


def h():
    return {"Authorization": f"Bearer {state['access']}"}


def check(r, ok):
    if r.status_code in ok:
        return
    if r.status_code >= 500:
        raise AssertionError(
            f"BACKEND PROBLEM: server crashed ({r.status_code}). {r.text[:200]}")
    raise AssertionError(
        f"TEST PROBLEM: got {r.status_code}, expected {ok}. {r.text[:200]}")


def get_spec():
    for url in (f"{API}/openapi.json", f"{BASE}/openapi.json"):
        try:
            data = requests.get(url).json()
        except Exception:
            continue
        if "paths" in data:
            return data
    raise AssertionError("TEST PROBLEM: openapi.json not found")


def test_register_and_login():
    r = requests.post(f"{API}/auth/register", json={
        "phone_number": phone, "password": pw,
        "full_name": "Test Farmer", "role_code": "farmer"})
    check(r, (201,))
    r = requests.post(f"{API}/auth/login",
                      json={"phone_number": phone, "password": pw})
    check(r, (200,))
    body = r.json()
    d = body.get("data") or body
    state["access"] = d.get("access_token")
    assert state["access"], f"TEST PROBLEM: no access_token in {body}"


def test_profile_without_token():
    r = requests.post(f"{API}/auth/me/profile", json={})
    check(r, (401, 403))


def test_show_profile_schema():
    spec = get_spec()
    path = next(p for p in spec["paths"] if p.endswith("/auth/me/profile"))
    op = spec["paths"][path]["post"]
    ref = op["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    name = ref.split("/")[-1]
    schema = spec["components"]["schemas"][name]
    print("\nSCHEMA NAME:", name)
    print("REQUIRED:", schema.get("required"))
    print(json.dumps(schema.get("properties", {}), indent=2)[:1500])


def test_profile_empty_payload():
    r = requests.post(f"{API}/auth/me/profile", json={}, headers=h())
    print("\nSTATUS:", r.status_code)
    print("BODY:", r.text[:600])
    check(r, (200, 400, 422))