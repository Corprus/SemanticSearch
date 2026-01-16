# app/domain/ports/embedding_model.py
from abc import ABC, abstractmethod

class EmbeddingModel(ABC):
    """
    ML модель, которая умеет считать эмбеддинги.
    """

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Вернуть эмбеддинги для списка текстов в том же порядке."""
        pass

    def embed(self, text: str) -> list[float]:
        """Получить эмбеддинги для одного текста, не деля."""
        return self.embed_batch([text])[0]        

