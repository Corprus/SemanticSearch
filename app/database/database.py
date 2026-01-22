# app/database/database.py
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from database.config import DatabaseSettings

class Base(DeclarativeBase):
    pass

_engine = None
_SessionLocal: sessionmaker[Session] | None = None

def init_db(_settings: DatabaseSettings) -> None:
    """
    Инициализация engine + Session factory.
    Вызывать один раз на старте.
    """
    global _engine, _SessionLocal
    _engine = create_engine(_settings.DATABASE_URL_psycopg, echo=_settings.DEBUG, future=True)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)

def get_engine():
    if _engine is None:
        raise RuntimeError("DB is not initialized. Call init_db(settings) first.")
    return _engine

@contextmanager
def get_session() -> Iterator[Session]:
    """
    Аналог using var db = new DbContext() в EF.
    """
    if _SessionLocal is None:
        raise RuntimeError("DB is not initialized. Call init_db(settings) first.")
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()
