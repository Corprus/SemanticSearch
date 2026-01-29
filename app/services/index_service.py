# app/services/index_service.py
from uuid import UUID
from sqlalchemy.orm import Session

from models.document import Document
from domain.interfaces.vector_index import VectorIndex
from domain.interfaces.embedding_model import EmbeddingModel
from infrastructure.dummy_embedding_model import DummyEmbeddingModel

class IndexService:
    """
    Сервис индексации документов
    """

    def __init__(self, session: Session, vector_index: VectorIndex, embedding_model: EmbeddingModel | None = None):
        self._session = session
        self._embedding_model = embedding_model or DummyEmbeddingModel()
        self._vector_index = vector_index

    def remove_document(self, user_id: UUID, document_id: UUID) -> None:
        """Удалить документ из VectorIndex."""
        self._vector_index.delete(user_id=user_id, doc_id=document_id)

    def search(self, user_id: UUID, query_text: str, top_k: int):
        q_vec = self._embedding_model.embed(query_text)
        return self._vector_index.query(q_vec, user_id, top_k)

    def index_document(self, user_id: UUID, document_id: UUID) -> None:
        """Посчитать embedding документа в VectorIndex."""

        doc = self._session.get(Document, str(document_id))
        if doc is None or doc.owner_id != str(user_id):
            return

        vector = self._embedding_model.embed(f"{doc.title}\n{doc.content}")

        # но внутри реализации VectorIndex (SqlAlchemyVectorIndex.upsert)
        self._vector_index.upsert(user_id=user_id, doc_id=document_id, vector=vector)
