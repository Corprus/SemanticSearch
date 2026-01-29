import numpy as np

from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from domain.interfaces.vector_index import VectorIndex
from models.vector_index_entry import VectorIndexEntry
import logging

logger = logging.getLogger(__name__)

class VectorIndexModel(VectorIndex):
    """
    Реализация VectorIndex поверх Postgres (SQLAlchemy).
    Храним embedding как JSON список float.
    """

    def __init__(self, session: Session, model_name: str = "default"):
        self._session = session
        self._model_name = model_name

    def upsert(self, user_id: UUID, doc_id: UUID, vector: list[float]) -> None:
        stmt = select(VectorIndexEntry).where(
            VectorIndexEntry.user_id == str(user_id),
            VectorIndexEntry.document_id == str(doc_id),
            VectorIndexEntry.model_name == self._model_name,
        )
        entry = self._session.execute(stmt).scalars().first()

        if entry is None:
            entry = VectorIndexEntry(
                user_id=str(user_id),
                document_id=str(doc_id),
                model_name=self._model_name,
                embedding=vector,
            )
            self._session.add(entry)
        else:
            entry.embedding = vector
            self._session.add(entry)

        self._session.flush()

    def delete(self, user_id: UUID, doc_id: UUID) -> None:
        self._session.execute(
            delete(VectorIndexEntry).where(
                VectorIndexEntry.user_id == str(user_id),
                VectorIndexEntry.document_id == str(doc_id),
                VectorIndexEntry.model_name == self._model_name,
            )
        )
        self._session.flush()

    def query(self, vector: list[float], user_id: UUID, top_k: int) -> list[tuple[UUID, float]]:
        q = np.asarray(vector, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0.0:
            return []

        stmt = select(VectorIndexEntry).where(
            VectorIndexEntry.user_id == str(user_id),
            VectorIndexEntry.model_name == self._model_name,
        )
        entries = list(self._session.execute(stmt).scalars().all())

        scored: list[tuple[UUID, float]] = []
        for e in entries:
            v = np.asarray(e.embedding, dtype=np.float32)
            denom = q_norm * np.linalg.norm(v)
            if denom == 0.0:
                score = 0.0
            else:
                score = float(np.dot(q, v) / denom)

            scored.append((UUID(e.document_id), score))            
        
        scored.sort(key=lambda x: x[1], reverse=True)
        logger.info(f"Scored:{scored}")
        return scored[:top_k]

