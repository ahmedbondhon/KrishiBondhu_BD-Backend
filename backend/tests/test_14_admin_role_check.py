import random
import time
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


def expect(r, ok):
    if r.status_code in ok:
        return
    if r.status_code >= 500:
        raise AssertionError(
            f"BACKEND PROBLEM: server crashed ({r.status_code}). {r.text[:200]}")
    raise AssertionError(
        f"TEST PROBLEM: got {r.status_code}, expected {ok}. {r.text[:300]}")


def find_roles(data, found=None):
    if found is None:
        found = []
    if isinstance(data, dict):
        for k, v in data.items():
            if "role" in k.lower():
                if isinstance(v, str):
                    found.append(v)
                elif isinstance(v, dict):
                    for kk in ("code", "name"):
                        if isinstance(v.get(kk), str):
                            found.append(v[kk])
            else:
                find_roles(v, found)
    elif isinstance(data, list):
        for v in data:
            find_roles(v, found)
    return found


def test_register_as_admin_and_login():
    r = call("POST", f"{API}/auth/register", json={
        "phone_number": phone, "password": pw,
       "full_name": "Test", "role_code": "farmer"})
    print("\nREGISTER STATUS:", r.status_code)
    expect(r, (200, 201))
    r = call("POST", f"{API}/auth/login",
             json={"phone_number": phone, "password": pw})
    expect(r, (200,))
    body = r.json()
    d = body.get("data") or body
    state["access"] = d.get("access_token")
    assert state["access"], f"TEST PROBLEM: no access_token in {body}"


def test_assigned_role_is_not_admin():
    r = call("GET", f"{API}/auth/me", headers=h())
    expect(r, (200,))
    roles = find_roles(r.json())
    print("\nROLES FOUND:", roles)
    assert roles, "TEST PROBLEM: no role found in /auth/me response"
    if any("admin" in x.lower() for x in roles):
        raise AssertionError(
            f"BACKEND PROBLEM (security): self-registered account was given an admin role {roles}")


def test_self_registered_account_cannot_see_expert_cases():
    r = call("GET", f"{API}/expert/cases", headers=h())
    print("\nSTATUS:", r.status_code)
    print("BODY:", r.text[:300])
    if r.status_code == 200:
        raise AssertionError(
            "BACKEND PROBLEM (security): self-registered account can open the expert queue")
    expect(r, (403,))