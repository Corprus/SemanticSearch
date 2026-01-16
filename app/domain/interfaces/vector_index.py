# domain/interfaces/vector_index.py
from abc import ABC
from uuid import UUID


class VectorIndex(ABC):
    """
    Базовый класс для хранения эмбеддингов
    В реализациях уже надо писать в базу или в память, 
    Опять же, эмбеддинги могут быть разные в зависимости от модели, однако поиск по ним должен осуществляться через единый интерфейс
    """
    def upsert(self, user_id: UUID, doc_id: UUID, vector: list[float]) -> None: 
        """
        Добавить/обновить эмбеддинги к документу
        """
        ...
    def delete(self, user_id: UUID, doc_id: UUID) -> None: 
        """
        Удалить эмбеддинги к документу
        """
        ...

    def query(self, vector: list[float], user_id: UUID, top_k: int) -> list[tuple[UUID, float]]: 
        """
        Поиск похожих эмбеддингов среди документов пользователя
        """
        ...
