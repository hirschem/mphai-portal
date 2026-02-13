print("AUTH ROUTER LOADED: bcd0a5f")
from fastapi import APIRouter
from pydantic import BaseModel
from app.auth import get_auth_level

router = APIRouter()

class LoginRequest(BaseModel):
    password: str

@router.post("/auth/login")
async def login(request: LoginRequest):
    print("LOGIN HIT: bcd0a5f")
    return {"level": get_auth_level(request.password)}

