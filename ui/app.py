from __future__ import annotations

import streamlit as st
import os

from api_client import ApiClient
from rendering.admin_page import render_admin_page
from rendering.ui_rendering import render_login_form, refresh_me, render_left_menu, render_search_history, render_search, render_documents, render_transactions, API_INTERNAL

st.set_page_config(page_title="Semantic Search UI", layout="wide")


if "api_url" not in st.session_state:
    st.session_state.api_url = API_INTERNAL

if "client" not in st.session_state:
    st.session_state.client = ApiClient(base_url=st.session_state.api_url)

client: ApiClient = st.session_state.client

if not client.token:
    # ---- AUTH ----
    render_login_form()
    st.stop()

if client.token and "me" not in st.session_state:
    try:
        refresh_me()
    except Exception as e:
        st.error(str(e))

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
elif selected == "Admin":
    render_admin_page(client)

