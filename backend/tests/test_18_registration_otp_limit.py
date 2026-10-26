import random
import re
import time

import requests

BASE = "http://127.0.0.1:8000"
API = BASE + "/api/v1"


def get_otp(ph):
    last = ""
    for _ in range(10):
        r = requests.get(f"{BASE}/demo/sms-inbox", params={"phone": ph}, timeout=10)
        last = r.text
        m = re.search(r'otp_code"\s*:\s*"?(\d{4,10})', r.text) or re.search(r"\b(\d{6})\b", r.text)
        if m:
            return m.group(1)
        time.sleep(1)
    assert False, last


def test_registration_otp_wrong_attempts_limit():
    ph = "+8801" + random.choice("3456789") + "".join(random.choices("0123456789", k=8))
    r = requests.post(f"{API}/auth/request-otp", json={"phone_number": ph, "purpose": "registration"})
    assert r.status_code in (200, 201), r.text
    code = get_otp(ph)
    wrong = "111111" if code != "111111" else "222222"
    statuses = []
    for _ in range(8):
        w = requests.post(f"{API}/auth/verify-otp", json={"phone_number": ph, "otp_code": wrong, "purpose": "registration"})
        statuses.append(w.status_code)
    print("\nWRONG STATUSES:", statuses)
    r = requests.post(f"{API}/auth/verify-otp", json={"phone_number": ph, "otp_code": code, "purpose": "registration"})
    print("CORRECT AFTER 8 WRONG:", r.status_code, r.text[:200])
    assert r.status_code != 200, "OTP still accepted after 8 wrong attempts (no limit)"
