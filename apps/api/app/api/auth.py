from fastapi import APIRouter
from pydantic import BaseModel
from app.auth import get_auth_level

router = APIRouter()

class LoginRequest(BaseModel):
    password: str

@router.post("/login")
async def login(request: LoginRequest):
    return {"level": get_auth_level(request.password)}

