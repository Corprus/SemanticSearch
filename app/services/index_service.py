# app/services/index_service.py
from uuid import UUID
from sqlalchemy.orm import Session

from common.domain.interfaces.vector_index import VectorIndex

class IndexService:
    """
    Сервис индексации документов
    """
    
    def __init__(self, session: Session, vector_index: VectorIndex):
        self._session = session
        self._vector_index = vector_index

    def remove_document(self, user_id: UUID, document_id: UUID) -> None:
        """Удалить документ из VectorIndex."""
        self._vector_index.delete(user_id=user_id, doc_id=document_id)

