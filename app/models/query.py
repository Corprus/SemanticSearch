from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base
from models.mixins import CrudMixin


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

    user = relationship("User")
    transaction = relationship("Transaction")
    results: Mapped[list["QueryResultItem"]] = relationship(
        back_populates="query",
        cascade="all, delete-orphan",
        order_by="QueryResultItem.rank",
    )
