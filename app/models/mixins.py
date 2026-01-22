from __future__ import annotations

from typing import TypeVar, Type
from sqlalchemy.orm import Session

T = TypeVar("T")

class CrudMixin:
    @classmethod
    def get(cls: Type[T], session: Session, entity_id) -> T | None:
        return session.get(cls, entity_id)

    def save(self, session: Session) -> None:
        session.add(self)
        session.flush()

    def delete(self, session: Session) -> None:
        session.delete(self)
        session.flush()
