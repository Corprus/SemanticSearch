from __future__ import annotations
from typing import Any, Dict, List

import pandas as pd
import streamlit as st
import os
import time

from streamlit_option_menu import option_menu

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
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
    st.session_state["me_ts"] = time.strftime("%H:%M:%S")

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

def set_api_url(url: str) -> None:
    st.session_state.api_url = url
    st.session_state.client = ApiClient(base_url=url, token=client.token)

def render_search_results(data: dict):
    status = (data.get("query_status") or "unknown").lower()
    items = data.get("items") or []

    badge = {"done":"✅ done","pending":"⏳ pending","processing":"⏳ processing","failed":"❌ failed"}.get(status, status)
    st.caption(f"Status: {badge} • items: {len(items)}")

    if not items:
        st.info("No results yet.")
        return

    df = pd.DataFrame([{
        "rank": it.get("rank"),
        "score": it.get("score"),
        "title": it.get("title"),
        "document_id": it.get("document_id"),
    } for it in items]).sort_values("rank")

    st.dataframe(df, use_container_width=True, hide_index=True)

    doc_id = st.selectbox("Open document", [""] + [it["document_id"] for it in items])
    if doc_id:
        doc = client.get_document(doc_id)
        st.markdown(f"### {doc.get('title','')}")
        st.caption(f"index_status: {doc.get('index_status')}")
        st.write(doc.get("content",""))

def render_upload():
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
                refresh_me()
                refresh_documents()
                st.success(f"Uploaded: {res['title']} • status: {res['index_status']}")
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
                    res = client.upload_document_file(file_name=file.name, file_bytes=file.getvalue(), title=title, mime_type = file.type)
                    refresh_me()
                    refresh_documents()
                    st.success(f"Uploaded: {res['title']} • status: {res['index_status']}")
                except ApiError as e:
                    st.error(str(e))

def ensure_history_loaded():
    if "search_history" not in st.session_state:
        refresh_history()

def render_search():
    st.header("Search")

    column_query, column_topk, column_run = st.columns([6, 1.5, 1.5])
    with column_query:
        query_text = st.text_input(
            "Query",
            value="",
            placeholder="Type your query…",
            label_visibility="collapsed",
            key="search_query",
        )
    with column_topk:
        top_k = st.number_input(
            "Top K",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            label_visibility="collapsed",
            key="search_topk",
        )
    with column_run:
        run = st.button("Run", use_container_width=True)

    colA, colB = st.columns([1, 1])
    with colA:
        auto = st.toggle("Auto-refresh", value=True)
    with colB:
        refresh_btn = st.button("Refresh results")

    if run:
        try:
            res = client.search(query_text=query_text, top_k=top_k)
            st.session_state["last_query_id"] = res["query_id"]
            refresh_me()  # сразу обновим баланс (списание)
            st.success(f"Created query: {res['query_id']}")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    query_id = st.session_state.get("last_query_id")
    if not query_id:
        st.info("Run search to get query_id.")
    else:
        st.caption(f"Query ID: {query_id}")
        try:
            data = client.get_search_results(query_id)
            items = data.get("items") or []
            render_results_with_documents(client, items, cache_prefix=f"q_{query_id}")
            status = (data.get("query_status") or "unknown").lower()
            if (auto and status != "done") or refresh_btn:
                time.sleep(1 if auto else 0)
                if auto:
                    st.rerun()
        except Exception as e:
            st.error(str(e))

def render_search_history():

    with st.spinner("Loading history..."):
        ensure_history_loaded()

    history = st.session_state.get("search_history") or []
    st.caption(f"updated: {st.session_state.get('history_ts','-')} • count: {len(history)}")

    if not history:
        st.info("No searches yet.")
    else:
        st.subheader("Search history")

        # автозагрузка
        if "search_history" not in st.session_state:
            refresh_history()

        history = st.session_state.get("search_history") or []
        render_history_as_cards(history)

def normalize_search_payload(data: dict) -> dict:
    return {
        "query_id": data.get("query_id", ""),
        "status": data.get("query_status", "unknown"),
        "items": data.get("items", []),
    }

