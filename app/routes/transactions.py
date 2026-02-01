# app/routes/transactions.py
from __future__ import annotations

from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from datetime import datetime

from infrastructure.deps import get_transaction_service
from infrastructure.auth import authenticate, CurrentUser

from services import authorization
from services.transaction_service import TransactionService

from common.models.transaction import TransactionType


router = APIRouter()


class AddCreditRequest(BaseModel):
    user_id: UUID | None = None
    amount: Decimal = Field(gt=0)


class TransactionIdResponse(BaseModel):
    transaction_id: UUID


@router.post("/credit", response_model=TransactionIdResponse, summary="Добавить деньги пользователю")
def add_credit(req: AddCreditRequest, tx: TransactionService = Depends(get_transaction_service), current_user: CurrentUser = Depends(authenticate)):    
    user_id = authorization.resolve_target_user(current_user, req.user_id)
    tx_id = tx.add_credit(user_id, req.amount)
    return TransactionIdResponse(transaction_id=tx_id)


class WithdrawRequest(BaseModel):
    user_id: UUID | None = None
    amount: Decimal = Field(gt=0)
    
@router.post("/debit", response_model=TransactionIdResponse, summary="Снять деньги с пользователя (admin only)")
def withdraw(req: WithdrawRequest, transaction_service: TransactionService = Depends(get_transaction_service), current_user: CurrentUser = Depends(authenticate)):
    authorization.ensure_admin(current_user)
    user_id = authorization.resolve_target_user(current_user, req.user_id)
    transaction_id = transaction_service.withdraw_credit(user_id, req.amount, TransactionType.CREDIT_WITHDRAW)
    return TransactionIdResponse(transaction_id=transaction_id)


class TransactionResponse(BaseModel):
    id: UUID
    timestamp: datetime
    amount: str
    reason: str
    reference_id: UUID | None = None


@router.get("", response_model=list[TransactionResponse], summary="Получить историю транзакций текущего пользователя")
def list_my_transactions(
    tx: TransactionService = Depends(get_transaction_service),
    current_user: CurrentUser = Depends(authenticate)):
    user_id = authorization.resolve_target_user(current_user)
    items = tx.get_transaction_history(user_id)
    return [
        TransactionResponse(
            id=i.id if isinstance(i.id, UUID) else UUID(str(i.id)),
            timestamp=i.timestamp,
            amount=str(i.amount),
            reason=str(i.reason),
            reference_id=(i.reference_id if i.reference_id is None else (i.reference_id if isinstance(i.reference_id, UUID) else UUID(str(i.reference_id)))),
        )
        for i in items
    ]


@router.get("/{user_id}", response_model=list[TransactionResponse], summary="Получить историю транзакций пользователя (admin only)")
def list_transactions(
    user_id: UUID,
    tx: TransactionService = Depends(get_transaction_service),
    current_user: CurrentUser = Depends(authenticate)):
    authorization.ensure_admin(current_user)
    user_id = authorization.resolve_target_user(current_user, user_id)
    items = tx.get_transaction_history(user_id)
    return [
        TransactionResponse(
            id=i.id if isinstance(i.id, UUID) else UUID(str(i.id)),
            timestamp=i.timestamp,
            amount=str(i.amount),
            reason=str(i.reason),
            reference_id=(i.reference_id if i.reference_id is None else (i.reference_id if isinstance(i.reference_id, UUID) else UUID(str(i.reference_id)))),
        )
        for i in items
    ]
