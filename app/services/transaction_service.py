from decimal import Decimal
from uuid import UUID

from app.domain.entities.transaction import Transaction


class TransactionService:
    """
    Сервис работы с транзакциями кредитов
    """

    def add_credit(self, user_id: UUID, amount: Decimal) -> UUID: 
        """Добавить на счет"""
        ...

    def withdraw_credit(self, user_id: UUID, amount: Decimal) -> UUID: 
        """Потратить кредит (если достаточно)"""
        ...

    def get_transaction_history(self, user_id: UUID, limit: int = 50, offset: int = 0) -> list[Transaction]: 
        """Получить историю транзакций"""
        ...