import re

def _resolve_openapi_template_path(app, concrete_path: str) -> str | None:
    paths = app.openapi().get("paths", {}) or {}
    for tmpl in paths.keys():
        pattern = "^" + re.sub(r"\{[^/]+\}", r"[^/]+", tmpl) + "$"
        if re.match(pattern, concrete_path):
            return tmpl
    return None
def _openapi_paths(app):
    return set(app.openapi().get("paths", {}).keys())

def _dump_paths(app):
    for p in sorted(_openapi_paths(app)):
        print(p)


import json

def _deref(spec: dict, schema: dict) -> dict:
    """
    Recursively dereference $ref and normalize common combinators.
    Returns a schema dict.
    """
    if not isinstance(schema, dict):
        return schema
    seen = set()
    cur = schema
    while isinstance(cur, dict) and "$ref" in cur:
        ref = cur["$ref"]
        if ref in seen:
            break
        seen.add(ref)
        parts = ref.lstrip("#/" ).split("/")
        node = spec
        for p in parts:
            node = node[p]
        # merge overlay keys (rare but legal)
        overlay = {k: v for k, v in cur.items() if k != "$ref"}
        cur = dict(node)
        cur.update(overlay)

    # Normalize allOf (merge object shapes)
    if isinstance(cur, dict) and "allOf" in cur and isinstance(cur["allOf"], list):
        merged = {"type": "object", "properties": {}, "required": []}
        for part in cur["allOf"]:
            part = _deref(spec, part)
            if not isinstance(part, dict):
                continue
            if part.get("type") == "object":
                merged["properties"].update(part.get("properties") or {})
                merged["required"].extend(part.get("required") or [])
        # overlay any direct props too
        merged["properties"].update(cur.get("properties") or {})
        merged["required"].extend(cur.get("required") or [])
        merged["required"] = sorted(set(merged["required"]))
        cur = merged

    # If anyOf/oneOf exist, pick the first branch deterministically
    for k in ("oneOf", "anyOf"):
        if isinstance(cur, dict) and k in cur and isinstance(cur[k], list) and cur[k]:
            base = {kk: vv for kk, vv in cur.items() if kk not in (k,)}
            chosen = _deref(spec, cur[k][0])
            if isinstance(chosen, dict):
                base.update(chosen)
            cur = base

    return cur

def _schema_instance(spec: dict, schema: dict):
    """
    Create a minimal *valid* instance for a JSON Schema-like OpenAPI schema,
    recursively satisfying required fields.
    """
    schema = _deref(spec, schema or {})
    if not isinstance(schema, dict):
        return "TEST"

    # enums
    if "enum" in schema and isinstance(schema["enum"], list) and schema["enum"]:
        return schema["enum"][0]

    t = schema.get("type")

    # handle "nullable" by still returning a concrete value (better for validation)
    fmt = schema.get("format")

    if t == "string" or t is None:
        if fmt == "uuid":
            return "00000000-0000-0000-0000-000000000000"
        if fmt in ("date-time", "datetime"):
            return "2026-01-01T00:00:00Z"
        if fmt == "date":
            return "2026-01-01"
        return "TEST"

    if t == "integer":
        return 1
    if t == "number":
        return 1.0
    if t == "boolean":
        return False

    if t == "array":
        items = schema.get("items") or {}
        min_items = schema.get("minItems") or 0
        if min_items and min_items > 0:
            return [_schema_instance(spec, items)]
        # still safer to return one element for many validators, but keep minimal:
        return []

    if t == "object":
        props = schema.get("properties") or {}
        required = schema.get("required") or []
        out = {}
        for k in required:
            out[k] = _schema_instance(spec, props.get(k, {}))
        return out

    # fallback
    return "TEST"

def _minimal_json_for_path(app, path: str, method: str) -> dict:
    spec = app.openapi()
    op = spec["paths"].get(path, {}).get(method.lower(), {}) or {}
    req = op.get("requestBody", {}) or {}
    content = req.get("content", {}) or {}
    app_json = content.get("application/json")
    if not app_json:
        return {}
    schema = app_json.get("schema", {}) or {}
    inst = _schema_instance(spec, schema)
    return inst if isinstance(inst, dict) else {}

