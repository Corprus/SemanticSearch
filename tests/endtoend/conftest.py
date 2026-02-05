import os
import time
from dataclasses import dataclass
from uuid import uuid4

import pytest
import requests


DEFAULT_BASE_URL = "http://localhost/api"


@dataclass(frozen=True)
class ApiUser:
    login: str
    password: str
    access_token: str


def wait_health(base_url: str, timeout_s: int = 120) -> None:
    """Wait until /health is ready."""
    deadline = time.time() + timeout_s
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            r = requests.get(f"{base_url}/health", timeout=3)
            if r.status_code == 200:
                return
        except Exception as e:  # noqa: BLE001
            last_err = e
        time.sleep(2)
    raise RuntimeError(f"Service is not healthy at {base_url}. Last error: {last_err}")


def api_headers(user: ApiUser) -> dict[str, str]:
    return {"Authorization": f"Bearer {user.access_token}"}


def create_user(base_url: str, login: str, password: str) -> None:
    r = requests.post(
        f"{base_url}/users",
        json={"login": login, "password": password, "role": "user"},
        timeout=10,
    )
    # 409 — пользователь уже существует
    assert r.status_code in (200, 201, 409), r.text


def login_user(base_url: str, login: str, password: str) -> ApiUser:
    r = requests.post(
        f"{base_url}/auth/login",
        data={"username": login, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return ApiUser(login=login, password=password, access_token=token)


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("E2E_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


@pytest.fixture(scope="session", autouse=True)
def _healthcheck(base_url: str) -> None:
    # Один раз на сессию убеждаемся, что система поднята.
    wait_health(base_url)


@pytest.fixture
def fresh_user(base_url: str) -> ApiUser:
    """Create + login a unique user for each test."""
    login = f"e2e_{uuid4().hex[:10]}"
    password = "pass12345"
    create_user(base_url, login, password)
    return login_user(base_url, login, password)
