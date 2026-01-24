# app/deps.py
from __future__ import annotations

from typing import Iterator
from fastapi import Depends
from sqlalchemy.orm import Session

from database.database import get_session

from services.user_service import UserService
from services.auth_service import AuthService
from services.transaction_service import TransactionService
from services.document_service import DocumentService
from services.search_service import SearchService
from services.index_service import IndexService

from infrastructure.md5_hasher import Md5PasswordHasher
from infrastructure.dummy_embedding_model import DummyEmbeddingModel
from infrastructure.vector_index_model import VectorIndexModel


def get_db() -> Iterator[Session]:
    with get_session() as session:
        with session.begin():
            yield session


def get_password_hasher():
    return Md5PasswordHasher()


def get_embedder():
    return DummyEmbeddingModel()


def get_vector_index(db: Session = Depends(get_db)):
    embedder = get_embedder()
    return VectorIndexModel(db, model_name=embedder.name)


def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    return TransactionService(db)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db, password_hasher=get_password_hasher())


def get_auth_service(
    user_service: UserService = Depends(get_user_service),
) -> AuthService:
    return AuthService(user_service=user_service, password_hasher=get_password_hasher())


def get_index_service(
    db: Session = Depends(get_db),
) -> IndexService:
    return IndexService(
        session=db,
        vector_index=get_vector_index(db),
        embedding_model=get_embedder(),
    )


def get_document_service(
    db: Session = Depends(get_db),
    tx: TransactionService = Depends(get_transaction_service),
    index: IndexService = Depends(get_index_service),
) -> DocumentService:
    return DocumentService(session=db, transaction_service=tx, index_service=index)


def get_search_service(
    db: Session = Depends(get_db),
    tx: TransactionService = Depends(get_transaction_service),
    index: IndexService = Depends(get_index_service),
) -> SearchService:
    return SearchService(session=db, transaction_service=tx, index_service=index)
