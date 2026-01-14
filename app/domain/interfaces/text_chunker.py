# app/domain/ports/text_chunker.py
from abc import ABC, abstractmethod

class TextChunker(ABC):
    """
    Базовый класс для нарезки текста
    В реализациях - можно сделать тупо по символам, по предложениям и тп
    """
    @abstractmethod
    def chunk(self, text: str) -> list[str]:
        """
        Нарезать текст на куски для получения эмбеддингов
        """
        ...