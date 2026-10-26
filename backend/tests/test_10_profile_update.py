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


def deref(schema, spec):
    if "$ref" in schema:
        node = spec
        for part in schema["$ref"].split("/")[1:]:
            node = node[part]
        return deref(node, spec)
    for key in ("anyOf", "oneOf", "allOf"):
        if key in schema:
            opts = [s for s in schema[key] if s.get("type") != "null"]
            return deref(opts[0], spec)
    return schema


def build_profile_payload():
    """Only simple fields. UUID / *_id fields are skipped."""
    spec = get_spec()
    path = next(p for p in spec["paths"] if p.endswith("/auth/me/profile"))
    op = spec["paths"][path]["post"]
    schema = deref(op["requestBody"]["content"]["application/json"]["schema"], spec)
    payload = {}
    for name, p in schema.get("properties", {}).items():
        p = deref(p, spec)
        low = name.lower()
        if low.endswith("_id") or p.get("format") in ("uuid", "date", "date-time"):
            continue
        if "enum" in p:
            payload[name] = p["enum"][0]
        elif "lang" in low:
            payload[name] = "bn"
        elif low in ("lat", "latitude"):
            payload[name] = 23.8103
        elif low in ("lng", "lon", "longitude"):
            payload[name] = 90.4125
        elif p.get("type") == "string":
            payload[name] = "Dhaka"
        elif p.get("type") == "integer":
            payload[name] = 1
        elif p.get("type") == "number":
            payload[name] = 1.0
        elif p.get("type") == "boolean":
            payload[name] = True
    return payload


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


def test_update_profile():
    payload = build_profile_payload()
    print("\nPAYLOAD:", payload)
    r = requests.post(f"{API}/auth/me/profile", json=payload, headers=h())
    print("STATUS:", r.status_code)
    print("BODY:", r.text[:500])
    check(r, (200, 201))


def test_profile_unknown_division_rejected():
    r = requests.post(f"{API}/auth/me/profile",
                      json={"division_id": str(uuid.uuid4())}, headers=h())
    print("\nSTATUS:", r.status_code)
    print("BODY:", r.text[:400])
    check(r, (400, 404, 422))


def test_profile_invalid_uuid_rejected():
    r = requests.post(f"{API}/auth/me/profile",
                      json={"division_id": "not-a-uuid"}, headers=h())
    check(r, (400, 422))


def test_me_still_works_after_update():
    r = requests.get(f"{API}/auth/me", headers=h())
    check(r, (200,))