import asyncio
import random
import re
import time

import requests
from sqlalchemy import text

from app.db.session import engine

BASE = "http://127.0.0.1:8000"
API = BASE + "/api/v1"

suffix = "".join(random.choices("0123456789", k=8))
phone = "+8801" + random.choice("3456789") + suffix
email = f"expert{suffix}@test.example.com"
pw = "Test@12345"
state = {}


def get_otp(ph):
    last = ""
    for _ in range(10):
        r = requests.get(f"{BASE}/demo/sms-inbox", params={"phone": ph}, timeout=10)
        assert r.status_code == 200, r.text[:200]
        last = r.text
        m = re.search(r'otp_code"\s*:\s*"?(\d{4,10})', r.text) or re.search(r"\b(\d{6})\b", r.text)
        if m:
            return m.group(1)
        time.sleep(1)
    assert False, last


def find_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            found = find_key(v, key)
            if found:
                return found
    if isinstance(obj, list):
        for v in obj:
            found = find_key(v, key)
            if found:
                return found
    return None


async def _activate(ph):
    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text("UPDATE auth.users SET status = 'active', is_active = true WHERE phone_number = :p"),
                {"p": ph},
            )
            return result.rowcount
    finally:
        await engine.dispose()


def activate_user(ph):
    return asyncio.run(_activate(ph))


def test_01_expert_register_and_activate():
    r = requests.post(f"{API}/auth/request-otp",
                      json={"phone_number": phone, "purpose": "registration"})
    print("\nOTP REQUEST:", r.status_code, r.text[:300])
    assert r.status_code in (200, 201), r.text
    code = get_otp(phone)
    r = requests.post(f"{API}/auth/verify-otp", json={
        "phone_number": phone, "otp_code": code, "purpose": "registration"})
    assert r.status_code == 200, r.text
    token = find_key(r.json(), "verification_token")
    assert token, r.text
    r = requests.post(f"{API}/auth/register/expert", json={
        "phone_number": phone, "verification_token": token,
        "password": pw, "full_name": "Test Expert", "email": email,
        "specialization": "Plant Pathology",
        "credentials": "PhD in Agriculture"})
    assert r.status_code == 201, r.text
    assert activate_user(phone) == 1
    state["ready"] = True


def test_02_expert_login():
    assert state.get("ready"), "test_01 must pass first"
    r = requests.post(f"{API}/auth/login",
                      json={"phone_number": phone, "password": pw})
    assert r.status_code == 200, r.text
    token = find_key(r.json(), "access_token")
    assert token, r.text
    state["token"] = token


def test_03_expert_sees_queue():
    assert state.get("token"), "test_02 must pass first"
    r = requests.get(f"{API}/expert/cases",
                     headers={"Authorization": f"Bearer {state['token']}"})
    assert r.status_code == 200, r.text


def test_04_queue_shape():
    assert state.get("token"), "test_02 must pass first"
    r = requests.get(f"{API}/expert/cases",
                     headers={"Authorization": f"Bearer {state['token']}"})
    assert r.status_code == 200, r.text
    print("\nQUEUE:", r.text[:900])


def test_05_expert_submits_review():
    assert state.get("token"), "test_02 must pass first"
    headers = {"Authorization": f"Bearer {state['token']}"}
    r = requests.get(f"{API}/expert/cases", headers=headers)
    assert r.status_code == 200, r.text
    cases = r.json()["data"]
    assert cases, "queue is empty"
    case_id = cases[0]["id"]
    r = requests.post(f"{API}/expert/cases/{case_id}/review", headers=headers, json={
        "agreed_with_ai": True,
        "diagnosis_notes_bn": "পর্যবেক্ষণ সঠিক আছে এবং যাচাই করা হয়েছে",
        "prescribed_treatment_bn": "নিয়মিত পর্যবেক্ষণ করুন"})
    print("\nREVIEW:", r.status_code, r.text[:500])
    assert r.status_code == 201, r.text
    data = find_key(r.json(), "review_id")
    assert data, r.text
    assert find_key(r.json(), "case_id") == case_id, r.text


from uuid import uuid4


def expert_headers():
    assert state.get("token"), "test_02 must pass first"
    return {"Authorization": f"Bearer {state['token']}"}


def first_case_id():
    r = requests.get(f"{API}/expert/cases", headers=expert_headers())
    assert r.status_code == 200, r.text
    cases = r.json()["data"]
    assert cases, "queue is empty"
    return cases[0]["id"]


