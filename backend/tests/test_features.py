import random

import pytest
import requests

BASE = "http://127.0.0.1:8000"
API = BASE + "/api/v1"
PASSWORD = "Test@12345"


def find_key(obj, key):
    """response-এর ভেতর যেকোনো জায়গা থেকে key খুঁজে বের করে"""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = find_key(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_key(v, key)
            if r is not None:
                return r
    return None


def new_phone():
    # সার্ভারের নিয়ম: +880 এর পর ঠিক ১০টা সংখ্যা
    return "+8801" + random.choice("3456789") + "".join(
        random.choice("0123456789") for _ in range(8)
    )


@pytest.fixture(scope="module")
def user():
    phone = new_phone()
    body = {"phone_number": phone, "password": PASSWORD, "full_name": "Test User"}
    reg = requests.post(f"{API}/auth/register", json=body, timeout=15)
    login = requests.post(
        f"{API}/auth/login",
        json={"phone_number": phone, "password": PASSWORD},
        timeout=15,
    )
    token = None
    try:
        token = find_key(login.json(), "access_token")
    except Exception:
        pass
    return {
        "phone": phone,
        "reg": reg,
        "login": login,
        "headers": {"Authorization": f"Bearer {token}"} if token else {},
    }


# ---------- AUTH ----------
def test_register_works(user):
    r = user["reg"]
    assert r.status_code in (200, 201), f"register -> {r.status_code}: {r.text[:300]}"


def test_login_gives_token(user):
    r = user["login"]
    assert r.status_code == 200, f"login -> {r.status_code}: {r.text[:300]}"
    assert user["headers"], f"access_token পাওয়া যায়নি: {r.text[:300]}"


def test_wrong_password_rejected(user):
    r = requests.post(
        f"{API}/auth/login",
        json={"phone_number": user["phone"], "password": "WrongPass@999"},
        timeout=15,
    )
    assert r.status_code in (400, 401, 403), f"ভুল পাসওয়ার্ডে -> {r.status_code}: {r.text[:200]}"


def test_duplicate_register_rejected(user):
    r = requests.post(
        f"{API}/auth/register",
        json={"phone_number": user["phone"], "password": PASSWORD, "full_name": "Dup"},
        timeout=15,
    )
    assert r.status_code in (400, 409, 422), f"একই নম্বরে দ্বিতীয়বার -> {r.status_code}: {r.text[:200]}"


def test_weak_password_rejected():
    r = requests.post(
        f"{API}/auth/register",
        json={"phone_number": new_phone(), "password": "1", "full_name": "Weak"},
        timeout=15,
    )
    assert r.status_code in (400, 422), f"১ অক্ষরের পাসওয়ার্ডে -> {r.status_code}: {r.text[:200]}"


def test_me_with_token(user):
    r = requests.get(f"{API}/auth/me", headers=user["headers"], timeout=15)
    assert r.status_code == 200, f"/auth/me -> {r.status_code}: {r.text[:200]}"


def test_me_without_token_blocked():
    r = requests.get(f"{API}/auth/me", timeout=15)
    assert r.status_code in (401, 403), f"token ছাড়া -> {r.status_code}"


# ---------- FARMS ----------
def test_create_and_list_farm(user):
    name = "Test Farm " + user["phone"][-4:]
    c = requests.post(
        f"{API}/farms",
        json={"name": name, "area_bigha": 2.5, "soil_type": "loam"},
        headers=user["headers"],
        timeout=15,
    )
    assert c.status_code in (200, 201), f"farm তৈরি -> {c.status_code}: {c.text[:300]}"
    lst = requests.get(f"{API}/farms", headers=user["headers"], timeout=15)
    assert lst.status_code == 200, f"farm তালিকা -> {lst.status_code}: {lst.text[:200]}"
    assert name in lst.text, "নতুন farm তালিকায় নেই"


def test_farm_requires_name(user):
    r = requests.post(f"{API}/farms", json={}, headers=user["headers"], timeout=15)
    assert r.status_code == 422, f"নাম ছাড়া farm -> {r.status_code}"


def test_farms_without_token_blocked():
    r = requests.get(f"{API}/farms", timeout=15)
    assert r.status_code in (401, 403), f"token ছাড়া farms -> {r.status_code}"


# ---------- DIAGNOSIS / NOTIFICATIONS ----------
def test_diagnosis_invalid_crop_not_crash(user):
    r = requests.post(
        f"{API}/diagnosis-cases",
        json={"crop_id": 999999999},
        headers=user["headers"],
        timeout=15,
    )
    assert r.status_code < 500, f"ভুল crop_id -> {r.status_code}: {r.text[:300]}"


def test_diagnosis_list(user):
    r = requests.get(f"{API}/diagnosis-cases", headers=user["headers"], timeout=15)
    assert r.status_code == 200, f"diagnosis তালিকা -> {r.status_code}: {r.text[:200]}"


def test_notifications_list(user):
    r = requests.get(f"{API}/notifications", headers=user["headers"], timeout=15)
    assert r.status_code == 200, f"notifications -> {r.status_code}: {r.text[:200]}"