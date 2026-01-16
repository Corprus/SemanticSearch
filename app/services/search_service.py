# app/services/search_service.py
from uuid import UUID
from app.domain.entities import Document
from app.domain.entities import QueryResults


class SearchService:
    """
    Сервис поиска
    """
    def search(self, user_id: UUID, query_text: str, top_k: int) -> QueryResults:
        """
        Вернуть top_k совпадений
        Данный метод уже должен проверить кредит, списать его, если достаточно - посчитать эмбеддинги для текста запроса, отправить запрос на поиск похожего, сгенерировать ответ...
        В общем, самый важный метод сервиса, ради которого всё и затевается
        """
        ...

    def search_documents(self, query_id : UUID) -> list[Document]:
        """Вернуть документы по поиску"""
        ...

    def get_history(self, user_id: UUID, limit: int = 50, offset: int = 0) -> list[QueryResults]:
        """Вернуть историю запросов пользователя."""
        ...

    def clear_history(self, user_id: UUID) -> None:
        """Очистить историю запросов пользователя."""
        ...
