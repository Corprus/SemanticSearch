from __future__ import annotations

from uuid import uuid4
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.database.database import Base
from common.models.mixins import CrudMixin


class QueryResultItem(Base, CrudMixin):
    """
    Одиночный результат запроса.
    """
    __tablename__ = "query_result_items"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))

    query_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("queries.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    score: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)

    query: Mapped["Query"] = relationship(back_populates="results")
    document = relationship("Document")

    __table_args__ = (
        UniqueConstraint("query_id", "rank", name="uq_query_rank"),
    )
