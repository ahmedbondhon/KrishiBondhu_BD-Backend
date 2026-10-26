import random

import requests

BASE = "http://127.0.0.1:8000"
API = BASE + "/api/v1"
CROP_ID = "50000000-0000-0000-0000-000000000001"
PW = "Test@12345"
S = {}


def find_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            f = find_key(v, key)
            if f:
                return f
    if isinstance(obj, list):
        for v in obj:
            f = find_key(v, key)
            if f:
                return f
    return None


def new_farmer():
    ph = "+8801" + random.choice("3456789") + "".join(random.choices("0123456789", k=8))
    r = requests.post(f"{API}/auth/register", json={"phone_number": ph, "password": PW,
                      "full_name": "Test Farmer", "role_code": "farmer"})
    assert r.status_code == 201, r.text
    r = requests.post(f"{API}/auth/login", json={"phone_number": ph, "password": PW})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {find_key(r.json(), 'access_token')}"}


def url():
    return f"{API}/farms/{S['plot']}/crop-cycles/{S['cycle']}"


def test_00_setup():
    S["h"] = new_farmer()
    r = requests.post(f"{API}/farms", headers=S["h"], json={"name": "টেস্ট জমি", "area_bigha": 2.5})
    assert r.status_code in (200, 201), r.text
    S["plot"] = find_key(r.json(), "id")
    r = requests.post(f"{API}/farms/{S['plot']}/crop-cycles", headers=S["h"],
                      json={"crop_id": CROP_ID, "sowing_date": "2026-10-01"})
    assert r.status_code in (200, 201), r.text
    S["cycle"] = find_key(r.json(), "id")
    assert S["cycle"], r.text


def test_01_update_saves_changes():
    r = requests.patch(url(), headers=S["h"], json={
        "notes": "আপডেট করা নোট", "yield_kg": 120.5,
        "expected_harvest_date": "2027-01-15"})
    print("\nUPDATE:", r.status_code, r.text[:300])
    assert r.status_code == 200, r.text
    g = requests.get(f"{API}/farms/{S['plot']}/crop-cycles", headers=S["h"])
    assert g.status_code == 200, g.text
    c = [x for x in g.json()["data"] if x["id"] == S["cycle"]][0]
    print("SAVED:", c)
    assert c["notes"] == "আপডেট করা নোট", c
    assert float(c["yield_kg"]) == 120.5, c
    assert c["expected_harvest_date"] == "2027-01-15", c


def test_02_unknown_cycle_404():
    other = "00000000-0000-4000-8000-000000000001"
    r = requests.patch(f"{API}/farms/{S['plot']}/crop-cycles/{other}", headers=S["h"], json={"notes": "x"})
    print("\nUNKNOWN CYCLE:", r.status_code)
    assert r.status_code == 404, r.text


def test_03_wrong_growth_stage_400():
    r = requests.patch(url(), headers=S["h"], json={"current_stage_id": "00000000-0000-4000-8000-000000000002"})
    print("\nBAD STAGE:", r.status_code)
    assert r.status_code == 400, r.text


def test_04_other_farmer_cannot_update():
    other = new_farmer()
    r = requests.patch(url(), headers=other, json={"notes": "হ্যাক"})
    print("\nOTHER FARMER:", r.status_code)
    assert r.status_code in (403, 404), r.text
    g = requests.get(f"{API}/farms/{S['plot']}/crop-cycles", headers=S["h"])
    c = [x for x in g.json()["data"] if x["id"] == S["cycle"]][0]
    assert c["notes"] == "আপডেট করা নোট", "other farmer changed the cycle"


def test_05_negative_yield_rejected():
    r = requests.patch(url(), headers=S["h"], json={"yield_kg": -50})
    print("\nNEGATIVE YIELD:", r.status_code, r.text[:200])
    assert r.status_code in (400, 422), "negative yield accepted"


def test_06_bad_date_rejected():
    r = requests.patch(url(), headers=S["h"], json={"actual_harvest_date": "2026-13-45"})
    print("\nBAD DATE:", r.status_code)
    assert r.status_code == 422, r.text


def test_07_unknown_status_rejected():
    r = requests.patch(url(), headers=S["h"], json={"status": "xyz_invalid"})
    print("\nBAD STATUS:", r.status_code, r.text[:200])
    assert r.status_code in (400, 422), "unknown status accepted"


def test_08_requires_login():
    r = requests.patch(url(), json={"notes": "x"})
    print("\nNO LOGIN:", r.status_code)
    assert r.status_code in (401, 403), r.text
