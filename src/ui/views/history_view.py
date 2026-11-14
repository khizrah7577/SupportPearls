"""Conversation history management."""

from __future__ import annotations

import streamlit as st

from src.storage.conversations import ConversationStore


CATEGORIES = ["general", "warranty", "shipping", "pricing", "troubleshooting", "policy"]


def render_history() -> None:
    user = st.session_state.user
    store = ConversationStore()
    user_id = int(user["id"])

    st.markdown(
        '<div class="topbar"><div class="topbar-brand">Conversation <span>History</span></div></div>',
        unsafe_allow_html=True,
    )

    q = st.text_input("Search conversations", placeholder="Search titles or message text…")
    conversations = store.list_for_user(user_id, query=q or None, limit=100)

    if not conversations:
        st.info("No conversations found.")
        if st.button("Start a chat", type="primary"):
            st.session_state.page = "chat"
            st.session_state.active_conversation_id = None
            st.rerun()
        return

    for conv in conversations:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([0.42, 0.18, 0.2, 0.2])
            with c1:
                st.markdown(f"**{conv.title}**")
                st.caption(f"{conv.message_count} msgs · updated {conv.updated_at}")
            with c2:
                new_cat = st.selectbox(
                    "Category",
                    CATEGORIES,
                    index=CATEGORIES.index(conv.category)
                    if conv.category in CATEGORIES
                    else 0,
                    key=f"cat_{conv.id}",
                    label_visibility="collapsed",
                )
                if new_cat != conv.category:
                    store.set_category(conv.id, user_id, new_cat)
            with c3:
                if st.button("Open", key=f"hist_open_{conv.id}", use_container_width=True):
                    st.session_state.page = "chat"
                    st.session_state.active_conversation_id = conv.id
                    st.rerun()
            with c4:
                if st.button("Delete", key=f"hist_del_{conv.id}", use_container_width=True):
                    store.delete(conv.id, user_id)
                    if st.session_state.get("active_conversation_id") == conv.id:
                        st.session_state.active_conversation_id = None
                    st.rerun()

            with st.expander("Rename"):
                new_title = st.text_input(
                    "Title", value=conv.title, key=f"title_{conv.id}"
                )
                if st.button("Save title", key=f"save_title_{conv.id}"):
                    store.rename(conv.id, user_id, new_title)
                    st.rerun()
