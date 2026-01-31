# app/domain/entities/transaction.py
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, Numeric, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.database.database import Base

class TransactionType(str, Enum):
    DOCUMENT_UPLOAD = "document_upload"
    SEARCH_QUERY = "search_query"
    CREDIT_ADD = "credit_add"
    CREDIT_WITHDRAW = "credit_withdraw"

class Transaction(Base):
    """
    Транзакция по списанию (или пополнению) 
    """
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # + пополнение, - списание
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    user: Mapped["User"] = relationship(back_populates="transactions")
    def __repr__(self) -> str:
        return (
            f"Transaction(id={self.id}, user_id={self.user_id}, "
            f"ts={self.timestamp}, amount={self.amount}, "
            f"reason={self.reason}, ref={self.reference_id})"
        )