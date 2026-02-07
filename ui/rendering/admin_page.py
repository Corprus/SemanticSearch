import streamlit as st
from uuid import UUID
from decimal import Decimal
from api_client import ApiClient
from rendering.common import refresh_me

def parse_uuid(value: str) -> UUID | None:
    try:
        v = value.strip()
        if not v:
            return None
        return UUID(v)
    except Exception:
        return None
    
def render_admin_user_picker(client: ApiClient):
    if "admin_users" not in st.session_state:
        refresh_admin_users(client)

    users = st.session_state["admin_users"]

    options = {
        f"{u['login']} • {u['role']} • {u['id']}": u["id"]
        for u in users
    }

    label = st.selectbox(
        "Target user",
        [""] + list(options.keys()),
        key="admin_pick_user",
    )

    if label:
        user_id = UUID(options[label])
        if st.session_state.get("admin_target_user_id") != str(user_id):
            st.session_state["admin_target_user_id"] = str(user_id)
            refresh_admin_target(client, user_id)

def render_admin_target_summary():
    user = st.session_state.get("admin_target_user")
    balance = st.session_state.get("admin_target_balance")

    if not user:
        st.info("Select target user.")
        return False

    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown(f"**User:** {user['login']}")
        st.caption(f"id: {user['id']}")
        st.caption(f"role: {user['role']}")

    with c2:
        st.metric("Balance", balance)

    return True

def render_admin_credits(client: ApiClient):
    target_id = st.session_state.get("admin_target_user_id")
    if not target_id:
        return

    user_id = UUID(target_id)

    c1, c2, c3 = st.columns([3, 1.5, 1.5])
    with c1:
        amount_raw = st.text_input("Amount", "1.00", key="admin_amount")

    try:
        amount = Decimal(amount_raw)
        valid = amount > 0
    except Exception:
        valid = False

    with c2:
        do_credit = st.button("➕ Credit", use_container_width=True)
    with c3:
        do_debit = st.button("➖ Debit", use_container_width=True)

    if (do_credit or do_debit) and not valid:
        st.warning("Amount must be positive")
        return

    if do_credit:
        client.credit_user(user_id, amount)
        refresh_admin_target(client, user_id)
        st.success("Credited")

    if do_debit:
        client.debit_user(user_id, amount)
        refresh_admin_target(client, user_id)
        st.success("Debited")


def refresh_admin_users(client: ApiClient):
    st.session_state["admin_users"] = client.list_users()
    refresh_me()

def refresh_admin_target(client: ApiClient, user_id: UUID):
    st.session_state["admin_target_user"] = client.get_user(user_id)

    raw = client.get_user_balance(user_id)
    st.session_state["admin_target_balance"] = Decimal(raw["balance"])
    refresh_me()



def render_admin_page(client: ApiClient):
    st.header("Admin")

    me = st.session_state.get("me") or {}
    if me.get("role") != "admin":
        st.error("Access denied")
        return

    st.subheader("Users")
    if st.button("🔄 Refresh users"):
        refresh_admin_users(client)

    render_admin_user_picker(client)
    st.divider()

    st.subheader("Target user")
    has_target = render_admin_target_summary()
    if not has_target:
        return

    st.divider()
    st.subheader("Credits")
    render_admin_credits(client)

    st.divider()
    st.subheader("Upload document for target")
    # ← тут твой существующий код upload (он уже норм)

    st.divider()
    st.subheader("Search as target")
    # ← твой существующий search-код (он тоже норм)
