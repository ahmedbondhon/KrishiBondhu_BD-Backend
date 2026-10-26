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


def test_read_without_token():
    r = requests.post(f"{API}/notifications/{uuid.uuid4()}/read")
    check(r, (401, 403))


def test_read_invalid_id():
    r = requests.post(f"{API}/notifications/not-a-uuid/read", headers=h())
    print("\nSTATUS:", r.status_code)
    check(r, (400, 404, 422))


def test_read_unknown_id():
    r = requests.post(f"{API}/notifications/{uuid.uuid4()}/read", headers=h())
    print("\nSTATUS:", r.status_code)
    print("BODY:", r.text[:400])
    check(r, (400, 404, 422))


def test_read_existing_notification_if_any():
    r = requests.get(f"{API}/notifications", headers=h())
    check(r, (200,))
    body = r.json()
    data = body.get("data") or body
    items = data.get("items") if isinstance(data, dict) else data
    if not items:
        print("\nNo notifications for this new user, skipping.")
        return
    nid = items[0].get("id")
    r = requests.post(f"{API}/notifications/{nid}/read", headers=h())
    check(r, (200, 204))