def test_06_disagree_without_issue_rejected():
    case_id = first_case_id()
    r = requests.post(f"{API}/expert/cases/{case_id}/review", headers=expert_headers(), json={
        "agreed_with_ai": False,
        "diagnosis_notes_bn": "পর্যবেক্ষণ সঠিক নয় এবং যাচাই করা হয়েছে"})
    assert r.status_code == 422, r.text


def test_07_short_notes_rejected():
    case_id = first_case_id()
    r = requests.post(f"{API}/expert/cases/{case_id}/review", headers=expert_headers(), json={
        "agreed_with_ai": True,
        "diagnosis_notes_bn": "ঠিক"})
    assert r.status_code == 422, r.text


def test_08_unknown_case_rejected():
    r = requests.post(f"{API}/expert/cases/{uuid4()}/review", headers=expert_headers(), json={
        "agreed_with_ai": True,
        "diagnosis_notes_bn": "পর্যবেক্ষণ সঠিক আছে এবং যাচাই করা হয়েছে"})
    assert r.status_code == 404, r.text


def test_09_reviewed_case_leaves_queue():
    r = requests.get(f"{API}/expert/cases", headers=expert_headers())
    assert r.status_code == 200, r.text
    numbers = [c["case_number"] for c in r.json()["data"]]
    print("QUEUE NUMBERS:", numbers)
    assert "KB-2026-000015" not in numbers, "reviewed case still in queue"


def test_10_duplicate_review_rejected():
    r = requests.post(f"{API}/expert/cases/6b7369ad-82ce-4fd2-8f77-0c5ec2dfbb3d/review", headers=expert_headers(), json={
        "agreed_with_ai": True,
        "diagnosis_notes_bn": "পর্যবেক্ষণ সঠিক আছে এবং যাচাই করা হয়েছে"})
    print("DUPLICATE:", r.status_code, r.text)
    assert r.status_code in (400, 409, 422), r.text


def test_11_reviewed_case_status_is_expert_reviewed():
    r = requests.get(f"{API}/expert/cases?status_filter=expert_reviewed", headers=expert_headers())
    print("REVIEWED LIST:", r.status_code, r.text[:600])
    assert r.status_code == 200, r.text
    items = {c["case_number"]: c["status"] for c in r.json()["data"]}
    assert "KB-2026-000015" in items, "reviewed case not in expert_reviewed list"
    assert items["KB-2026-000015"] == "expert_reviewed", items


POOL = ("KB-2026-000015", "KB-2026-000016", "KB-2026-000017", "KB-2026-000018")


def escalate_one(exclude=None):
    async def _run():
        try:
            async with engine.begin() as conn:
                r = await conn.execute(text(
                    "SELECT id FROM case_mgmt.diagnosis_cases "
                    "WHERE case_number IN :nums AND (CAST(:ex AS text) IS NULL OR id::text <> :ex) "
                    "ORDER BY (status = 'escalated') DESC LIMIT 1"
                ).bindparams(__import__("sqlalchemy").bindparam("nums", expanding=True)),
                    {"nums": list(POOL), "ex": exclude})
                row = r.first()
                assert row, "no pool case available"
                cid = str(row[0])
                await conn.execute(text(
                    "UPDATE case_mgmt.diagnosis_cases SET status = 'escalated', assigned_expert_id = NULL "
                    "WHERE id::text = :i"), {"i": cid})
                return cid
        finally:
            await engine.dispose()
    return asyncio.run(_run())


def first_case_id():
    return escalate_one(exclude=state.get("case_id"))


def test_05_expert_submits_review():
    case_id = escalate_one()
    r = requests.post(f"{API}/expert/cases/{case_id}/review", headers=expert_headers(), json={
        "agreed_with_ai": True,
        "diagnosis_notes_bn": "পর্যবেক্ষণ সঠিক আছে এবং যাচাই করা হয়েছে",
        "prescribed_treatment_bn": "নিয়মিত পর্যবেক্ষণ করুন"})
    print("\nREVIEW:", r.status_code, r.text[:500])
    assert r.status_code == 201, r.text
    assert find_key(r.json(), "review_id"), r.text
    assert find_key(r.json(), "case_id") == case_id, r.text
    state["case_id"] = case_id


