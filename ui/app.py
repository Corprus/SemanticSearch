from __future__ import annotations
from typing import Any, Dict, List

import pandas as pd
import streamlit as st
import os
import time

from decimal import Decimal, InvalidOperation
from api_client import ApiClient, ApiError

st.set_page_config(page_title="Semantic Search UI", layout="wide")

API_INTERNAL = os.getenv("API_BASE_URL", "http://web-proxy/api")
API_PUBLIC = os.getenv("API_BASE_URL_PUBLIC", "http://localhost/api")
if "api_url" not in st.session_state:
    st.session_state.api_url = API_INTERNAL

if "client" not in st.session_state:
    st.session_state.client = ApiClient(base_url=st.session_state.api_url)

client: ApiClient = st.session_state.client

def refresh_me():
    st.session_state["me"] = client.get_me()

def set_api_url(url: str) -> None:
    st.session_state.api_url = url
    st.session_state.client = ApiClient(base_url=url, token=client.token)

def render_search_results(client: ApiClient, query_data: dict):
    base_url = API_PUBLIC
    norm = normalize_search_payload(query_data)
    query_id = norm["query_id"]
    status = str(norm["status"]).lower()
    items = norm["items"]

    badge = {
        "done": "✅ done",
        "processing": "⏳ processing",
        "pending": "⏳ pending",
        "failed": "❌ failed",
        "error": "❌ error",
    }.get(status, f"ℹ️ {status}")

    st.subheader("Search results")
    st.caption(f"Query ID: {query_id} • Status: {badge}")

    if not items:
        st.info("Результатов пока нет.")
        return

    # Таблица
    df = pd.DataFrame([{
        "rank": it.get("rank"),
        "score": it.get("score"),
        "document_id": it.get("document_id"),
    } for it in items]).sort_values("rank")

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Open document")

    for it in items:
        doc_id = it.get("document_id")
        rank = it.get("rank")
        score = it.get("score")

        with st.expander(f"#{rank} • score={score} • {doc_id}", expanded=False):
            # 1) Ссылка на API (кликабельная)
            api_doc_url = f"{base_url}/documents/{doc_id}"
            st.link_button("Open in API", api_doc_url)

            # 2) Загрузить и показать контент документа
            if st.button("Fetch and show document", key=f"fetch_doc_{doc_id}"):
                doc = client.get_document(str(doc_id))
                # подстрой ключ под твой ответ документа:
                content = doc.get("content") or doc.get("text") or doc.get("document_text")
                if content:
                    st.markdown("**Content**")
                    st.write(content)
                else:
                    st.warning("В ответе документа нет поля content/text. Показываю raw JSON.")
                    st.json(doc)

def normalize_search_payload(data: dict) -> dict:
    return {
        "query_id": data.get("query_id", ""),
        "status": data.get("query_status", "unknown"),
        "items": data.get("items", []),
    }

# ---- AUTH ----
if not client.token:
    st.subheader("Login")
    c1, c2 = st.columns(2)
    with c1:
        username = st.text_input("Username", value="")
    with c2:
        password = st.text_input("Password", value="", type="password")

    if st.button("Sign in"):
        try:
            token = client.login_oauth_password(username=username, password=password)
            client.set_token(token)
            st.success("Logged in")
            st.rerun()
        except ApiError as e:
            st.error(str(e)) 
    st.stop()
