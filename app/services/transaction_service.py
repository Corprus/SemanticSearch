from decimal import Decimal
from uuid import UUID
from contextlib import nullcontext
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from models.user import User
from models.transaction import Transaction, TransactionType
from models.account import Account
from services.exceptions import UserNotExistsException, InsufficientBalanceException

class TransactionService:
    """
    Сервис работы с транзакциями кредитов
    """

    def __init__(self, session: Session):
        self._session = session

    def _get_or_create_account_locked(self, user_id: UUID) -> Account:
        # блокируем строку аккаунта
        stmt = select(Account).where(Account.user_id == str(user_id)).with_for_update()
        acc = self._session.execute(stmt).scalars().first()
        if acc is None:
            # аккаунта нет -> создаём (внутри транзакции)
            acc = Account(user_id=str(user_id), balance=Decimal("0.00"))
            self._session.add(acc)
            self._session.flush()

            # и сразу лочим её (можно повторно выбрать, но обычно не требуется)
        return acc        

    def add_credit(self, user_id: UUID, amount: Decimal, reason: TransactionType = TransactionType.CREDIT_ADD, reference_id: UUID | None = None) -> UUID: 
        """Добавить на счет"""
        if amount <= 0:
                raise ValueError("amount must be > 0")

        user = self._session.get(User, str(user_id))
        if user is None:
            raise UserNotExistsException()

        with self._get_transaction_context():
            acc = self._get_or_create_account_locked(user_id)
            acc.balance += amount
            acc.updated_at = datetime.now(timezone.utc)

            tx = Transaction(
                user_id=str(user_id),
                amount=amount,
                reason=reason.value,
                reference_id=str(reference_id) if reference_id else None,
            )
            self._session.add(tx)
            self._session.flush()
            return UUID(tx.id)
    
    def withdraw_credit(self, user_id: UUID, amount: Decimal, reason: TransactionType, reference_id: UUID | None = None) -> UUID:
        """Потратить кредит (если достаточно)"""
        if amount <= 0:
            raise ValueError("amount must be > 0")

        user = self._session.get(User, str(user_id))
        if user is None:
            raise UserNotExistsException()

        with self._get_transaction_context():
            acc = self._get_or_create_account_locked(user_id)

            if acc.balance < amount:
                raise InsufficientBalanceException()

            acc.balance -= amount
            acc.updated_at = datetime.now(timezone.utc)

            tx = Transaction(
                user_id=str(user_id),
                amount=-amount,
                reason=reason.value,
                reference_id=str(reference_id) if reference_id else None,
            )
            self._session.add(tx)
            self._session.flush()
            return UUID(tx.id)
    
    def get_transaction_history(self, user_id: UUID, limit: int = 50, offset: int = 0) -> list[Transaction]: 
        """Получить историю транзакций"""
        history = (
            select(Transaction)
            .where(Transaction.user_id == str(user_id))
            .order_by(Transaction.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.execute(history).scalars().all())
    
    def get_balance(self, user_id: UUID) -> Decimal:
        acc = self._session.get(Account, str(user_id))
        return acc.balance if acc else Decimal("0.00")
    
    def update_transaction_link(self, transaction_id: UUID, reason: TransactionType, reference_id: UUID | None) -> None:
        """Обновление reference в записи о транзакции"""
        tx = self._session.get(Transaction, str(transaction_id))
        if tx is None:
            return
        tx.reason = reason.value
        tx.reference_id = str(reference_id) if reference_id is not None else None
        self._session.add(tx)
        self._session.flush()


    def _get_transaction_context(self):
        # Если транзакция уже начата (autobegin или внешний begin) — не начинаем новую
        return nullcontext() if self._session.in_transaction() else self._session.begin()
