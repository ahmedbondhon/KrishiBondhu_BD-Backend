import random
import uuid
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
        f"TEST PROBLEM: got {r.status_code}, expected {ok}. {r.text[:300]}")


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


def test_show_fields():
    schema = get_spec()["components"]["schemas"]["CreateDiagnosisCaseRequest"]
    print("\nREQUIRED:", schema.get("required"))
    for name, p in schema.get("properties", {}).items():
        print(" -", name, ":", p.get("type") or p.get("anyOf") or p.get("$ref"),
              p.get("format", ""))


def test_create_case_invalid_crop_id():
    r = requests.post(f"{API}/diagnosis-cases",
                      json={"crop_id": "not-a-uuid"}, headers=h())
    print("\nSTATUS:", r.status_code)
    check(r, (400, 422))


def test_create_case_unknown_crop():
    r = requests.post(f"{API}/diagnosis-cases",
                      json={"crop_id": str(uuid.uuid4())}, headers=h())
    print("\nSTATUS:", r.status_code)
    print("BODY:", r.text[:500])
    check(r, (400, 404, 422))