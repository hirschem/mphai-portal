import os
import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Any
from app.auth import require_auth

STORAGE_DIR = Path(os.environ.get("STORAGE_DIR", "/data"))
SAVES_DIR = STORAGE_DIR / "admin_saves"

router = APIRouter()

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


@router.get("/api/admin-saves/{kind}/{entity_id}")
async def get_admin_save(kind: str, entity_id: str, auth=Depends(require_auth)):
    if kind not in ALLOWED_KINDS:
        return JSONResponse({"success": False, "error": "Invalid kind"}, status_code=400)
    if not entity_id:
        return JSONResponse({"success": False, "error": "Missing entity_id"}, status_code=400)
    path = get_save_path(kind, entity_id)
    try:
        data = read_json(path)
        return {"success": True, "data": data}
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.put("/api/admin-saves/{kind}/{entity_id}")
async def put_admin_save(kind: str, entity_id: str, request: Request, auth=Depends(require_auth)):
    if kind not in ALLOWED_KINDS:
        return JSONResponse({"success": False, "error": "Invalid kind"}, status_code=400)
    if not entity_id:
        return JSONResponse({"success": False, "error": "Missing entity_id"}, status_code=400)
    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            return JSONResponse({"success": False, "error": "Payload must be a JSON object"}, status_code=400)
        path = get_save_path(kind, entity_id)
        atomic_write_json(path, payload)
        return {"success": True}
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
