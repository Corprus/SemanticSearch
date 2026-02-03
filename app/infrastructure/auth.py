from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from infrastructure.jwt_handler import InvalidTokenError, JwtHandler
from infrastructure.deps import get_jwt_handler  # добавишь фабрику
from infrastructure.deps import get_user_service

from services.user_service import UserService
from dataclasses import dataclass
from common.models.user import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@dataclass(frozen=True)
class CurrentUser:
    id: UUID
    role: UserRole
    login: str    

async def authenticate(
    token: str = Depends(oauth2_scheme),
    jwt_handler: JwtHandler = Depends(get_jwt_handler),
    user_service: UserService = Depends(get_user_service),  # можешь убрать, если не хочешь DB-check
) -> CurrentUser:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in for access",
        )

    try:
        decoded = jwt_handler.verify_access_token(token)
        user_id = UUID(decoded["sub"])
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = user_service.find_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token user",
        )
    
    return CurrentUser(
        id=UUID(user.id),
        role=UserRole(user.role),
        login = user.login
    )