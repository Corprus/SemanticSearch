# app/services/document_service.py
from uuid import UUID
from app.domain.entities.document import Document

class DocumentService:
    def add_document(self, user_id: UUID, title: str, content: str) -> Document:
        """
        Добавить (загрузить) документ в систему
        Тут будет сразу и списываться кредит за загрузку
        """
        ...

    def get_document(self, user_id: UUID, document_id: UUID) -> Document:
        """
        Получить документ из системы
        """
        ...

    def list_documents(self, user_id: UUID) -> list[Document]:
        """
        Получить документы пользователя
        """
        ...
        

    def delete_document(self, user_id: UUID, document_id: UUID) -> None:
        """
        Удалить документ из системы
        """
        ...
