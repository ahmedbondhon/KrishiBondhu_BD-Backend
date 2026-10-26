import pytest
import requests

BASE = "http://127.0.0.1:8000"

CANDIDATES = [
    "/openapi.json",
    "/api/v1/openapi.json",
    "/api/openapi.json",
    "/v1/openapi.json",
]


def load_spec():
    for p in CANDIDATES:
        try:
            data = requests.get(BASE + p, timeout=10).json()
            if isinstance(data, dict) and "paths" in data:
                print("OpenAPI found at", p)
                return data
        except Exception:
            pass
    return None


SPEC = load_spec()


def load_paths():
    gets, posts = [], []
    if not SPEC:
        return gets, posts
    for path, methods in SPEC["paths"].items():
        if "{" in path:          # id লাগে এমন path বাদ
            continue
        if "get" in methods:
            gets.append(path)
        if "post" in methods:
            posts.append(path)
    return gets, posts


GET_PATHS, POST_PATHS = load_paths()


def test_server_is_running():
    assert requests.get(f"{BASE}/health", timeout=10).status_code == 200


def test_openapi_found():
    assert SPEC is not None, "openapi.json পাওয়া যায়নি"


@pytest.mark.parametrize("path", GET_PATHS)
def test_get_does_not_crash(path):
    res = requests.get(BASE + path, timeout=15)
    # 401/403/422 ঠিক আছে (login বা ডেটা লাগে), কিন্তু 500 মানে বাগ
    assert res.status_code < 500, f"{path} -> {res.status_code}: {res.text[:200]}"


@pytest.mark.parametrize("path", POST_PATHS)
def test_post_empty_body_does_not_crash(path):
    res = requests.post(BASE + path, json={}, timeout=15)
    # খালি ডেটায় 422 আসা উচিত, 500 এলে বাগ
    assert res.status_code < 500, f"{path} -> {res.status_code}: {res.text[:200]}"