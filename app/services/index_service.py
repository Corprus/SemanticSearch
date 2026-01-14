# app/services/index_service.py
from uuid import UUID


class IndexService:
    """
    Сервис индексации документов
    """
    def index_document(self, user_id: UUID, document_id: UUID) -> None:
        """Посчитать embedding документа в VectorIndex."""
        ...

    def remove_document(self, user_id: UUID, document_id: UUID) -> None:
        """Удалить документ из VectorIndex."""
        ...
