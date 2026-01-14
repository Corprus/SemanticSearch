# app/domain/entities/transaction.py
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from enum import Enum

class TransactionType(Enum):
    DOCUMENT_UPLOAD = "document_upload"
    SEARCH_QUERY = "search_query"
    CREDIT_ADD = "credit_add"

@dataclass(frozen=True)
class Transaction:
    """
    Транзакция по списанию (или пополнению) 
    """
    id: UUID
    user_id: UUID
    timestamp: datetime
    amount: Decimal
    reason: TransactionType
    reference_id: UUID  # doc_id или query_id
