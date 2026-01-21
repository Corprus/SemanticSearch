from __future__ import annotations

from decimal import Decimal
from enum import Enum
from uuid import uuid4

from sqlalchemy import String, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base
from models.mixins import CrudMixin


class UserRole(str, Enum):
    """
    Перечисление возможных ролей пользователя
    """
    USER = "user"
    ADMIN = "admin"


class User(Base, CrudMixin):
    """
    Класс пользователя
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    login: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        String(32),
        nullable=False,
        default=UserRole.USER.value,
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"User(id={self.id}, "
            f"login={self.login}, balance={self.balance}, "
            f"role={self.role})"
        )
