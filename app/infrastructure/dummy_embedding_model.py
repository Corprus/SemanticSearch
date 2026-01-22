# app/infrastructure/embedding/zero_embedding.py
import numpy as np
from domain.interfaces.embedding_model import EmbeddingModel

class DummyEmbeddingModel(EmbeddingModel):
    """
    Хоть и математичная, но неточная примерная апроксимация эмбеддингов.
    Требовалась для покрытия поиска, пока реальные модели не завезли.
    """
    def __init__(self, dim: int = 64, name: str = "dummy-embed"):
        self.dim = dim
        self.name = name



    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []

        for text in texts:
            vec = np.zeros(self.dim, dtype=np.float32) # берём нули
    
            tokens = [t for t in text.lower().split() if t.strip()] #текст бьём по словам
            if not tokens:
                vec[0] = 1.0
                embeddings.append(vec.tolist())
                continue

            for tok in tokens:
                idx = hash(tok) % self.dim #берём хэш от строки, ограничиваем размерностью
                vec[idx] += 1.0 # смещаем подальше от нуля

            # L2-нормализация — чтобы cosine similarity был корректным
            norm = np.linalg.norm(vec)
            if norm > 0.0:
                vec /= norm
            else:
                vec[0] = 1.0

            embeddings.append(vec.tolist())

        return embeddings
