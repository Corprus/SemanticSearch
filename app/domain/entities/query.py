# app/domain/entities/query.py
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from decimal import Decimal

@dataclass(frozen=True)
class Query:
    """
    Класс, описывающий запрос пользователя - что он искал, его "стоимость", ссылка на транзакцию, когда был сделан.
    """
    id: UUID
    user_id: UUID
    query_text: str
    cost: Decimal
    transaction_id: UUID
    created_at: datetime


@dataclass(frozen=True)
class QueryResultItem:
    """
    Одиночный результат запроса
    """
    document_id: UUID
    score: float
    rank: int

@dataclass(frozen=True)
class QueryResults:
    """
    Результаты поиска по запросу
    """
    query_id: UUID
    items: tuple[QueryResultItem]

