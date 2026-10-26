import random
import requests
import pytest

BASE = "http://127.0.0.1:8000"
API = BASE + "/api/v1"


def get_schemas():
    for p in ("/api/v1/openapi.json", "/openapi.json"):
        r = requests.get(BASE + p)
        if r.status_code == 200:
            return r.json()["components"]["schemas"]
    return {}


SCHEMAS = get_schemas()


def fake(prop, name=""):
    if "$ref" in prop:
        return build(SCHEMAS[prop["$ref"].split("/")[-1]])
    for k in ("anyOf", "oneOf"):
        if k in prop:
            opts = [o for o in prop[k] if o.get("type") != "null"]
            return fake(opts[0], name) if opts else None
    if "enum" in prop:
        return prop["enum"][0]
    t, f = prop.get("type"), prop.get("format")
    n = name.lower()
    if t == "string":
        if f == "uuid":
            return "00000000-0000-0000-0000-000000000000"
        if f == "date":
            return "2026-10-01"
        if f == "date-time":
            return "2026-10-01T00:00:00Z"
        return "Test " + name
    if t == "number":
        if "lat" in n:
            return 23.8103
        if "lon" in n or "lng" in n:
            return 90.4125
        return 1.5
    if t == "integer":
        return 1
    if t == "boolean":
        return True
    if t == "array":
        return []
    if t == "object":
        return {}
    return None


def build(schema):
    props = schema.get("properties", {})
    return {k: fake(props[k], k) for k in schema.get("required", [])}


@pytest.fixture(scope="module")
def h():
    phone = "+8801" + random.choice("3456789") + "".join(random.choices("0123456789", k=8))
    requests.post(f"{API}/auth/register", json={
        "phone_number": phone, "password": "Test@12345",
        "full_name": "Farm Tester", "role_code": "farmer"})
    r = requests.post(f"{API}/auth/login",
                      json={"phone_number": phone, "password": "Test@12345"})
    assert r.status_code == 200, r.text
    b = r.json()
    d = b.get("data") or b
    return {"Authorization": f"Bearer {d['access_token']}"}


state = {}


def test_farms_without_token():
    assert requests.get(f"{API}/farms").status_code in (401, 403)


def test_farms_list_empty(h):
    r = requests.get(f"{API}/farms", headers=h)
    assert r.status_code == 200, r.text


def test_create_farm(h):
    payload = build(SCHEMAS["CreatePlotRequest"])
    payload["area_bigha"] = 2.5
    print("\nPAYLOAD:", payload)
    r = requests.post(f"{API}/farms", json=payload, headers=h)
    print("RESPONSE:", r.status_code, r.text[:500])
    assert r.status_code in (200, 201), r.text
    body = r.json()
    d = body.get("data") or body
    state["id"] = d.get("id")
    assert state["id"], body


def test_farm_in_list(h):
    r = requests.get(f"{API}/farms", headers=h)
    assert r.status_code == 200
    assert state["id"] in r.text