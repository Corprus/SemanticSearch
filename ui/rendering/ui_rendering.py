from __future__ import annotations

import pandas as pd
import streamlit as st
import time
from streamlit_option_menu import option_menu

from api_client import ApiClient, ApiError

import rendering.common

def render_results_with_documents(items: list[dict], cache_prefix: str):
    """
    Compact results list with expanders.
    items: [{document_id, title/document_title, score, rank}]
    """
    if not items:
        st.info("No results.")
        return

    st.markdown("### Results")

    # сортировка на всякий случай
    items_sorted = sorted(items, key=lambda x: (x.get("rank") is None, x.get("rank", 10**9)))

    for it in items_sorted:
        doc_id = it.get("document_id")
        title = it.get("title") or it.get("document_title") or "(untitled)"
        rank = it.get("rank")
        score = it.get("score")

        # компактный лейбл одной строкой
        parts = []
        if rank is not None:
            parts.append(f"**#{rank}**")
        parts.append(title)

        if score is not None:
            try:
                parts.append(f"`{float(score):.4f}`")
            except Exception:
                parts.append(f"`{score}`")

        label = " · ".join(parts)

        with st.expander(label, expanded=False):
            cache_key = f"{cache_prefix}_doc_{doc_id}"

            if cache_key not in st.session_state:
                with st.spinner("Loading document..."):
                    doc = rendering.common.client.get_document(str(doc_id))
                    st.session_state[cache_key] = doc

            doc = st.session_state[cache_key]

            # заголовок + контент
            if doc.get("title"):
                st.markdown(f"#### {doc.get('title')}")

            # если хочешь показывать статус индексации — раскомментируй
            # st.caption(f"index_status: {doc.get('index_status')}")

            st.write(doc.get("content", ""))

def render_left_menu():
    me = st.session_state.get("me") or {}
    with st.sidebar:
        render_pop_over()
        
        is_admin = str(me.get("role", "")).lower() == "admin"
        options = ["Search", "Documents", "Transactions"]
        icons = ["search", "file-earmark-text", "credit-card"]

        if is_admin:
            options.append("Admin")
            icons.append("shield-lock")

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

    col_refresh, col_filter = st.columns([1, 2])
    with col_refresh:
        if st.button("🔄 Refresh documents"):
            rendering.common.refresh_documents()
            st.rerun()

    if "documents" not in st.session_state:
        try:
            rendering.common.refresh_documents()
        except Exception as e:
            st.error(str(e))

    docs = st.session_state.get("documents") or []
    st.caption(
        f"updated: {rendering.common.format_ts(st.session_state.get('documents_ts'))} • count: {len(docs)}"
    )

    if not docs:
        st.info("No documents.")
        return

    # --- фильтр по статусу индексации ---
    statuses = sorted({d.get("index_status", "") for d in docs})
    with col_filter:
        status_filter = st.selectbox(
            "Filter by index status",
            ["(all)"] + statuses,
        )

    filtered = docs if status_filter == "(all)" else [
        d for d in docs if d.get("index_status") == status_filter
    ]

    # --- компактный список документов ---
    for d in filtered:
        doc_id = d.get("id")
        title = d.get("title") or "(untitled)"
        status = d.get("index_status", "unknown")

        # аккуратный статус
        status_badge = {
            "indexed": "✅ indexed",
            "processing": "⏳ processing",
            "pending": "⏳ pending",
            "failed": "❌ failed",
        }.get(status, status)

        ts_raw = rendering.common.get_doc_ts(d)
        ts_label = rendering.common.format_ts(ts_raw) if ts_raw else None

        parts = [title]

        if ts_label:
            parts.append(f"`{ts_label}`")

        parts.append(f"`{status_badge}`")

        label = " · ".join(parts)

        with st.expander(label, expanded=False):
            st.write(d.get("content", ""))

REASON_LABELS = {
    "search_query": "Search query",
    "document_upload": "Document upload",
    "credit_add": "Credit added",
    "credit_withdraw": "Debit"
}