def _multipart_fields_for_path(app, tmpl: str, method: str):
    spec = app.openapi()
    op = spec["paths"][tmpl][method.lower()]
    content = (op.get("requestBody", {}) or {}).get("content", {}) or {}
    form = content.get("multipart/form-data", {}) or {}
    schema = _deref(spec, (form.get("schema") or {}))

    props = schema.get("properties") or {}
    # deref each prop (important!)
    props = {k: _deref(spec, v or {}) for k, v in props.items()}
    required = set(schema.get("required") or [])

    # find binary file field(s)
    file_fields = []
    for k, v in props.items():
        vt = v.get("type")
        if (vt == "string" and v.get("format") == "binary") or v.get("format") == "binary":
            file_fields.append((k, v))
        elif vt == "array" and v.get("items", {}).get("type") == "string" and v.get("items", {}).get("format") == "binary":
            file_fields.append((k, v))

    png_1x1 = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00"
        b"\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x0cIDAT"
        b"\x08\xd7c\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00"
        b"\x18\xdd\x8d\x18"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    files = {}
    data = {}
    for k, v in file_fields:
        if v.get("type") == "array":
            # array of files: use list of tuples
            files = [(k, ("test.png", png_1x1, "image/png"))]
        else:
            files[k] = ("test.png", png_1x1, "image/png")

    for k in required:
        if any(k == ff[0] for ff in file_fields):
            continue
        v = props.get(k, {})
        vt = v.get("type")
        if vt in ("object", "array"):
            data[k] = json.dumps(_schema_instance(spec, v))
        elif vt == "integer":
            data[k] = "1"
        elif vt == "number":
            data[k] = "1"
        elif vt == "boolean":
            data[k] = "false"
        else:
            data[k] = "TEST"

    return files, data

def _expects_multipart(app, path: str, method: str) -> bool:
    spec = app.openapi()
    op = spec["paths"].get(path, {}).get(method.lower(), {})
    content = op.get("requestBody", {}).get("content", {})
    return "multipart/form-data" in content
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.models.config import get_settings
SETTINGS = get_settings()
DEMO_TOKEN = SETTINGS.demo_password
ADMIN_TOKEN = SETTINGS.admin_password

app = create_app()
import inspect
print("APP FILE:", inspect.getfile(create_app))

# DEBUG (remove after audit)
print("\n=== ROUTES (API) ===")
for r in app.routes:
    path = getattr(r, "path", "")
    methods = sorted(getattr(r, "methods", []) or [])
    if path.startswith("/api/"):
        print(methods, path, type(r).__name__)
print("=== END ROUTES ===\n")

# DEBUG (remove after audit)
from fastapi.routing import APIRoute
def _dump_route_deps(path: str, method: str):
    for r in app.routes:
        if isinstance(r, APIRoute) and r.path == path and method in (r.methods or set()):
            calls = [d.call for d in r.dependant.dependencies]
            print(f"\n=== DEPS for {method} {path} ===")
            for c in calls:
                print(" -", getattr(c, "__name__", repr(c)), c)
            print("=== END DEPS ===\n")
            return
    print(f"\nNOT FOUND: {method} {path}\n")

_dump_route_deps("/api/proposals/generate", "POST")
_dump_route_deps("/api/transcribe/upload", "POST")
_dump_route_deps("/api/history/list", "GET")
_dump_route_deps("/api/book/list", "GET")
_dump_route_deps("/api/admin-saves/invoice/{invoice_id}", "PUT")  # adjust if your template differs

# DEBUG (remove after audit)
print("\n=== ROUTES (API) ===")
for r in app.routes:
    path = getattr(r, "path", "")
    methods = sorted(getattr(r, "methods", []) or [])
    if path.startswith("/api/"):
        print(methods, path, type(r).__name__)
print("=== END ROUTES ===\n")