else:
    with st.sidebar:
        st.header("Account")

        # грузим me один раз после логина
        if client.token and "me" not in st.session_state:
            try:
                refresh_me()
            except Exception as e:
                st.error(str(e))
        try:
            me = st.session_state.get("me")
            if me:
                st.write(f"👤 **{me['login']}** ({me['role']})")
                
                head1, head2 = st.columns(spec=[0.9, 0.2])
                with head1:
                    st.metric("Balance", me["balance"])
                with head2:
                    refresh_clicked = st.button("🔄", help="Refresh balance")

                if refresh_clicked:
                    refresh_me()
                    st.rerun()
                    
                st.divider()
                st.subheader("Add credits")

                col1, col2 = st.columns(spec=[0.9, 0.2])
                with col1:
                    amount_str = st.text_input("Amount", value="100.00", key="credit_amount", label_visibility="collapsed")                    
                with col2:
                    add_clicked = st.button("➕", help="Add credits")
                
                
                if st.button("🚪 Logout", use_container_width=True):
                    client.logout()
                    # чистим session_state
                    for k in ["me", "last_query_id"]:
                        st.session_state.pop(k, None)

                        st.success("Logged out")
                        st.rerun()

                if add_clicked:
                    try:
                        amount = Decimal(amount_str)
                        if amount <= 0:
                            st.error("Amount must be > 0")
                        else:
                            client.add_credit(amount)
                            st.success("Credits added")
                            refresh_me()
                            st.rerun()
                    except InvalidOperation:
                        st.error("Invalid amount format (e.g. 1.00)")
                    except Exception as e:
                        st.error(str(e))
        except Exception:
            st.warning("Not authenticated")



# ---- TABS ----
tab_upload, tab_search, tab_debug = st.tabs(["Upload", "Search", "Debug"])

with tab_upload:
    st.subheader("Upload document")
    
    st.markdown("### Title")
    title = st.text_input(
        "Document title",
        value="",
        key="document_title",
        label_visibility="collapsed",
    )
    left, right = st.columns(2)

    with left:
        st.markdown("### Text")
        content = st.text_area("Paste text", height=250)
        if st.button("Upload text"):
            try:
                res = client.upload_document_text(content=content, title=title)
                st.success("Uploaded")
                st.json(res)
            except ApiError as e:
                st.error(str(e))

    with right:
        st.markdown("### File")
        file = st.file_uploader("Choose a file", type=None)
        if st.button("Upload file"):
            if not file:
                st.warning("Pick a file first")
            else:
                try:
                    res = client.upload_document_file(file_name=file.name, file_bytes=file.getvalue(), title=title)
                    st.success("Uploaded")
                    st.json(res)
                except ApiError as e:
                    st.error(str(e))


with tab_search:
    st.subheader("Search")

    query = st.text_input("Query", value="")
    top_k = st.slider("Top K", min_value=1, max_value=20, value=5)

    col_a, col_b = st.columns([1, 1])
    with col_a:
        auto = st.toggle("Auto-refresh", value=True)
    with col_b:
        refresh = st.button("Refresh results")

    poll_interval = st.selectbox("Poll interval (sec)", [0.5, 1, 2], index=1, disabled=not auto)

    if st.button("Run search"):
        try:
            res = client.search(query_text=query, top_k=top_k)
            query_id = res["query_id"]
            st.session_state["last_query_id"] = query_id
            st.success(f"Created query: {query_id}")
        except ApiError as e:
            st.error(str(e))

    query_id = st.session_state.get("last_query_id")
    if not query_id:
        st.info("Запусти поиск, чтобы получить query_id.")
        st.stop()

    st.info(f"Tracking query_id: {query_id}")

    # Всегда пробуем получить текущий статус/результаты (один раз за прогон)
    try:
        data = client.get_search(query_id)  # <-- это GET /search/{query_id}
        render_search_results(client, data)  # <-- твоя красивая отрисовка
    except ApiError as e:
        st.error(str(e))
        st.stop()

    # Логика автообновления
    # - Refresh: кнопка просто приводит к rerun (Streamlit и так ререндерит после клика)
    # - Auto-refresh: делаем sleep + rerun
    if auto:
        time.sleep(float(poll_interval))
        st.rerun()

with tab_debug:
    st.subheader("Debug / Health")
    if st.button("GET /health"):
        try:
            st.json(client.health())
        except Exception as e:
            st.error(str(e))

    st.markdown("### Token (first 40 chars)")
    st.code((client.token[:40] + "...") if client.token else "no token")