def render_transactions():
    st.subheader("Transactions")
    if st.button("🔄 Refresh transactions"):
        rendering.common.refresh_transactions()
        st.rerun()

    if "transactions" not in st.session_state:
        try:
            rendering.common.refresh_transactions()
        except Exception as e:
            st.error(str(e))

    txs = st.session_state.get("transactions") or []
    st.caption(f"updated: {st.session_state.get('tx_ts','-')} • count: {len(txs)}")

    if not txs:
        st.info("No transactions.")
    else:
        txs = st.session_state.get("transactions") or []

        # --- humanize ---
        df = pd.DataFrame(txs)

        if not df.empty:
            # Timestamp: красиво
            # utc=True чтобы Z нормально распарсилось, потом можно в локаль +03:00
            ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
            df["Timestamp"] = ts.dt.tz_convert("Europe/Moscow").dt.strftime("%d.%m.%Y %H:%M:%S")

            # Amount: 2 знака
            df["Amount"] = pd.to_numeric(df["amount"], errors="coerce").map(lambda x: f"{x:.2f}" if pd.notna(x) else "")

            # Reason: читаемый текст
            df["Transaction Type"] = df["reason"].map(lambda r: REASON_LABELS.get(r, r))

            # Referenced ID
            df["Referenced ID"] = df["reference_id"].fillna("")

            # оставим только нужные колонки
            df = df[["Timestamp", "Amount", "Transaction Type", "Referenced ID"]]

        # --- dropdown reasons (тоже читаемо) ---
        reason_values = sorted({t.get("reason", "") for t in txs})
        reason_options = ["(all)"] + [REASON_LABELS.get(r, r) for r in reason_values]

        selected_label = st.selectbox("Filter by reason", reason_options)

        if selected_label != "(all)":
            # обратно из label -> reason
            label_to_reason = {REASON_LABELS.get(r, r): r for r in reason_values}
            selected_reason = label_to_reason.get(selected_label, selected_label)
            txs = [t for t in txs if t.get("reason") == selected_reason]

        # пересоберём df уже по filtered txs (чтобы таблица совпадала с фильтром)
        df = pd.DataFrame(txs)
        if not df.empty:
            ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
            df["Timestamp"] = ts.dt.tz_convert("Europe/Moscow").dt.strftime("%d.%m.%Y %H:%M:%S")
            df["Amount"] = pd.to_numeric(df["amount"], errors="coerce").map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
            df["Transaction Type"] = df["reason"].map(lambda r: REASON_LABELS.get(r, r))
            df["Referenced ID"] = df["reference_id"].fillna("")
            df = df[["Timestamp", "Amount", "Transaction Type", "Referenced ID"]]

        st.dataframe(df, use_container_width=True, hide_index=True)

def render_history_as_cards(history: list[dict]):
    if not history:
        st.info("No searches yet.")
        return

    # верхняя строка — аккуратная
    updated_raw = st.session_state.get("history_ts")
    st.caption(f"updated: {rendering.common.format_ts(updated_raw)} • count: {len(history)}")

    # последние запросы сверху
    for h in history:
        q = h.get("query", {})
        items = h.get("items") or []

        query_text = q.get("query_text", "")
        ts = q.get("timestamp")

        header_parts = []
        if query_text:
            header_parts.append(f"🔎 **{query_text}**")
        if ts:
            header_parts.append(f"`{rendering.common.format_ts(ts)}`")
        header_parts.append(f"{len(items)} results")

        header = " · ".join(header_parts)

        with st.expander(header, expanded=False):

            if not items:
                st.info("No results")
                continue

            # компактный список результатов — как в Search
            items_sorted = sorted(items, key=lambda x: (x.get("rank") is None, x.get("rank", 10**9)))

            for it in items_sorted:
                doc_id = it.get("document_id")
                title = it.get("document_title") or "(untitled)"
                rank = it.get("rank")
                score = it.get("score")

                parts = []
                if rank is not None:
                    parts.append(f"**#{rank}**")
                parts.append(title)
                if score is not None:
                    try:
                        parts.append(f"`{float(score):.4f}`")
                    except Exception:
                        parts.append(f"`{score}`")

                label = " · ".join(parts)

                with st.expander(label, expanded=False):
                    cache_key = f"hist_doc_{doc_id}"

                    if cache_key not in st.session_state:
                        with st.spinner("Loading document..."):
                            doc = rendering.common.client.get_document(str(doc_id))
                            st.session_state[cache_key] = doc

                    doc = st.session_state[cache_key]

                    if doc.get("title"):
                        st.markdown(f"#### {doc.get('title')}")

                    st.write(doc.get("content", ""))


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
                res = rendering.common.client.upload_document_text(content=content, title=title)
                rendering.common.refresh_me()
                rendering.common.refresh_documents()
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
                    res = rendering.common.client.upload_document_file(file_name=file.name, file_bytes=file.getvalue(), title=title, mime_type = file.type)
                    rendering.common.refresh_me()
                    rendering.common.refresh_documents()
                    st.success(f"Uploaded: {res['title']} • status: {res['index_status']}")
                except ApiError as e:
                    st.error(str(e))

