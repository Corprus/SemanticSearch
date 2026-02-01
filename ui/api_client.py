from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
from decimal import Decimal

import requests


class ApiError(RuntimeError):
    pass


@dataclass
class ApiClient:
    base_url: str
    token: Optional[str] = None

    def set_token(self, token: str) -> None:
        self.token = token

    def clear_token(self) -> None:
        self.token = None

    def _headers(self) -> Dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def login_oauth_password(self, username: str, password: str) -> str:
        """
        OAuth2 password flow: application/x-www-form-urlencoded
        """

        resp = requests.post(
            f"{self.base_url}/auth/login",
            data={"username": username, "password": password},
            timeout=15,
        )
        if resp.status_code != 200:
            raise ApiError(f"Login failed: {resp.status_code} {resp.text}")

        data = resp.json()
        token = data.get("access_token")
        if not token:
            raise ApiError(f"Invalid login response: {data}")
        return token

    def health(self) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/health", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def upload_document_text(self, title, content: str) -> Dict[str, Any]:
        resp = requests.put(
            f"{self.base_url}/documents",
            json={"content": content, "title" : title},
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code != 200:
            raise ApiError(f"Upload text failed: {resp.status_code} {resp.text}")
        return resp.json()

    def upload_document_file(self, file_name:str, title: str, file_bytes: bytes) -> Dict[str, Any]:
        files = {"file": (file_name, file_bytes)}
        resp = requests.post(
            f"{self.base_url}/documents/upload",
            files=files,
            json={"title" : title},
            headers=self._headers(),
            timeout=60,
        )
        if resp.status_code != 200:
            raise ApiError(f"Upload file failed: {resp.status_code} {resp.text}")
        return resp.json()

    def search(self, query_text: str, top_k: int) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/search",
            json={"query_text": query_text, "top_k": top_k},
            headers=self._headers(),
            timeout=60,
        )
        if resp.status_code != 200:
            raise ApiError(f"Search failed: {resp.status_code} {resp.text}")
        return resp.json()
    
    def get_search(self, query_id: str) -> dict:
        resp = requests.get(
            f"{self.base_url}/search/{query_id}",
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code != 200:
            raise ApiError(f"Get search failed: {resp.status_code} {resp.text}")
        return resp.json()
    
        
    def get_search_results(self, query_id: str) -> list[dict]:
        resp = requests.get(f"{self.base_url}/search/{query_id}/results", headers=self._headers(), timeout=30)
        resp.raise_for_status()
        if resp.status_code != 200:
            raise ApiError(f"Get search failed: {resp.status_code} {resp.text}")
        return resp.json()
    
    
    def get_query(self, query_id: str) -> Dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/search/{query_id}",
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_document(self, document_id: str) -> Dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/documents/{document_id}",
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    
    def get_me(self) -> dict:
        resp = requests.get(
            f"{self.base_url}/users/me",
            headers=self._headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    
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

    def logout(self):
        self.token = None

    def list_documents(self) -> list[dict]:
        resp = requests.get(f"{self.base_url}/documents", headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_search_history(self) -> list[dict]:
        resp = requests.get(f"{self.base_url}/search/history", headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()



    def list_transactions(self) -> list[dict]:
        resp = requests.get(f"{self.base_url}/transactions", headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()  