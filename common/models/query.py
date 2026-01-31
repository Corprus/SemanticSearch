from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Numeric, Text, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.database.database import Base
from common.models.mixins import CrudMixin

class QueryJobStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"

class Query(Base, CrudMixin):
    """
    Класс, описывающий запрос пользователя - что он искал, его "стоимость", ссылка на транзакцию, когда был сделан.
    """
    __tablename__ = "queries"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    query_text: Mapped[str] = mapped_column(Text, nullable=False)

    cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))

    # транзакция, которая списала стоимость поиска
    transaction_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("transactions.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    query_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=QueryJobStatus.PENDING.value,
    )

    query_error: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    top_k: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    user = relationship("User")
    transaction = relationship("Transaction")
    results: Mapped[list["QueryResultItem"]] = relationship(
        back_populates="query",
        cascade="all, delete-orphan",
        order_by="QueryResultItem.rank",
    )
