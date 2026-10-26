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
    """ফেল হলে বলে দেবে সমস্যা ব্যাকএন্ডে নাকি টেস্টে।"""
    if r.status_code in ok:
        return
    if r.status_code >= 500:
        raise AssertionError(
            f"BACKEND PROBLEM: সার্ভার ক্র্যাশ করেছে ({r.status_code}). {r.text[:200]}")
    raise AssertionError(
        f"TEST PROBLEM (সম্ভবত ভুল payload/URL): পেয়েছি {r.status_code}, "
        f"চেয়েছিলাম {ok}. {r.text[:200]}")


def find_key(data, part):
    """JSON-এর ভেতর যে key-তে `part` শব্দ আছে তার মান খোঁজে।"""
    if isinstance(data, dict):
        for k, v in data.items():
            if part in k.lower() and isinstance(v, str):
                return v
        for v in data.values():
            x = find_key(v, part)
            if x:
                return x
    return None


GOOD = {
    "original_name": "leaf.jpg",
    "mime_type": "image/jpeg",
    "file_size_bytes": 123456,
}


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
    assert state["access"], f"TEST PROBLEM: access_token নেই: {body}"


def test_upload_url_valid_request():
    r = requests.post(f"{API}/files/upload-url", json=GOOD, headers=h())
    print("\nSTATUS:", r.status_code)
    print("BODY:", r.text[:600])
    check(r, (200, 201))
    state["upload_url"] = find_key(r.json(), "url")
    assert state["upload_url"], f"BACKEND PROBLEM: রেসপন্সে URL নেই: {r.text[:300]}"


def test_upload_url_bad_mime_type_rejected():
    bad = dict(GOOD, mime_type="application/x-msdownload", original_name="virus.exe")
    r = requests.post(f"{API}/files/upload-url", json=bad, headers=h())
    print("\nSTATUS:", r.status_code)
    check(r, (400, 415, 422))


def test_upload_url_zero_size_rejected():
    bad = dict(GOOD, file_size_bytes=0)
    r = requests.post(f"{API}/files/upload-url", json=bad, headers=h())
    print("\nSTATUS:", r.status_code)
    check(r, (400, 422))


def test_upload_url_huge_file_rejected():
    bad = dict(GOOD, file_size_bytes=10_000_000_000)  # ~10 GB
    r = requests.post(f"{API}/files/upload-url", json=bad, headers=h())
    print("\nSTATUS:", r.status_code)
    check(r, (400, 413, 422))