def ensure_history_loaded():
    if "search_history" not in st.session_state:
        rendering.common.refresh_history()

def render_search():
    st.header("Search")

    with st.form("search_form", clear_on_submit=False):
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
            run = st.form_submit_button("Run", use_container_width=True)

    colA, colB = st.columns([1, 1])
    with colA:
        auto = st.toggle("Auto-refresh", value=True)
    with colB:
        refresh_btn = st.button("Refresh results")


    if run:
        try:
            # очистить результаты прошлого поиска (кеш документов по query)
            for k in list(st.session_state.keys()):
                if k.startswith("q_") and "_doc_" in k:
                    st.session_state.pop(k, None)

            # чтобы history обновилась заново для нового query_id
            st.session_state.pop("history_refreshed_for_query_id", None)

            # (опционально) визуально обнулить текущий query_id до получения нового
            st.session_state.pop("last_query_id", None)

            res = rendering.common.client.search(query_text=query_text, top_k=top_k)
            st.session_state["last_query_id"] = res["query_id"]
            rendering.common.refresh_me()  # сразу обновим баланс (списание)
            st.success(f"Created query: {res['query_id']}")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    query_id = st.session_state.get("last_query_id")
    if not query_id:
        ...
        #st.info("No search in")
    else:
        st.caption(f"Query ID: {query_id}")
        status_box = st.empty()
        results_box = st.empty()
        try:
            data = rendering.common.client.get_search_results(query_id)
            items = data.get("items") or []
            status = (data.get("query_status") or "unknown").lower()
            if status != "done":
                status_box.info("⏳ Идёт поиск…")
                results_box.empty()
            else:
                status_box.success("✅ Поиск завершён")
                last_refreshed = st.session_state.get("history_refreshed_for_query_id")
                with results_box.container():
                    render_results_with_documents(items, cache_prefix=f"q_{query_id}")
                if last_refreshed != query_id:
                    rendering.common.refresh_history()
                    st.session_state["history_refreshed_for_query_id"] = query_id

            if (auto and status != "done") or refresh_btn:
                time.sleep(1 if auto else 0)
                if auto:
                    st.rerun()
        except Exception as e:
            st.error(str(e))

def render_search_history():

    with st.spinner("Loading history..."):
        ensure_history_loaded()

        # автозагрузка
        if "search_history" not in st.session_state:
            rendering.common.refresh_history()
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
            rendering.common.client.create_user(username=username, password=password)  # см. ниже ApiClient
            st.success("User created")

            # опционально: сразу логиним
            token = rendering.common.client.login_oauth_password(username, password)
            st.session_state.access_token = token
            rendering.common.client.set_token(token)
            rendering.common.refresh_me()
            st.session_state["page"] = "Search"
            st.rerun()

        except Exception as e:
            st.error(str(e))

    if do_login:
        try:
            token = rendering.common.client.login_oauth_password(username, password)
            st.session_state.access_token = token
            rendering.common.client.set_token(token)
            rendering.common.refresh_me()
            st.session_state["page"] = "Search"
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
                amount = rendering.common.parse_amount(amount_raw)
                if amount is None:
                    st.warning("Invalid amount")
                else:
                    rendering.common.client.add_credit(amount)
                    rendering.common.refresh_me()
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
        with col_refresh:
            if st.button("↻ Refresh account"):
                rendering.common.refresh_me()
                st.rerun()   

def logout():
    client: ApiClient = st.session_state.client

    # server-side logout (вторично, но пусть будет)
    try:
        client.logout()
    except Exception:
        pass

    # источник истины
    st.session_state["access_token"] = None
    client.set_token(None)

    # основные ключи UI
    for k in [
        "me",
        "page",
        "last_query_id",
        "documents",
        "search_history",
        "transactions",
    ]:
        st.session_state.pop(k, None)

    # динамические кеши документов и поиска
    for k in list(st.session_state.keys()):
        if k.startswith(("doc_", "q_")):
            st.session_state.pop(k, None)

    st.rerun()