# DEBUG (remove after audit)
from fastapi.routing import APIRoute
def _dump_route_deps(path: str, method: str):
    for r in app.routes:
        if isinstance(r, APIRoute) and r.path == path and method in (r.methods or set()):
            calls = [d.call for d in r.dependant.dependencies]
            print(f"\n=== DEPS for {method} {path} ===")
            for c in calls:
                print(" -", getattr(c, "__name__", repr(c)), c)
            print("=== END DEPS ===\n")
            return
    print(f"\nNOT FOUND: {method} {path}\n")

_dump_route_deps("/api/proposals/generate", "POST")
_dump_route_deps("/api/transcribe/upload", "POST")
_dump_route_deps("/api/history/list", "GET")
_dump_route_deps("/api/book/list", "GET")
_dump_route_deps("/api/admin-saves/invoice/{invoice_id}", "PUT")  # adjust if your template differs
client = TestClient(app)

# List of (method, path, requires_admin)
PROTECTED_ENDPOINTS = [
    ("POST", "/api/transcribe/upload", False),
    ("POST", "/api/proposals/generate", False),
    ("POST", "/api/proposals/export/testsession", False),
    ("GET", "/api/proposals/download/testsession", False),
    ("GET", "/api/history/list", True),
    ("GET", "/api/history/testsession", True),
    ("DELETE", "/api/history/testsession", True),
    ("POST", "/api/book/upload", False),
    ("GET", "/api/book/list", True),
    ("GET", "/api/book/download/testchapter", False),
    ("DELETE", "/api/book/testchapter", True),
    ("GET", "/api/admin-saves/invoice/testid", False),
    ("PUT", "/api/admin-saves/invoice/testid", False),
]

@pytest.mark.parametrize("method,path,requires_admin", PROTECTED_ENDPOINTS)
def test_auth_required(method, path, requires_admin):
    tmpl = _resolve_openapi_template_path(app, path)
    assert tmpl is not None, f"Auth test URL not mounted: {path}"

    # Prepare request
    payload_kwargs = {}
    if method == "POST" and _expects_multipart(app, tmpl, method):
        files, data = _multipart_fields_for_path(app, tmpl, method)
        payload_kwargs = {"files": files, "data": data}
    elif method in ("POST", "PUT", "PATCH"):
        payload_kwargs = {"json": _minimal_json_for_path(app, tmpl, method)}

    if requires_admin:
        # No token
        resp = client.request(method, path, **payload_kwargs)
        assert resp.status_code == 401, f"{method} {path} should require auth"
        # User token (non-admin)
        resp2 = client.request(method, path, headers={"Authorization": f"Bearer {DEMO_TOKEN}"}, **payload_kwargs)
        assert resp2.status_code == 403, f"{method} {path} should require admin token"
        # Admin token
        resp3 = client.request(method, path, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}, **payload_kwargs)
        assert resp3.status_code != 401, f"{method} {path} should accept admin token"
    else:
        resp = client.request(method, path, **payload_kwargs)
        assert resp.status_code == 401, f"{method} {path} should require auth"
        # Invalid token
        resp2 = client.request(method, path, headers={"Authorization": "Bearer invalid"}, **payload_kwargs)
        assert resp2.status_code == 401, f"{method} {path} should reject invalid token"
        # Valid token (demo)
        resp3 = client.request(method, path, headers={"Authorization": f"Bearer {DEMO_TOKEN}"}, **payload_kwargs)
        assert resp3.status_code != 401, f"{method} {path} should accept demo token"
        # Valid token (admin)
        resp4 = client.request(method, path, headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}, **payload_kwargs)
        assert resp4.status_code != 401, f"{method} {path} should accept admin token"
    # All error responses must have error shape
    responses = [resp, resp2]
    if requires_admin:
        responses.append(resp3)
    else:
        responses.extend([resp3, resp4])

    for r in responses:
        if r.status_code != 200:
            try:
                error_response = r.json()
            except Exception:
                error_response = None
            if error_response:
                assert "error" in error_response, f"{method} {path} error response missing 'error'"
                assert "request_id" in error_response["error"], f"{method} {path} error missing request_id"
