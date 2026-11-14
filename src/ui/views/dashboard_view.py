"""Professional home dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.storage.conversations import ConversationStore
from src.ui.components import SUGGESTED_PROMPTS


def render_dashboard() -> None:
    user = st.session_state.user
    store = ConversationStore()
    stats = store.stats_for_user(int(user["id"]))
    recent = store.list_for_user(int(user["id"]), limit=5)

    st.markdown(
        f"""
        <div class="topbar">
          <div class="topbar-brand">Support<span>Pearlz</span></div>
        </div>
        <div class="welcome-banner">
          <h2>Welcome back, {user.get('full_name', 'there').split()[0]}</h2>
          <p>Your grounded Pearlz support workspace is ready. Ask product, warranty,
          shipping, and policy questions — every answer cites its source.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="stat-grid">
          <div class="stat-card"><div class="label">Conversations</div>
            <div class="value">{stats['conversations']}</div></div>
          <div class="stat-card"><div class="label">Messages</div>
            <div class="value">{stats['messages']}</div></div>
          <div class="stat-card"><div class="label">Questions asked</div>
            <div class="value">{stats['questions']}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1.1, 0.9], gap="large")
    with c1:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.markdown("### Open the assistant")
        st.caption("Start a grounded conversation with the Pearlz knowledge base.")
        if st.button("Start new chat", type="primary", use_container_width=True):
            st.session_state.page = "chat"
            st.session_state.active_conversation_id = None
            st.session_state.pending_prompt = None
            st.rerun()
        st.markdown("##### Suggested prompts")
        for i, prompt in enumerate(SUGGESTED_PROMPTS[:4]):
            if st.button(prompt, key=f"dash_prompt_{i}", use_container_width=True):
                st.session_state.page = "chat"
                st.session_state.pending_prompt = prompt
                st.session_state.active_conversation_id = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.markdown("### Activity (last 14 days)")
        activity = stats.get("activity") or []
        if activity:
            df = pd.DataFrame(activity)
            df = df.rename(columns={"day": "Day", "count": "Messages"})
            st.bar_chart(df.set_index("Day"))
        else:
            st.caption("No messages yet — your activity chart will appear here.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="history-card">', unsafe_allow_html=True)
        st.markdown("### Recent conversations")
        if not recent:
            st.caption("No conversations yet. Start your first chat.")
        else:
            for conv in recent:
                cols = st.columns([0.72, 0.28])
                with cols[0]:
                    st.markdown(f"**{conv.title[:48]}**")
                    st.caption(
                        f"{conv.message_count} messages · {conv.updated_at} · {conv.category}"
                    )
                with cols[1]:
                    if st.button("Open", key=f"open_conv_{conv.id}", use_container_width=True):
                        st.session_state.page = "chat"
                        st.session_state.active_conversation_id = conv.id
                        st.rerun()
        if st.button("View all history", use_container_width=True):
            st.session_state.page = "history"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.markdown("### Platform overview")
        st.markdown(
            """
            - Answers only from indexed Pearlz documents  
            - Citations with file + location  
            - Confidence signals and honest refusals  
            - Multi-turn follow-ups with query rewriting  
            """
        )
        st.markdown("</div>", unsafe_allow_html=True)
