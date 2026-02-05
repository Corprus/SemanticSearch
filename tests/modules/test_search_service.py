"""
Тесты поиска
"""

from decimal import Decimal
from uuid import UUID

import pytest

from app.services.search_service import SearchService
from app.services.transaction_service import TransactionService
from common.models.user import User
from common.models.query import Query
from common.exceptions import UserNotExistsException


class _DummyCelery:
    def __init__(self):
        self.calls = []

    def send_task(self, name, args=None, kwargs=None):
        self.calls.append((name, args or [], kwargs or {}))


def _create_user(session, login: str = "u", password_hash: str = "hash") -> User:
    user = User(login=login, password_hash=password_hash)
    session.add(user)
    session.flush()
    return user


def test_create_query_job_withdraws_credit_and_enqueues(session, monkeypatch):
    """
    Тестим, что в момент постановки поиска, кредит списывается, а задача - ставится в очередь
    """
    user = _create_user(session)
    tx = TransactionService(session)
    tx.add_credit(UUID(user.id), Decimal("5.00"))
    session.commit()

    dummy = _DummyCelery()
    # Patch the module-level celery app used by SearchService
    import app.services.search_service as ss
    monkeypatch.setattr(ss, "worker_app", dummy)

    svc = SearchService(session, tx, search_cost=Decimal("1.00"))
    query_id = svc.create_query_job(UUID(user.id), "hello", top_k=3)

    # Query row created and linked to a transaction
    q = session.get(Query, str(query_id))
    assert q is not None
    assert q.transaction_id is not None
    assert q.cost == Decimal("1.00")

    # Credit was deducted: 5 - 1 = 4
    assert tx.get_balance(UUID(user.id)) == Decimal("4.00")

    # Celery task enqueued
    assert len(dummy.calls) == 1
    task_name, args, _ = dummy.calls[0]
    assert str(query_id) in args
    assert task_name == ss.TASK_PROCESS_SEARCH_QUERY_NAME


def test_create_query_job_requires_positive_top_k(session):
    """
    Тестим валидацию на top_k
    """

    user = _create_user(session)
    tx = TransactionService(session)
    tx.add_credit(UUID(user.id), Decimal("5.00"))
    session.commit()

    svc = SearchService(session, tx)
    with pytest.raises(ValueError):
        svc.create_query_job(UUID(user.id), "hello", top_k=0)


def test_create_query_job_user_missing(session):
    """
    Тестим, что нельзя поставить в работу поиск от несуществующего пользователя
    """
    tx = TransactionService(session)
    svc = SearchService(session, tx)
    with pytest.raises(UserNotExistsException):
        svc.create_query_job(UUID("00000000-0000-0000-0000-000000000001"), "hello", top_k=1)
