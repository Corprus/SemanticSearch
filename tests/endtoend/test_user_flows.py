"""
Тесты системы в целом, end-to-end, 
Типичных действий пользователя
"""
import time
from decimal import Decimal

import requests

from conftest import ApiUser, api_headers


def get_me(base_url: str, user: ApiUser) -> dict:
    """
    Тестит получение самого пользователя, что оно не сбоит
    """
    r = requests.get(f"{base_url}/users/me", headers=api_headers(user), timeout=10)
    assert r.status_code == 200, r.text
    return r.json()


def add_credit(base_url: str, user: ApiUser, amount: Decimal) -> str:
    """
    Тестит добавление кредита пользователю
    """
    r = requests.post(
        f"{base_url}/transactions/credit",
        json={"amount": str(amount)},
        headers=api_headers(user),
        timeout=10,
    )
    assert r.status_code == 200, r.text
    return r.json()["transaction_id"]


def upload_doc(base_url: str, user: ApiUser, title: str, content: str) -> str:
    """
    Тестит аплоад файла
    """
    r = requests.put(
        f"{base_url}/documents",
        json={"title": title, "content": content},
        headers=api_headers(user),
        timeout=10,
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def wait_doc_indexed(base_url: str, user: ApiUser, doc_id: str, timeout_s: int = 120) -> str:
    """
    Ожидание аплоада
    """
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        r = requests.get(
            f"{base_url}/documents/{doc_id}",
            headers=api_headers(user),
            timeout=10,
        )
        assert r.status_code == 200, r.text
        last = r.json()
        status_ = last["index_status"]
        if status_ in ("indexed", "failed"):
            return status_
        time.sleep(2)
    raise TimeoutError(f"Document {doc_id} did not finish indexing. Last={last}")


def create_search(base_url: str, user: ApiUser, query_text: str, top_k: int = 5) -> str:
    """
    Создание поиска
    """
    r = requests.post(
        f"{base_url}/search",
        json={"query_text": query_text, "top_k": top_k},
        headers=api_headers(user),
        timeout=10,
    )
    assert r.status_code == 200, r.text
    return r.json()["query_id"]


def wait_search_done(base_url: str, user: ApiUser, query_id: str, timeout_s: int = 60) -> dict:
    """
    Ожидание выполнения поиска
    """
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        r = requests.get(
            f"{base_url}/search/{query_id}/results",
            headers=api_headers(user),
            timeout=10,
        )
        assert r.status_code == 200, r.text
        last = r.json()
        if last["query_status"] in ("done", "failed"):
            return last
        time.sleep(2)
    raise TimeoutError(f"Query {query_id} did not finish. Last={last}")


def get_transactions(base_url: str, user: ApiUser) -> list[dict]:
    """
    Тестит получение списка транзакций
    """
    r = requests.get(f"{base_url}/transactions", headers=api_headers(user), timeout=10)
    assert r.status_code == 200, r.text
    return r.json()


def get_search_history(base_url: str, user: ApiUser) -> list[dict]:
    """
    Тестит получение истории поиска
    """
    r = requests.get(f"{base_url}/search/history", headers=api_headers(user), timeout=10)
    assert r.status_code == 200, r.text
    return r.json()


def test_authorization(base_url, fresh_user):
    # Созданый пользователь должен быть авторизован и /me должен его возвращать
    me = get_me(base_url, fresh_user)
    assert me["login"] == fresh_user.login

    # повторная авторизация должна работать
    r2 = requests.post(
        f"{base_url}/auth/login",
        data={"username": fresh_user.login, "password": fresh_user.password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    assert r2.status_code == 200
    assert r2.json()["access_token"]

    # неверный пароль
    r_bad = requests.post(
        f"{base_url}/auth/login",
        data={"username": fresh_user.login, "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    # ежли предоставили неверный пароль- должны дать отлуп
    assert r_bad.status_code == 401


def test_balance_add(base_url, fresh_user):
    """
    Тестирование добавления баланса
    """
    me0 = get_me(base_url, fresh_user)
    assert Decimal(me0["balance"]) == Decimal("0.00")

    add_credit(base_url, fresh_user, Decimal("5.00"))
    me1 = get_me(base_url, fresh_user)
    assert Decimal(me1["balance"]) == Decimal("5.00")


def test_upload_debit(base_url, fresh_user):
    """
    Тестирование списания кредитов за аплоад документов + что образовываются транзакции
    """
    add_credit(base_url, fresh_user, Decimal("3.00"))

    doc_id = upload_doc(base_url, fresh_user, title="Cats", content="Cats are wonderful animals")
    status_ = wait_doc_indexed(base_url, fresh_user, doc_id)
    assert status_ == "indexed"

    # 3.00 - 1.00 за загрузку
    me = get_me(base_url, fresh_user)
    assert Decimal(me["balance"]) == Decimal("2.00")

    transactions = get_transactions(base_url, fresh_user)
    reasons = [t["reason"] for t in transactions]
    assert "credit_add" in reasons
    assert "document_upload" in reasons


def test_search_debit(base_url, fresh_user):
    """
    Тестирование списания кредитов за поиск + что образовываются транзакции
    """
    add_credit(base_url, fresh_user, Decimal("5.00"))

    # чтобы поиск вернул результаты — загружаем 2 документа и ждём индексации
    d1 = upload_doc(base_url, fresh_user, title="Cats", content="Cats are wonderful animals")
    d2 = upload_doc(base_url, fresh_user, title="Dogs", content="Dogs are loyal friends")
    assert wait_doc_indexed(base_url, fresh_user, d1) == "indexed"
    assert wait_doc_indexed(base_url, fresh_user, d2) == "indexed"

    bal_before = Decimal(get_me(base_url, fresh_user)["balance"])

    qid = create_search(base_url, fresh_user, "cats animals", top_k=5)
    result = wait_search_done(base_url, fresh_user, qid)
    assert result["query_status"] == "done"
    assert isinstance(result["items"], list)
    # ожидаем хотя бы один результат (Cats)
    assert any("cat" in i["title"].lower() for i in result["items"])

    bal_after = Decimal(get_me(base_url, fresh_user)["balance"])
    # 1.00 списывается за поиск
    assert bal_after == bal_before - Decimal("1.00")

    txs = get_transactions(base_url, fresh_user)
    assert any(t["reason"] == "search_query" for t in txs)

    history = get_search_history(base_url, fresh_user)
    assert any(h["query"]["id"] == qid for h in history)


def test_insufficient_balance(base_url, fresh_user):
    """
    Тест на отлуп при недостаточном балансе
    """
    # баланс = 0
    me0 = get_me(base_url, fresh_user)
    assert Decimal(me0["balance"]) == Decimal("0.00")

    r = requests.post(
        f"{base_url}/search",
        json={"query_text": "cats", "top_k": 5},
        headers=api_headers(fresh_user),
        timeout=10,
    )
    assert r.status_code == 409, r.text

    me1 = get_me(base_url, fresh_user)
    assert Decimal(me1["balance"]) == Decimal("0.00")


def test_search_invalid_inpput(base_url, fresh_user):
    """
    Проверка что если параметры поиска некорректны, будет отлуп (пока что только top-k = 0)
    """
    add_credit(base_url, fresh_user, Decimal("2.00"))
    bal_before = Decimal(get_me(base_url, fresh_user)["balance"])

    # top_k=0 нарушает валидацию (Field ge=1)
    r = requests.post(
        f"{base_url}/search",
        json={"query_text": "cats", "top_k": 0},
        headers=api_headers(fresh_user),
        timeout=10,
    )
    assert r.status_code == 422

    bal_after = Decimal(get_me(base_url, fresh_user)["balance"])
    assert bal_after == bal_before