def test_09_reviewed_case_leaves_queue():
    r = requests.get(f"{API}/expert/cases", headers=expert_headers())
    assert r.status_code == 200, r.text
    ids = [c["id"] for c in r.json()["data"]]
    assert state["case_id"] not in ids, "reviewed case still in queue"


def test_10_duplicate_review_rejected():
    r = requests.post(f"{API}/expert/cases/{state['case_id']}/review", headers=expert_headers(), json={
        "agreed_with_ai": True,
        "diagnosis_notes_bn": "পর্যবেক্ষণ সঠিক আছে এবং যাচাই করা হয়েছে"})
    print("DUPLICATE:", r.status_code, r.text[:300])
    assert r.status_code in (400, 409, 422), r.text


def test_11_reviewed_case_status_is_expert_reviewed():
    r = requests.get(f"{API}/expert/cases?status_filter=expert_reviewed", headers=expert_headers())
    assert r.status_code == 200, r.text
    items = {c["id"]: c["status"] for c in r.json()["data"]}
    assert state["case_id"] in items, "reviewed case not in expert_reviewed list"
    assert items[state["case_id"]] == "expert_reviewed", items


CROP_ID = "50000000-0000-0000-0000-000000000001"


def _register_farmer():
    ph = "+8801" + random.choice("3456789") + "".join(random.choices("0123456789", k=8))
    r = requests.post(f"{API}/auth/request-otp", json={"phone_number": ph, "purpose": "registration"})
    assert r.status_code in (200, 201), r.text
    code = get_otp(ph)
    r = requests.post(f"{API}/auth/verify-otp", json={"phone_number": ph, "otp_code": code, "purpose": "registration"})
    assert r.status_code == 200, r.text
    vt = find_key(r.json(), "verification_token")
    assert vt, r.text
    r = requests.post(f"{API}/auth/register/farmer-agent", json={
        "phone_number": ph, "verification_token": vt, "password": "123456",
        "full_name": "Test Farmer", "role": "farmer"})
    assert r.status_code == 201, r.text
    assert activate_user(ph) == 1
    r = requests.post(f"{API}/auth/login", json={"phone_number": ph, "password": "123456"})
    assert r.status_code == 200, r.text
    tok = find_key(r.json(), "access_token")
    assert tok, r.text
    return {"Authorization": f"Bearer {tok}"}


def test_12_farmer_sees_expert_review():
    fh = _register_farmer()
    r = requests.post(f"{API}/diagnosis-cases", headers=fh, json={"crop_id": CROP_ID, "farmer_notes": "test case"})
    print("\nCREATE:", r.status_code, r.text[:300])
    assert r.status_code == 201, r.text
    cid = find_key(r.json(), "case_id")
    before = requests.get(f"{API}/diagnosis-cases/{cid}", headers=fh).json()
    async def _esc():
        try:
            async with engine.begin() as conn:
                await conn.execute(text("UPDATE case_mgmt.diagnosis_cases SET status='escalated', assigned_expert_id=NULL WHERE id::text=:i"), {"i": cid})
        finally:
            await engine.dispose()
    asyncio.run(_esc())
    r = requests.post(f"{API}/expert/cases/{cid}/review", headers=expert_headers(), json={
        "agreed_with_ai": True,
        "diagnosis_notes_bn": "পর্যবেক্ষণ সঠিক আছে এবং যাচাই করা হয়েছে"})
    assert r.status_code == 201, r.text
    after = requests.get(f"{API}/diagnosis-cases/{cid}", headers=fh)
    print("AFTER:", after.status_code, after.text[:700])
    assert after.status_code == 200, after.text
    d = after.json()["data"]
    assert d["status"] == "expert_reviewed", d["status"]
    assert len(d["expert_reviews"]) == 1, d
    assert d["expert_reviews"][0]["agreed_with_ai"] is True
    b = before["data"]
    assert d.get("confidence_score") == b.get("confidence_score"), "AI result changed"
    assert d.get("top_predictions") == b.get("top_predictions"), "AI predictions changed"
    state["farmer_h"] = fh
    state["farmer_case"] = cid


def test_13_other_farmer_forbidden():
    assert state.get("farmer_case"), "test_12 must pass first"
    other = _register_farmer()
    r = requests.get(f"{API}/diagnosis-cases/{state['farmer_case']}", headers=other)
    print("\nOTHER FARMER:", r.status_code, r.text[:200])
    assert r.status_code == 403, r.text
