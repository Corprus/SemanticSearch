# app/routes/auth.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from pydantic import BaseModel
from services.auth_service import AuthService
from infrastructure.deps import get_auth_service

router = APIRouter()

class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@router.post("/login", response_model=TokenResponse, summary="Авторизовать пользователя (пока заглушка)")
def login(form_data: OAuth2PasswordRequestForm = Depends(),
           auth: AuthService = Depends(get_auth_service)):
    token = auth.login(form_data.username, form_data.password)
    return TokenResponse(access_token=token, token_type="bearer")

@router.post("/logout", summary="Разлогинить пользователя (заглушка, в реальности просто удалим токен с фронта)")
def logout(auth: AuthService = Depends(get_auth_service)):
    auth.logout()
    return