def render_login_form():
    st.subheader("Login")
    with st.form("auth_form", clear_on_submit=False):
        username = st.text_input("Username", key="auth_username")
        password = st.text_input("Password", type="password", key="auth_password")

        c1, c2 = st.columns(2)
        with c1:
            do_login = st.form_submit_button("Sign in", use_container_width=True)
        with c2:
            do_signup = st.form_submit_button("Create user", use_container_width=True)

    if do_signup:
        try:
            client.create_user(username=username, password=password)  # см. ниже ApiClient
            st.success("User created")

            # опционально: сразу логиним
            token = client.login_oauth_password(username, password)
            client.set_token(token)
            refresh_me()
            st.rerun()

        except Exception as e:
            st.error(str(e))

    if do_login:
        try:
            token = client.login_oauth_password(username, password)
            client.set_token(token)
            refresh_me()
            st.rerun()
        except Exception as e:
            st.error(str(e))

def render_pop_over():
    me = st.session_state.get("me")
    if not me:
        return
    with st.popover(f"👤 {me['login']} ({me["balance"]})"):
        st.caption(me["role"])
        st.metric("Balance", me["balance"])

        st.markdown("**Add credits**")
        col_amount, col_add_cred, col_transactions = st.columns([3, 1, 1])

        with col_amount:
            amount_raw = st.text_input(
                "amount",
                placeholder="1.00",
                label_visibility="collapsed",
                key="popover_amount",
            )

        with col_add_cred:
            if st.button("➕", help="Add credits", key="popover_add"):
                amount = parse_amount(amount_raw)
                if amount is None:
                    st.warning("Invalid amount")
                else:
                    client.add_credit(amount)
                    refresh_me()
                    st.rerun()

        with col_transactions:
            if st.button("📜", help="Transactions", key="popover_tx"):
                st.session_state["page"] = "Transactions"
                st.rerun()

        st.divider()
        col_logout, col_refresh = st.columns([1,1])
        with col_logout:
            if st.button("🚪 Logout", key="popover_logout"):
                logout()
                st.rerun()
        with col_refresh:
            if st.button("↻ Refresh account"):
                refresh_me()
                st.rerun()   

def logout():
    client.logout()
    for k in ["me", "Documents", "Search History", "Transactions"]:
        st.session_state.pop(k, None)
    st.rerun()    


def render_left_menu():
    with st.sidebar:
        render_pop_over()

        options = ["Search", "Documents", "Transactions"]
        icons = ["search", "file-earmark-text", "credit-card"]

        current = st.session_state.get("page", "Search")
        default_index = options.index(current) if current in options else -1

        selected = option_menu(
            menu_title=None,
            options=options,
            icons=icons,
            default_index=default_index,
        )

        if selected != current and selected != -1:
            st.session_state["page"] = selected
            st.rerun()
    

def render_documents():
    st.subheader("Documents")
    with st.expander("Upload new document", expanded=False):
        render_upload()
    if st.button("🔄 Refresh documents"):
        refresh_documents()
        st.rerun()

    if "documents" not in st.session_state:
        try:
            refresh_documents()
        except Exception as e:
            st.error(str(e))

    docs = st.session_state.get("documents") or []
    st.caption(f"updated: {st.session_state.get('documents_ts','-')} • count: {len(docs)}")

    if not docs:
        st.info("No documents.")
    else:
        statuses = sorted({d.get("index_status","") for d in docs})
        status_filter = st.selectbox("Filter by index_status", ["(all)"] + statuses)

        filtered = docs if status_filter == "(all)" else [d for d in docs if d.get("index_status") == status_filter]

        df = pd.DataFrame([{
            "title": d.get("title"),
            "text": make_preview(d.get("content","")),
            "indexed": d.get("index_status") == "indexed"
#            "document_id": d.get("id"),
        } for d in filtered])

        st.dataframe(df, use_container_width=True, hide_index=True)

        # selected = st.selectbox("Open document", [""] + [d["id"] for d in filtered])
        # if selected:
        #     d = next((x for x in filtered if x["id"] == selected), None)
        #     if d:
        #         st.markdown(f"### {d.get('title','')}")
        #         st.caption(f"index_status: {d.get('index_status')}")
        #         st.write(d.get("content",""))


