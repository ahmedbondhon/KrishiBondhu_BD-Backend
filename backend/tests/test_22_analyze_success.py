"""
test_22: আসল পাতার ছবি দিয়ে পুরো পথ যাচাই।
ছবি আপলোড -> কেস তৈরি -> কেসে ছবি যোগ -> analyze -> advisory (রোগের পরামর্শ) আসা -> ফিডব্যাক

ছবি রাখুন: backend\\tests\\assets\\  (jpg/jpeg/png)
চালানোর কমান্ড: python -m pytest tests/test_22_analyze_success.py -s -v
"""
import json
import random
from pathlib import Path

import httpx
import pytest

BASE = "http://127.0.0.1:8000"
API = BASE + "/api/v1"
PW = "Test@12345"

ASSETS = Path(__file__).parent / "assets"
MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
IMAGES = sorted(p for p in ASSETS.glob("*") if p.suffix.lower() in MIME) if ASSETS.exists() else []


def call(method, path, token=None, **kw):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.request(method, API + path, headers=headers, timeout=120, **kw)


def first_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = first_key(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = first_key(v, key)
            if r is not None:
                return r
    return None


def register_and_login():
    phone = "+8801" + random.choice("3456789") + "".join(random.choices("0123456789", k=8))
    r = call("POST", "/auth/register", json={"phone_number": phone, "password": PW,
                                              "full_name": "Analyze Tester", "role_code": "farmer"})
    assert r.status_code == 201, r.text
    r = call("POST", "/auth/login", json={"phone_number": phone, "password": PW})
    assert r.status_code == 200, r.text
    token = first_key(r.json(), "access_token")
    assert token, r.text
    return token


def find_crop_id(token):
    r = call("GET", "/catalog/crops", token)
    assert r.status_code == 200, r.text
    cid = first_key(r.json(), "id")
    assert cid, "crop_id পাওয়া যায়নি: " + r.text[:300]
    return cid


def test_00_images_exist():
    assert IMAGES, f"কোনো ছবি নেই। ছবি রাখুন: {ASSETS}"


@pytest.mark.parametrize("img", IMAGES, ids=[p.name for p in IMAGES])
def test_full_analyze_flow(img):
    data = img.read_bytes()
    mime = MIME[img.suffix.lower()]
    print(f"\n=== ছবি: {img.name} ({len(data)} bytes) ===")

    token = register_and_login()
    crop_id = find_crop_id(token)

    # ১. আপলোড URL
    r = call("POST", "/files/upload-url", token,
             json={"original_name": img.name, "mime_type": mime, "file_size_bytes": len(data)})
    assert r.status_code in (200, 201), "upload-url: " + r.text
    upload_url = first_key(r.json(), "upload_url")
    storage_path = first_key(r.json(), "storage_path")
    assert upload_url and storage_path, r.text

    # ২. ছবি আপলোড
    pr = httpx.put(upload_url, content=data, headers={"Content-Type": mime}, timeout=120)
    assert pr.status_code < 300, f"আপলোড ফেল: {pr.status_code} {pr.text[:300]}"

    # ৩. আপলোড নিশ্চিত
    r = call("POST", "/files/confirm-upload", token,
             json={"storage_path": storage_path, "original_name": img.name,
                   "mime_type": mime, "file_size_bytes": len(data)})
    assert r.status_code in (200, 201), "confirm-upload: " + r.text
    file_id = first_key(r.json(), "file_id") or first_key(r.json(), "id")
    assert file_id, r.text

    # ৪. কেস তৈরি ও ছবি যোগ
    r = call("POST", "/diagnosis-cases", token, json={"crop_id": crop_id})
    assert r.status_code in (200, 201), "create case: " + r.text
    case_id = first_key(r.json(), "case_id") or first_key(r.json(), "id")
    assert case_id, r.text

    r = call("POST", f"/diagnosis-cases/{case_id}/images", token,
             json={"file_id": file_id, "is_primary": True})
    assert r.status_code in (200, 201), "add image: " + r.text

    # ৫. analyze
    r = call("POST", f"/diagnosis-cases/{case_id}/analyze", token)
    print("ANALYZE STATUS:", r.status_code)
    print("ANALYZE RESPONSE:", r.text[:700])
    assert r.status_code in (200, 201, 202), "analyze: " + r.text
    advisory = first_key(r.json(), "advisory")
    assert advisory, "analyze সফল, কিন্তু advisory (রোগের পরামর্শ) আসেনি: " + r.text[:500]

    # ৬. ফিডব্যাক
    r = call("POST", f"/diagnosis-cases/{case_id}/feedback", token,
             json={"rating": 5, "is_helpful": True, "feedback_text": "ঠিক আছে"})
    print("FEEDBACK:", r.status_code, r.text[:200])
    assert r.status_code in (200, 201), "feedback: " + r.text
