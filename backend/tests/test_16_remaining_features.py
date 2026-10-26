import random
import httpx
import pytest

BASE = "http://127.0.0.1:8000"
API = BASE + "/api/v1"
PW = "Test@12345"
S = {}


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


def need(*keys):
    for k in keys:
        if S.get(k) is None:
            pytest.skip(f"আগের ধাপ ফেল করায় '{k}' নেই")


def H():
    return {"Authorization": f"Bearer {S['token']}"}


def call(method, path, **kw):
    return httpx.request(method, API + path, timeout=60, **kw)


def test_00_register_login():
    phone = "+8801" + random.choice("3456789") + "".join(random.choices("0123456789", k=8))
    r = call("POST", "/auth/register", json={"phone_number": phone, "password": PW,
                                              "full_name": "Test User", "role_code": "farmer"})
    assert r.status_code == 201, r.text
    r = call("POST", "/auth/login", json={"phone_number": phone, "password": PW})
    assert r.status_code == 200, r.text
    S["token"] = first_key(r.json(), "access_token")
    assert S["token"], r.text


def test_01_find_crop_id():
    need("token")
    spec = None
    for u in ("/openapi.json", "/api/v1/openapi.json"):
        r0 = httpx.get(BASE + u, timeout=30)
        if r0.status_code == 200 and "paths" in r0.json():
            spec = r0.json()
            break
    assert spec, "openapi.json পাওয়া যায়নি"
    paths = [p for p, v in spec["paths"].items()
             if "crop" in p.lower() and "get" in v and "{" not in p and "cycle" not in p.lower()]
    assert paths, "crop সংক্রান্ত কোনো GET পথ নেই"
    for p in paths:
        r = httpx.get(BASE + p, headers=H(), timeout=30)
        if r.status_code == 200:
            cid = first_key(r.json(), "id")
            if cid:
                S["crop_id"] = cid
                print("crop পথ:", p)
                return
    pytest.fail(f"crop_id মেলেনি, পরীক্ষিত পথ: {paths}")


def test_02_create_case():
    need("crop_id")
    r = call("POST", "/diagnosis-cases", headers=H(), json={"crop_id": S["crop_id"]})
    assert r.status_code in (200, 201), r.text
    S["case_id"] = first_key(r.json(), "case_id") or first_key(r.json(), "id")
    assert S["case_id"], r.text


def test_03_get_case():
    need("case_id")
    r = call("GET", f"/diagnosis-cases/{S['case_id']}", headers=H())
    assert r.status_code == 200, r.text


def test_04_upload_url():
    need("token")
    r = call("POST", "/files/upload-url", headers=H(),
             json={"original_name": "leaf.jpg", "mime_type": "image/jpeg", "file_size_bytes": 2048})
    assert r.status_code in (200, 201), r.text
    print("UPLOAD RESPONSE:", r.text)
    d = r.json()
    S["storage_path"] = first_key(d, "storage_path") or first_key(d, "path")
    S["upload_url"] = first_key(d, "upload_url")
    assert S["upload_url"] and S["storage_path"], r.text


def test_05_confirm_upload():
    need("storage_path", "upload_url")
   
    data = open(r"C:\Users\PONKHI\leaf.jpg", "rb").read()
    pr = httpx.put(S["upload_url"], content=data,
                   headers={"Content-Type": "image/jpeg"}, timeout=60)
    print("PUT raw:", pr.status_code, pr.text[:900])
    if pr.status_code >= 300:
        pr = httpx.put(S["upload_url"], files={"file": ("leaf.jpg", data, "image/jpeg")}, timeout=60)
        print("PUT multipart:", pr.status_code, pr.text[:900])
    r = call("POST", "/files/confirm-upload", headers=H(),
             json={"storage_path": S["storage_path"], "original_name": "leaf.jpg",
                   "mime_type": "image/jpeg", "file_size_bytes": len(data)})
    print("CONFIRM RESPONSE:", r.text)
    assert r.status_code in (200, 201), r.text
    S["file_id"] = first_key(r.json(), "file_id") or first_key(r.json(), "id")


def test_06_view_url():
    need("file_id")
    r = call("GET", f"/files/{S['file_id']}/view-url", headers=H())
    assert r.status_code == 200, r.text


def test_07_add_image():
    need("case_id", "file_id")
    r = call("POST", f"/diagnosis-cases/{S['case_id']}/images", headers=H(),
             
             json={"file_id": S["file_id"], "is_primary": True})
    
    
    assert r.status_code in (200, 201), r.text


def test_08_analyze():
    need("case_id", "file_id")
    r = call("POST", f"/diagnosis-cases/{S['case_id']}/analyze", headers=H())
    
    assert r.status_code in (200, 201, 202), r.text
    S["advisory"] = r.json().get("data", {}).get("advisory")


def test_09_feedback():
    need("case_id", "file_id")
    r = call("POST", f"/diagnosis-cases/{S['case_id']}/feedback", headers=H(),
             json={"rating": 5, "is_helpful": True, "feedback_text": "ঠিক আছে"})
    if S.get("advisory"):
      
      assert r.status_code in (200, 201), r.text
    else:
        assert r.status_code == 404, r.text
        assert r.json()["error"]["code"] == "ADVISORY_NOT_FOUND", r.text  


def test_10_notification_read():
    need("token")
    r = call("GET", "/notifications", headers=H())
    assert r.status_code == 200, r.text
    nid = first_key(r.json(), "id")
    if not nid:
        pytest.skip("এই ইউজারের কোনো নোটিফিকেশন নেই")
    r = call("POST", f"/notifications/{nid}/read", headers=H())
    assert r.status_code in (200, 204), r.text


def test_11_crop_cycles():
    need("token", "crop_id")
    r = call("POST", "/farms", headers=H(), json={"name": "টেস্ট জমি", "area_bigha": 2.5})
    assert r.status_code in (200, 201), r.text
    plot = first_key(r.json(), "id")
    r = call("POST", f"/farms/{plot}/crop-cycles", headers=H(),
             json={"crop_id": S["crop_id"], "sowing_date": "2026-10-01"})
    assert r.status_code in (200, 201), r.text
    r = call("GET", f"/farms/{plot}/crop-cycles", headers=H())
    assert r.status_code == 200, r.text
    
    
def test_expert_queue_forbidden_for_farmer():
    r = call("GET", "/expert/cases", headers=H())
    assert r.status_code == 403, r.text


def test_expert_queue_requires_login():
    r = call("GET", "/expert/cases")
    assert r.status_code == 401, r.text


def test_expert_review_forbidden_for_farmer():
    r = call("POST", "/expert/cases/00000000-0000-0000-0000-000000000000/review",
             headers=H(),
             json={"agreed_with_ai": True,
                   "diagnosis_notes_bn": "পর্যবেক্ষণ সঠিক আছে এবং যাচাই করা হয়েছে"})
    assert r.status_code == 403, r.text