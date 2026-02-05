"""
Тесты работы с пользователями
"""
from uuid import UUID

import pytest

from app.services.user_service import UserService
from app.services.auth_service import AuthService
from common.models.user import UserRole
from common.exceptions import UserAlreadyExistsException, InvalidCredentialsException
from app.infrastructure.md5_hasher import Md5PasswordHasher
from app.infrastructure.jwt_handler import JwtConfig, JwtHandler


def test_create_user_and_prevent_duplicates(session):
    """
    Проверка отлупа на дубликатах пользователя
    """
    hasher = Md5PasswordHasher()
    users = UserService(session, hasher)

    u1 = users.create_user("alice", "secret", role=UserRole.USER)
    assert u1.login == "alice"

    with pytest.raises(UserAlreadyExistsException):
        users.create_user("alice", "secret", role=UserRole.USER)


def test_auth_login_success(session):
    """
    Проверка что корректно логинимся свежим пользователем
    """
    hasher = Md5PasswordHasher()
    users = UserService(session, hasher)
    u = users.create_user("bob", "pass", role=UserRole.USER)

    jwt_handler = JwtHandler(JwtConfig(secret_key="test-secret", access_token_ttl_minutes=60))
    auth = AuthService(users, hasher, jwt_handler)

    token = auth.login("bob", "pass")
    payload = jwt_handler.verify_access_token(token)

    assert UUID(payload["sub"]) == UUID(u.id)


def test_auth_login_invalid_credentials(session):
    """
    Проверка что отлуп с некорректными кредами
    """
    hasher = Md5PasswordHasher()
    users = UserService(session, hasher)
    users.create_user("carol", "right", role=UserRole.USER)

    jwt_handler = JwtHandler(JwtConfig(secret_key="test-secret", access_token_ttl_minutes=60))
    auth = AuthService(users, hasher, jwt_handler)

    with pytest.raises(InvalidCredentialsException):
        auth.login("carol", "wrong")

    with pytest.raises(InvalidCredentialsException):
        auth.login("missing", "any")