def render_transactions():
    st.subheader("Transactions")
    if st.button("🔄 Refresh transactions"):
        refresh_transactions()
        st.rerun()

    if "transactions" not in st.session_state:
        try:
            refresh_transactions()
        except Exception as e:
            st.error(str(e))

    txs = st.session_state.get("transactions") or []
    st.caption(f"updated: {st.session_state.get('tx_ts','-')} • count: {len(txs)}")

    if not txs:
        st.info("No transactions.")
    else:
        reasons = sorted({t.get("reason","") for t in txs})
        reason_filter = st.selectbox("Filter by reason", ["(all)"] + reasons)

        filtered = txs if reason_filter == "(all)" else [t for t in txs if t.get("reason") == reason_filter]

        df = pd.DataFrame([{
            "timestamp": t.get("timestamp"),
            "amount": t.get("amount"),
            "type": t.get("reason"),
            #"reference_id": t.get("reference_id"),
            #"transaction_id": t.get("id"),
        } for t in filtered])

        st.dataframe(df, use_container_width=True, hide_index=True)

        ref = st.text_input("Open reference as document_id (optional)", value="")
        if ref.strip():
            try:
                doc = client.get_document(ref.strip())
                st.markdown(f"### {doc.get('title','')}")
                st.caption(f"index_status: {doc.get('index_status')}")
                st.write(doc.get("content",""))
            except Exception:
                st.info("reference_id is not a document id (or not accessible).")

def render_results_with_documents(client, items: list[dict], cache_prefix: str):
    """
    items: [{document_id, title, score, rank}]
    cache_prefix: уникальная строка, чтобы ключи не конфликтовали (например f"q_{query_id}")
    """
    if not items:
        st.info("No results.")
        return

    # Документы (вложенные expanders)
    st.markdown("### Search results")
    for it in items:
        doc_id = it.get("document_id")
        title = it.get("title") or it.get("document_title") or "(untitled)"
        score = it.get("score")
        rank = it.get("rank")

        label = f"📄 #{rank} • {title}"
        if score is not None:
            label += f" (score {round(float(score), 4)})"

        with st.expander(label, expanded=False):
            # cache per doc, per query context
            key = f"{cache_prefix}_doc_{doc_id}"

            if key not in st.session_state:
                with st.spinner("Loading document..."):
                    doc = client.get_document(str(doc_id))
                    st.session_state[key] = doc

            doc = st.session_state[key]
            st.markdown(f"#### {doc.get('title','')}")
            st.caption(f"index_status: {doc.get('index_status')}")
            st.write(doc.get("content", ""))

def render_history_as_cards(history: list[dict]):
    if not history:
        st.info("No searches yet.")
        return

    for h in history:
        q = h["query"]
        items = h.get("items") or []

        with st.expander(f"🔎 {q['query_text']}", expanded=False):
            st.caption(f"{q['timestamp']} • results: {len(items)}")

            if not items:
                st.info("No results")
                continue

            df = pd.DataFrame([{
                "rank": it["rank"],
                "score": round(it["score"], 3),
                "title": it["document_title"],
            } for it in items]).sort_values("rank")

            st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown("### Documents")

            for it in items:
                doc_id = it["document_id"]
                title = it["document_title"]
                score = round(it["score"], 3)

                label = f"📄 {title} (score {score})"

                with st.expander(label, expanded=False):
                    # lazy-load документа
                    cache_key = f"doc_{doc_id}"

                    if cache_key not in st.session_state:
                        with st.spinner("Loading document..."):
                            doc = client.get_document(doc_id)
                            st.session_state[cache_key] = doc

                    doc = st.session_state[cache_key]

                    st.markdown(f"#### {doc['title']}")
                    st.caption(f"Index status: {doc['index_status']}")
                    st.write(doc["content"])


if not client.token:
    # ---- AUTH ----
    render_login_form()
    st.stop()


if client.token and "me" not in st.session_state:
    try:
        refresh_me()
    except Exception as e:
        st.error(str(e))

me = st.session_state.get("me")
render_left_menu()

selected = st.session_state.get("page")
# роутинг
if selected == "Search":
     st.subheader("Search")
     render_search()
     st.divider()
     st.subheader("Search history")
     render_search_history()
elif selected == "Documents":
    render_documents()
elif selected == "Transactions":
    render_transactions()


