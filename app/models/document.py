from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base
from enum import Enum

if TYPE_CHECKING:
    from models.query_result_item import QueryResultItem

class DocumentIndexStatus(str, Enum):
    PENDING = "pending"
    INDEXED = "indexed"
    FAILED = "failed"

class Document(Base):
    """
    Класс пользовательского документа, для которого будут считаться эмбеддинги в ML
    """
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    owner_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(256), nullable=False, default="Untitled")
    content: Mapped[str] = mapped_column(Text, nullable=False)


    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    index_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DocumentIndexStatus.PENDING.value,
    )

    index_error: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    owner = relationship("User")

    def __repr__(self) -> str:
        return (
            f"Document(id={self.id}, "
            f"title={self.title}. "
            f"ownerid={self.owner_id}, created={self.created_at})"
            f"status={self.index_status}"
        )
