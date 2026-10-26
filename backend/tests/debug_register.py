import json
import random

import requests

URL = "http://127.0.0.1:8000/api/v1/auth/register"


def digits(n):
    return "".join(random.choice("0123456789") for _ in range(n))


tail = "17" + digits(8)
phones = [
    "0" + tail,
    "+880" + tail,
    "880" + tail,
]
passwords = ["Test@12345", "Password123!", "abc12345"]

for phone in phones:
    for pw in passwords:
        body = {"phone_number": phone, "password": pw, "full_name": "Test User"}
        r = requests.post(URL, json=body, timeout=15)
        print("PHONE:", phone, "| PW:", pw, "| STATUS:", r.status_code)
        if r.status_code >= 400:
            try:
                err = r.json().get("error", {}).get("details", r.json())
            except Exception:
                err = r.text[:300]
            print("   ", json.dumps(err, ensure_ascii=True)[:400])
        else:
            print("    OK! এই ফরম্যাটে কাজ করছে")