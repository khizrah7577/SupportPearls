"""SupportPearlz — premium Streamlit application entry point.

Run locally:
    streamlit run app.py

Streamlit Cloud: set Main file path to `app.py` and add OPENAI_API_KEY in Secrets.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.auth.db import init_db
from src.auth.service import AuthService
from src.ui.components import render_sidebar_nav
from src.ui.theme import inject_theme
from src.ui.views.auth_view import render_auth
from src.ui.views.chat_view import render_chat
from src.ui.views.dashboard_view import render_dashboard
from src.ui.views.history_view import render_history
from src.ui.views.settings_view import render_settings


def _init_session() -> None:
    defaults = {
        "authenticated": False,
        "user": None,
        "page": "dashboard",
        "auth_mode": "login",
        "auth_error": "",
        "auth_info": "",
        "active_conversation_id": None,
        "pending_prompt": None,
        "llm_model": "gpt-4o-mini",
        "remember_session": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _restore_user_if_needed() -> None:
    """Re-hydrate user object from DB when session has a user id."""
    user = st.session_state.get("user")
    if not user or not st.session_state.get("authenticated"):
        return
    fresh = AuthService().get_user(int(user["id"]))
    if fresh is None:
        st.session_state.authenticated = False
        st.session_state.user = None
        return
    st.session_state.user = fresh.to_dict()
    st.session_state.llm_model = fresh.preferred_model


def main() -> None:
    st.set_page_config(
        page_title="SupportPearlz",
        page_icon="💧",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_theme()
    init_db()
    _init_session()
    _restore_user_if_needed()

    if not st.session_state.authenticated or not st.session_state.user:
        render_auth()
        return

    with st.sidebar:
        user = st.session_state.user
        st.markdown(f"**{user.get('full_name', 'User')}**")
        st.caption(user.get("email", ""))
        st.divider()
        selected = render_sidebar_nav(st.session_state.page)
        if selected != st.session_state.page:
            st.session_state.page = selected
            st.rerun()
        st.divider()
        if st.button("Sign out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    page = st.session_state.page
    if page == "dashboard":
        render_dashboard()
    elif page == "chat":
        render_chat()
    elif page == "history":
        render_history()
    elif page == "settings":
        render_settings()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
