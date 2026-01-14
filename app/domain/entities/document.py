from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

@dataclass
class Document:
    """
    Класс пользовательского документа, для которого будут считаться эмбеддинги в ML
    """
    id: UUID
    user_id: UUID
    content: str
    transaction_id: UUID
    created_at: datetime
