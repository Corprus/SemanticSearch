from sentence_transformers import SentenceTransformer
from common.domain.interfaces.embedding_model import EmbeddingModel

class SentenceTransformerEmbeddingModel(EmbeddingModel):
    """
    Реализация EmbeddingModel на базе Hugging Face Sentence Transformers.
    """

    def __init__(
        self,
        normalize: bool = True,
    ):
        self._normalize = normalize
        self._model = SentenceTransformer(self.name)
        
    @property
    def name(self) -> str:
        return "sentence-transformers/all-MiniLM-L6-v2"      
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Посчитать эмбеддинги для списка текстов.
        Порядок сохраняется.
        """
        if not texts:
            return []

        embeddings = self._model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=self._normalize,
            show_progress_bar=False,
        )

        # SentenceTransformer возвращает np.ndarray
        return embeddings.tolist()
