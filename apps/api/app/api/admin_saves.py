import os
import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from app.middleware.error_handlers import error_response
from typing import Any
from app.auth import require_auth

STORAGE_DIR = Path(os.environ.get("STORAGE_DIR", "/data"))
SAVES_DIR = STORAGE_DIR / "admin_saves"

from fastapi import Depends
from app.auth import require_auth
from fastapi import Depends
from app.auth import require_auth
from fastapi import Depends
from app.auth import require_auth
router = APIRouter(
    dependencies=[Depends(require_auth)]
)

ALLOWED_KINDS = {"invoice", "book"}


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def get_save_path(kind: str, entity_id: str) -> Path:
    return SAVES_DIR / kind / f"{entity_id}.json"


def atomic_write_json(path: Path, data: Any):
    ensure_dir(path.parent)
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


from fastapi import Depends
from app.auth import require_auth
@router.get("/api/admin-saves/{kind}/{entity_id}", dependencies=[Depends(require_auth)])
async def get_admin_save(kind: str, entity_id: str, auth=Depends(require_auth)):
    request_id = None
    try:
        from fastapi import Request as _Request
        import inspect
        frame = inspect.currentframe()
        while frame:
            if "request" in frame.f_locals and isinstance(frame.f_locals["request"], _Request):
                request_id = getattr(frame.f_locals["request"].state, "request_id", None)
                break
            frame = frame.f_back
    except Exception:
        pass
    if kind not in ALLOWED_KINDS:
        return error_response("invalid_kind", "Invalid kind", request_id, 400)
    if not entity_id:
        return error_response("missing_entity_id", "Missing entity_id", request_id, 400)
    path = get_save_path(kind, entity_id)
    try:
        data = read_json(path)
        return {"success": True, "data": data}
    except Exception as e:
        return error_response("server_error", str(e), request_id, 500)


@router.put("/api/admin-saves/{kind}/{entity_id}", dependencies=[Depends(require_auth)])
async def put_admin_save(kind: str, entity_id: str, request: Request, auth=Depends(require_auth)):
    request_id = getattr(request.state, "request_id", None)
    if kind not in ALLOWED_KINDS:
        return error_response("invalid_kind", "Invalid kind", request_id, 400)
    if not entity_id:
        return error_response("missing_entity_id", "Missing entity_id", request_id, 400)
    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            return error_response("invalid_payload", "Payload must be a JSON object", request_id, 400)
        path = get_save_path(kind, entity_id)
        atomic_write_json(path, payload)
        return {"success": True}
    except Exception as e:
        return error_response("server_error", str(e), request_id, 500)
