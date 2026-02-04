"""
Тест сервиса транзакций
"""

from decimal import Decimal
from uuid import UUID

import pytest

from services.transaction_service import TransactionService
from common.models.user import User
from common.models.account import Account
from common.models.transaction import TransactionType
from common.exceptions import UserNotExistsException, InsufficientBalanceException


def _create_user(session, login: str = "u", password_hash: str = "hash") -> User:
    user = User(login=login, password_hash=password_hash)
    session.add(user)
    session.flush()
    return user


def test_add_credit_creates_transaction(session):
    """
    Тестим, что добавление кредита создаёт транзакцию
    """
    user = _create_user(session)
    svc = TransactionService(session)

    tx_id = svc.add_credit(UUID(user.id), Decimal("10.00"), reason=TransactionType.CREDIT_ADD)
    session.commit()

    acc = session.get(Account, str(user.id))
    assert acc is not None
    assert acc.balance == Decimal("10.00")

    assert isinstance(tx_id, UUID)


def test_add_credit_negative_amount_raises(session):
    """
    Тестим, что нельзя добавить отрицательный кредит
    """
    user = _create_user(session)
    svc = TransactionService(session)

    with pytest.raises(ValueError):
        svc.add_credit(UUID(user.id), Decimal("0"))


def test_add_credit_user_missing(session):
    """
    Тестим, что нельзя добавить кредит отсутствующему пользователю
    """
    svc = TransactionService(session)
    with pytest.raises(UserNotExistsException):
        svc.add_credit(UUID("00000000-0000-0000-0000-000000000001"), Decimal("1.00"))


def test_withdraw_credit_insufficient_balance(session):
    """
    Тестим, что нельзя списать кредиты ниже 0
    """    
    user = _create_user(session)
    svc = TransactionService(session)

    # no funds
    with pytest.raises(InsufficientBalanceException):
        svc.withdraw_credit(UUID(user.id), Decimal("1.00"), reason=TransactionType.SEARCH_QUERY)


def test_withdraw_credit_success(session):
    """
    Тестим, что нельзя можно списать кредиты выше 0
    """    
    user = _create_user(session)
    svc = TransactionService(session)
    svc.add_credit(UUID(user.id), Decimal("5.00"))
    session.commit()

    tx_id = svc.withdraw_credit(UUID(user.id), Decimal("2.00"), reason=TransactionType.SEARCH_QUERY)
    session.commit()

    acc = session.get(Account, str(user.id))
    assert acc.balance == Decimal("3.00")
    assert isinstance(tx_id, UUID)
