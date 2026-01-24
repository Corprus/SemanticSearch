# app/routes/auth.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from uuid import UUID
from services.auth_service import AuthService
from infrastructure.deps import get_auth_service

router = APIRouter()


class LoginRequest(BaseModel):
    login: str
    password: str


class TokenResponse(BaseModel):
    token: str


@router.post("/login", response_model=TokenResponse, summary="Авторизовать пользователя (пока заглушка)")
def login(req: LoginRequest, auth: AuthService = Depends(get_auth_service)):
    token = auth.login(req.login, req.password)
    return TokenResponse(token=token)

@router.post("/logout/{user_id}", summary="Разлогинить пользователя (пока заглушка)")
def logout(user_id: UUID, auth: AuthService = Depends(get_auth_service)):
    auth.logout(user_id)
    return