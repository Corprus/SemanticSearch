# app/routes/users.py
from __future__ import annotations

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.user_service import UserService
from services.transaction_service import TransactionService
from services import authorization

from infrastructure.deps import get_user_service, get_transaction_service
from infrastructure.auth import authenticate, CurrentUser

from common.models.user import UserRole


router = APIRouter()


class CreateUserRequest(BaseModel):
    login: str
    password: str
    role: UserRole = UserRole.USER

class UserResponse(BaseModel):
    id: UUID
    login: str
    role: UserRole
    balance: Optional[str] = None

@router.post("", response_model=UserResponse, summary="Создать пользователя")
def create_user(
    req: CreateUserRequest,
    users: UserService = Depends(get_user_service)    
):
    """
    Создать пользователя
    """

    u = users.create_user(req.login, req.password, role=req.role)
    return UserResponse(id=UUID(u.id), login=u.login, role=u.role)

@router.get("", response_model=list[UserResponse], summary="Получить список пользователей")
def list_users(
    role: Optional[UserRole] = Query(default=None),
    usersService: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(authenticate)):
    """
    Получить всех пользователей
    Опционально: role=USER|ADMIN
    """
    try:
        authorization.ensure_admin(current_user)
        items = usersService.list_users(role=role)
        
    except TypeError:
        # list_users без параметров -> всех получаем
        items = usersService.list_users()

    return [UserResponse(id=UUID(u.id), login=u.login, role=u.role) for u in items]


@router.get("/{user_id}", response_model=UserResponse, summary="Получить пользователя по id")
def get_user(
    user_id: UUID,
    users: UserService = Depends(get_user_service),
    transaction_service: TransactionService = Depends(get_transaction_service),
    current_user: CurrentUser = Depends(authenticate)):
    """
    Получить пользователя по id
    """
    user_id = authorization.resolve_target_user(current_user, user_id)
    u = users.find_user_by_id(user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    balance = transaction_service.get_balance(user_id)

    return UserResponse(id=UUID(u.id), login=u.login, role=u.role, balance=str(balance))

class BalanceResponse(BaseModel):
    user_id: UUID
    balance: str  # чтобы Decimal не ругался в JSON


@router.get("/{user_id}/balance", summary="Получить баланс пользователя", response_model=BalanceResponse)
def get_balance(
    user_id: UUID,
    transaction_service: TransactionService = Depends(get_transaction_service),
    current_user: CurrentUser = Depends(authenticate)):
    """
    Получить баланс пользователя
    """
    user_id = authorization.resolve_target_user(current_user, user_id)
    balance = transaction_service.get_balance(user_id)
    return BalanceResponse(user_id=user_id, balance=str(balance))
