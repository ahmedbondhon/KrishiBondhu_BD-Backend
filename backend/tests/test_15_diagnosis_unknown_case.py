import random
import time
import uuid
import requests

BASE = "http://127.0.0.1:8000"
API = BASE + "/api/v1"

phone = "+8801" + random.choice("3456789") + "".join(random.choices("0123456789", k=8))
pw = "Test@12345"
state = {}


def h():
    return {"Authorization": f"Bearer {state['access']}"}


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
            f"BACKEND PROBLEM: server accepted an unknown case ({r.status_code}). {r.text[:200]}")
    raise AssertionError(
        f"TEST PROBLEM: got {r.status_code}, expected {ok}. {r.text[:200]}")


def test_register_and_login():
    r = call("POST", f"{API}/auth/register", json={
        "phone_number": phone, "password": pw,
        "full_name": "Test Farmer", "role_code": "farmer"})
    expect_rejected(r, (201,))
    r = call("POST", f"{API}/auth/login",
             json={"phone_number": phone, "password": pw})
    expect_rejected(r, (200,))
    body = r.json()
    d = body.get("data") or body
    state["access"] = d.get("access_token")
    assert state["access"], f"TEST PROBLEM: no access_token in {body}"


def test_endpoints_need_token():
    cid = uuid.uuid4()
    calls = [
        ("GET", f"{API}/diagnosis-cases/{cid}"),
        ("POST", f"{API}/diagnosis-cases/{cid}/images"),
        ("POST", f"{API}/diagnosis-cases/{cid}/analyze"),
        ("POST", f"{API}/diagnosis-cases/{cid}/feedback"),
    ]
    for method, url in calls:
        r = call(method, url, json={})
        print("\n", method, url.replace(API, ""), "->", r.status_code)
        expect_rejected(r, (401, 403))


def test_get_unknown_case():
    r = call("GET", f"{API}/diagnosis-cases/{uuid.uuid4()}", headers=h())
    print("\nSTATUS:", r.status_code)
    print("BODY:", r.text[:300])
    expect_rejected(r, (404, 422))


def test_get_invalid_case_id():
    r = call("GET", f"{API}/diagnosis-cases/not-a-uuid", headers=h())
    print("\nSTATUS:", r.status_code)
    expect_rejected(r, (400, 404, 422))


def test_analyze_unknown_case():
    r = call("POST", f"{API}/diagnosis-cases/{uuid.uuid4()}/analyze",
             json={}, headers=h())
    print("\nSTATUS:", r.status_code)
    print("BODY:", r.text[:300])
    expect_rejected(r, (404, 422))


def test_add_image_unknown_case():
    r = call("POST", f"{API}/diagnosis-cases/{uuid.uuid4()}/images",
             json={}, headers=h())
    print("\nSTATUS:", r.status_code)
    print("BODY:", r.text[:300])
    expect_rejected(r, (404, 422))


def test_feedback_unknown_case():
    r = call("POST", f"{API}/diagnosis-cases/{uuid.uuid4()}/feedback",
             json={}, headers=h())
    print("\nSTATUS:", r.status_code)
    print("BODY:", r.text[:300])
    expect_rejected(r, (404, 422))