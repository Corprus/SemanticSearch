from __future__ import annotations

import pandas as pd
import streamlit as st
import time
import os

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from api_client import ApiClient
import re


API_INTERNAL = os.getenv("API_BASE_URL", "http://web-proxy/api")
API_PUBLIC = os.getenv("API_BASE_URL_PUBLIC", "http://localhost/api")

if "api_url" not in st.session_state:
    st.session_state.api_url = API_INTERNAL

if "client" not in st.session_state:
    st.session_state.client = ApiClient(base_url=st.session_state.api_url)

client: ApiClient = st.session_state.client

_TIME_ONLY_RE = re.compile(r"^\d{2}:\d{2}:\d{2}$")

def set_api_url(url: str) -> None:
    st.session_state.api_url = url
    st.session_state.client = ApiClient(base_url=url, token=client.token)


def format_ts(ts) -> str:
    if ts is None:
        return "-"

    # если это "HH:MM:SS" (как твои *_ts) — оставляем как есть
    if isinstance(ts, str) and _TIME_ONLY_RE.match(ts.strip()):
        return ts.strip()

    # всё остальное пробуем распарсить как дату/время
    dt = pd.to_datetime(ts, utc=True, errors="coerce")
    if pd.isna(dt):
        return str(ts)

    # красиво в МСК
    return dt.tz_convert("Europe/Moscow").strftime("%d.%m.%Y %H:%M:%S")

def get_doc_ts(doc: dict) -> str | None:
    return (
        doc.get("created_at")
        or doc.get("indexed_at")
    )

def refresh_me():
    try:
        st.session_state["me"] = client.get_me()
        st.session_state["me_ts"] = time.strftime("%H:%M:%S")
    except Exception as e:
        st.session_state.access_token = None
        client.set_token(None)
        st.error(f"failed to load profile: {e}")
        st.rerun()
def refresh_documents():
    st.session_state["documents"] = client.list_documents()
    st.session_state["documents_ts"] = time.strftime("%H:%M:%S")

def refresh_history():
    st.session_state["search_history"] = client.get_search_history()
    st.session_state["history_ts"] = time.strftime("%H:%M:%S")

def refresh_transactions():
    st.session_state["transactions"] = client.list_transactions()
    st.session_state["tx_ts"] = time.strftime("%H:%M:%S")

def make_preview(text: str, n: int = 180) -> str:
    if not text:
        return ""
    t = text.strip().replace("\n", " ")
    return t if len(t) <= n else t[:n] + "…"

def parse_amount(value: str) -> Decimal | None:
    try:
        amount = Decimal(value.strip())
        if amount <= 0:
            return None
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return None
