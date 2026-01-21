from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import User
from models.transaction import Transaction, TransactionType
from services.exceptions import UserNotExistsException, InsufficientBalanceException

class TransactionService:
    """
    Сервис работы с транзакциями кредитов
    """

    def __init__(self, session: Session):
        self._session = session

    def add_credit(self, user_id: UUID, amount: Decimal) -> UUID: 
        """Добавить на счет"""
        if amount <= 0:
                raise ValueError("amount must be > 0")

        user = self._session.get(User, str(user_id))
        if user is None:
            raise UserNotExistsException()

        user.balance += amount
        self._session.add(user)

        tx = Transaction(
            user_id=str(user_id),
            amount=amount,
            reason=TransactionType.CREDIT_ADD.value,
            reference_id=None,
        )
        self._session.add(tx)
        self._session.flush()

        return UUID(tx.id)
    
    def withdraw_credit(self, user_id: UUID, amount: Decimal) -> UUID: 
        """Потратить кредит (если достаточно)"""
        if amount <= 0:
            raise ValueError("amount must be > 0")

        user = self._session.get(User, str(user_id))
        if user is None:
            raise UserNotExistsException()

        if user.balance < amount:
            raise InsufficientBalanceException()

        user.balance -= amount
        self._session.add(user)

        tx = Transaction(
            user_id=str(user_id),
            amount=-amount,
            reason=TransactionType.SEARCH_QUERY.value,  # по умолчанию; документ/поиск уточняем снаружи
            reference_id=None,
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
    
    def update_transaction_link(self, transaction_id: UUID, reason: TransactionType, reference_id: UUID | None) -> None:
        """Обновление reference в записи о транзакции"""
        tx = self._session.get(Transaction, str(transaction_id))
        if tx is None:
            return
        tx.reason = reason.value
        tx.reference_id = str(reference_id) if reference_id is not None else None
        self._session.add(tx)
        self._session.flush()