import requests
import mimetypes
from decimal import Decimal
from typing import Optional
from uuid import UUID

class ApiError(RuntimeError):
    pass

class ApiClient:
    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def set_token(self, token: str) -> None:
        self.token = token

    def logout(self) -> None:
        self.token = None

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    # --- AUTH (oauth2 form) ---
    def login_oauth_password(self, username: str, password: str) -> str:
        resp = requests.post(
            f"{self.base_url}/auth/login",
            data={"username": username, "password": password},
            timeout=15,
        )
        if resp.status_code != 200:
            raise ApiError(f"Login failed: {resp.status_code} {resp.text}")
        data = resp.json()
        return data["access_token"]
    
    def create_user(self, username: str, password: str) -> dict:
        resp = requests.post(
            f"{self.base_url}/users",
            json={"login": username, "password": password},
            timeout=30,
        )
        if not (200 <= resp.status_code < 300):
            raise ApiError(f"Create user failed: {resp.status_code} {resp.text}")
        return resp.json()

    # --- ME / BALANCE ---
    def get_me(self) -> dict:
        resp = requests.get(
            f"{self.base_url}/users/me",
            headers=self._headers(),
            timeout=15,
        )
        if resp.status_code != 200:
            raise ApiError(f"Get me failed: {resp.status_code} {resp.text}")
        return resp.json()

    # --- CREDITS ---
    def add_credit(self, amount: Decimal) -> dict:
        resp = requests.post(
            f"{self.base_url}/transactions/credit",
            json={"amount": str(amount)},
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code != 200:
            raise ApiError(f"Add credit failed: {resp.status_code} {resp.text}")
        return resp.json()

    # --- DOCUMENTS ---
    def list_documents(self) -> list[dict]:
        resp = requests.get(
            f"{self.base_url}/documents",
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code != 200:
            raise ApiError(f"List documents failed: {resp.status_code} {resp.text}")
        return resp.json()

    def get_document(self, document_id: str, user_id: Optional[UUID] = None) -> dict:
        params = {}
        if user_id is not None:
            params["user_id"] = str(user_id)
        resp = requests.get(
            f"{self.base_url}/documents/{document_id}",
            params=params,
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code != 200:
            raise ApiError(f"Get document failed: {resp.status_code} {resp.text}")
        return resp.json()

    def upload_document_text(self, title: str, content: str, user_id: Optional[UUID] = None) -> dict:
        payload = {"title": title, "content": content}
        if user_id is not None:
            payload["user_id"] = str(user_id)
        resp = requests.put(
            f"{self.base_url}/documents",
            json=payload,
            headers=self._headers(),
            timeout=60,
        )
        if not (200 <= resp.status_code < 300):
            raise ApiError(f"Upload document failed: {resp.status_code} {resp.text}")
        return resp.json()
    
    def upload_document_file(self, file_name: str, file_bytes: bytes, mime_type: str | None, title: str | None = None) -> dict:
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(file_name)
        mime_type = mime_type or "application/octet-stream"

        files = {"file": (file_name, file_bytes, mime_type)}
        data = {}
        if title:
            data["title"] = title

        resp = requests.post(
            f"{self.base_url}/documents/upload",
            files=files,
            data=data,
            headers=self._headers(),
            timeout=120,
        )
        if not (200 <= resp.status_code < 300):
            raise ApiError(f"Upload file failed: {resp.status_code} {resp.text}")
        return resp.json()

    # --- SEARCH ---
    def search(self, query_text: str, top_k: int, user_id: Optional[UUID] = None) -> dict:
        payload = {"query_text": query_text, "top_k": top_k}
        if user_id is not None:
            payload["user_id"] = str(user_id)
        resp = requests.post(
            f"{self.base_url}/search",
            json=payload,
            headers=self._headers(),
            timeout=60,
        )
        if resp.status_code != 200:
            raise ApiError(f"Search failed: {resp.status_code} {resp.text}")
        return resp.json()

    def get_search_results(self, query_id: str, user_id: Optional[UUID] = None) -> dict:
        params = {}
        if user_id is not None:
            params["user_id"] = str(user_id)
        resp = requests.get(
            f"{self.base_url}/search/{query_id}/results",
            params=params,
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code != 200:
            raise ApiError(f"Get results failed: {resp.status_code} {resp.text}")
        return resp.json()

    def get_search_history(self) -> list[dict]:
        resp = requests.get(
            f"{self.base_url}/search/history",
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code != 200:
            raise ApiError(f"Search history failed: {resp.status_code} {resp.text}")
        return resp.json()

    # --- TRANSACTIONS ---
    def list_transactions(self) -> list[dict]:
        resp = requests.get(
            f"{self.base_url}/transactions",
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code != 200:
            raise ApiError(f"Transactions failed: {resp.status_code} {resp.text}")
        return resp.json()