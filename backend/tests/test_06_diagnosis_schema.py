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


def get_spec():
    for url in (f"{API}/openapi.json", f"{BASE}/openapi.json"):
        try:
            data = requests.get(url).json()
        except Exception:
            continue
        if "paths" in data:
            print("\nOPENAPI URL:", url)
            return data
    raise AssertionError("openapi.json পাওয়া যায়নি")


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


def test_show_create_case_schema():
    spec = get_spec()
    path = next(p for p in spec["paths"]
                if p.endswith("/diagnosis-cases") and "post" in spec["paths"][p])
    op = spec["paths"][path]["post"]
    ref = op["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    name = ref.split("/")[-1]
    print("\nSCHEMA NAME:", name)
    print(json.dumps(spec["components"]["schemas"][name], indent=2)[:1800])


def test_create_case_empty_payload():
    r = requests.post(f"{API}/diagnosis-cases", json={}, headers=h())
    print("\nSTATUS:", r.status_code)
    print("BODY:", r.text[:800])
    assert r.status_code in (400, 422), r.text