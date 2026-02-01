from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.database.database import Base
from common.models.mixins import CrudMixin


class VectorIndexEntry(Base, CrudMixin):
    """
    Индексная запись: документ -> embedding (для конкретной модели).
    """
    __tablename__ = "vector_index_entries"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(String(128), nullable=False)

    # embedding как список чисел: [0.1, 0.2, ...]
    embedding: Mapped[list[float]] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    document = relationship("Document")

    __table_args__ = (
        UniqueConstraint("user_id", "document_id", "model_name", name="uq_vec_user_doc_model"),
    )
