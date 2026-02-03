import streamlit as st
import pandas as pd
from uuid import UUID
from decimal import Decimal
from rendering.ui_rendering import render_results_with_documents

def parse_uuid(value: str) -> UUID | None:
    try:
        v = value.strip()
        if not v:
            return None
        return UUID(v)
    except Exception:
        return None

def render_admin_page(client):
    st.header("Admin")

    me = st.session_state.get("me") or {}
    if str(me.get("role", "")).lower() != "admin":
        st.error("Access denied")
        return
    
     # --- USERS LIST ---
    st.subheader("Users")

    colA, colB = st.columns([1, 3])
    with colA:
        if st.button("🔄 Refresh users", use_container_width=True):
            st.session_state.pop("admin_users", None)
            st.rerun()

    # кешируем список пользователей, чтобы не дергать каждый ререндер
    if "admin_users" not in st.session_state:
        try:
            st.session_state["admin_users"] = client.list_users()
        except Exception as e:
            st.error(str(e))
            return

    users = st.session_state.get("admin_users") or []
    if not users:
        st.info("No users found.")
        return

    # Табличка
    df = pd.DataFrame([{
        "login": u.get("login"),
        "role": u.get("role"),
        "user_id": u.get("id"),
    } for u in users])

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Быстрый выбор target по login
    st.markdown("**Set target user**")
    options = [""] + [f"{u.get('login')} • {u.get('role')} • {u.get('id')}" for u in users]
    pick = st.selectbox("Pick user", options, index=0, label_visibility="collapsed", key="admin_pick_user")
    target_raw = st.session_state.get("admin_target_user_id") or ""

    if pick:
        # достаём id из строки (последний сегмент после " • ")
        target_id = pick.split(" • ")[-1].strip()
        if target_id != target_raw:
            st.session_state["admin_target_user_id"] = target_id
            st.rerun()

    st.divider()

    # --- Target user ---
    st.subheader("Target user")

    target_raw = st.text_input(
        "Target user_id",
        value=target_raw or "",
        placeholder="UUID of target user",
        key="admin_target_user_id_input",
    )

    target_user_id = parse_uuid(target_raw)
    if target_raw.strip() and target_user_id is None:
        st.warning("Invalid UUID")
        return

    if target_user_id is None:
        st.info("Enter target user_id to enable admin actions.")
        return

    st.session_state["admin_target_user_id"] = str(target_user_id)

    # --- Target summary ---
    c1, c2, c3 = st.columns([3, 2, 2])
    with c1:
        try:
            user = client.get_user(target_user_id)
            st.markdown(f"**User:** {user.get('login', '')}")
            st.caption(f"id: {user.get('id', '')}")
            st.caption(f"role: {user.get('role', '')}")
        except Exception as e:
            st.error(str(e))
            return

    with c2:
        try:
            bal = client.get_user_balance(target_user_id)
            # у тебя response_model может быть просто число/строка — подстрой если надо
            st.markdown("**Balance**")
            st.write(bal)
        except Exception as e:
            st.error(str(e))

    with c3:
        if st.button("🔄 Refresh target info", use_container_width=True):
            st.rerun()

    st.divider()

    # --- Credits ---
    st.subheader("Credits")

    cc1, cc2, cc3 = st.columns([3, 1.5, 1.5])
    with cc1:
        amount_raw = st.text_input(
            "Amount",
            value="1.00",
            label_visibility="collapsed",
            key="admin_amount",
            placeholder="1.00",
        )
    with cc2:
        do_credit = st.button("➕ Credit", use_container_width=True)
    with cc3:
        do_debit = st.button("➖ Debit", use_container_width=True)

    amount = None
    try:
        amount = Decimal(amount_raw)
    except Exception:
        amount = None

    if (do_credit or do_debit) and (amount is None or amount <= 0):
        st.warning("Amount must be a positive number")
        return

    if do_credit:
        try:
            client.credit_user(target_user_id, amount)
            st.success("Credited")
        except Exception as e:
            st.error(str(e))

    if do_debit:
        try:
            client.debit_user(target_user_id, amount)
            st.success("Debited")
        except Exception as e:
            st.error(str(e))

    st.divider()

    # --- Upload document for target ---
    st.subheader("Upload document for target")

    up1, up2 = st.columns(2)
    with up1:
        st.markdown("**Text upload**")
        title = st.text_input("Title", value="", key="admin_doc_title")
        content = st.text_area("Content", value="", height=180, key="admin_doc_content")
        if st.button("Upload text", key="admin_upload_text"):
            try:
                doc = client.upload_document_text(title=title, content=content, user_id=target_user_id)
                st.success(f"Uploaded: {doc.get('title','')}")
            except Exception as e:
                st.error(str(e))

    with up2:
        st.markdown("**File upload**")
        f = st.file_uploader("Choose file", type=["txt", "md", "json"], key="admin_file")
        if st.button("Upload file", key="admin_upload_file"):
            if not f:
                st.warning("Pick a file")
            else:
                try:
                    doc = client.upload_document_file(
                        file_name=f.name,
                        file_bytes=f.getvalue(),
                        mime_type=f.type,
                        title=title or None,
                        user_id=target_user_id,      # если твой upload endpoint принимает user_id — отлично
                    )
                    st.success(f"Uploaded: {doc.get('title','')}")
                except Exception as e:
                    st.error(str(e))

    st.divider()

    # --- Search as target ---
    st.subheader("Search as target")

    s1, s2, s3 = st.columns([6, 1.5, 1.5])
    with s1:
        qtext = st.text_input("Query", value="", label_visibility="collapsed", key="admin_q")
    with s2:
        top_k = st.number_input("Top K", min_value=1, max_value=20, value=5, step=1, label_visibility="collapsed", key="admin_topk")
    with s3:
        run = st.button("Run", use_container_width=True, key="admin_run_search")

    if run:
        try:
            res = client.search(query_text=qtext, top_k=int(top_k), user_id=target_user_id)
            st.session_state["admin_last_query_id"] = res["query_id"]
            st.success("Search started")
        except Exception as e:
            st.error(str(e))

    admin_qid = st.session_state.get("admin_last_query_id")
    if admin_qid:
        st.caption(f"Last query_id: {admin_qid}")
        try:
            results = client.get_search_results(admin_qid, user_id=target_user_id)
            # переиспользуй твой render_results_with_documents / render_results_with_documents(...)
            items = results.get("items") or []
            if items:
                render_results_with_documents(client, items, cache_prefix=f"admin_{admin_qid}")
            else:
                st.info(f"Status: {results.get('query_status')}")
        except Exception as e:
            st.error(str(e))
