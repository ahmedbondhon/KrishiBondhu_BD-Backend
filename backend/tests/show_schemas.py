import requests

BASE = "http://127.0.0.1:8000"
spec = None
for p in ["/openapi.json", "/api/v1/openapi.json"]:
    try:
        data = requests.get(BASE + p, timeout=10).json()
        if "paths" in data:
            spec = data
            break
    except Exception:
        pass


def resolve(ref):
    node = spec
    for part in ref.lstrip("#/").split("/"):
        node = node[part]
    return node


for path in [
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/farms",
    "/api/v1/diagnosis-cases",
]:
    body = spec["paths"][path]["post"].get("requestBody", {})
    schema = body.get("content", {}).get("application/json", {}).get("schema", {})
    if "$ref" in schema:
        schema = resolve(schema["$ref"])
    print(path)
    print("  required:", schema.get("required"))
    print("  fields:", list(schema.get("properties", {}).keys()))