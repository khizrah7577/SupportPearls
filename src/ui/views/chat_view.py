"""Premium chatbot interface wired to the existing RAG agent."""

from __future__ import annotations

import streamlit as st

from src.chains.schemas import DisplayResponse
from src.retrieval.vector_store import index_exists, read_index_meta
from src.services.agent_service import (
    clear_agent_cache,
    ensure_index,
    get_agent,
    get_runtime_settings,
    resolve_openai_api_key,
)
from src.storage.conversations import ConversationStore
from src.ui.components import SUGGESTED_PROMPTS, render_assistant_meta


def _ensure_conversation(store: ConversationStore, user_id: int) -> int:
    cid = st.session_state.get("active_conversation_id")
    if cid and store.get(int(cid), user_id):
        return int(cid)
    conv = store.create(user_id)
    st.session_state.active_conversation_id = conv.id
    return conv.id


def _ask_agent(question: str) -> DisplayResponse:
    from src.chains.schemas import Confidence

    agent = get_agent()
    if agent is None:
        return DisplayResponse(
            answer=(
                "The assistant is not ready. Add a valid OpenAI API key in Settings "
                "and ensure the knowledge index is built."
            ),
            citations=[],
            confidence=Confidence.none,
            answered=False,
            flags=["not_ready"],
            rewritten_query=question,
            original_query=question,
            refusal=True,
        )

    try:
        return agent.ask(question)
    except Exception as exc:  # noqa: BLE001
        return DisplayResponse(
            answer=f"I hit an error while answering: {exc}",
            citations=[],
            confidence=Confidence.none,
            answered=False,
            flags=["error"],
            rewritten_query=question,
            original_query=question,
            refusal=True,
        )


def render_chat() -> None:
    user = st.session_state.user
    user_id = int(user["id"])
    store = ConversationStore()
    settings = get_runtime_settings()
    meta = read_index_meta(settings.vector_store_path) or {}
    chunk_bit = f" · {meta.get('chunk_count')} chunks" if meta.get("chunk_count") else ""

    st.markdown(
        f"""
        <div class="topbar">
          <div class="topbar-brand">Support<span>Pearlz</span> Chat</div>
          <div class="topbar-meta" style="font-size:0.8rem;background:#fff;border:1px solid rgba(7,23,38,.12);
               padding:.35rem .7rem;border-radius:999px;color:#071726;">
            KB · {settings.vector_store_collection}{chunk_bit}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Toolbar
    t1, t2, t3, t4 = st.columns([1, 1, 1, 1])
    with t1:
        if st.button("New chat", use_container_width=True):
            agent = get_agent()
            if agent:
                agent.reset_session()
            conv = store.create(user_id)
            st.session_state.active_conversation_id = conv.id
            st.session_state.pending_prompt = None
            st.rerun()
    with t2:
        if st.button("Rebuild index", use_container_width=True):
            with st.spinner("Building knowledge index…"):
                clear_agent_cache()
                ok, msg = ensure_index(settings)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
    with t3:
        export = st.button("Export TXT", use_container_width=True)
    with t4:
        api_ready = bool(resolve_openai_api_key())
        index_ready = index_exists(
            settings.vector_store_path, settings.vector_store_collection
        )
        st.caption(
            ("API key ready" if api_ready else "API key missing")
            + " · "
            + ("Index ready" if index_ready else "Index missing")
        )

    if not resolve_openai_api_key():
        st.warning(
            "No OpenAI API key found. Add one in **Settings**, or set `OPENAI_API_KEY` "
            "in Streamlit secrets / `.env`."
        )

    if not index_exists(settings.vector_store_path, settings.vector_store_collection):
        st.warning(
            "Knowledge index is missing. Click **Rebuild index** (uses local HuggingFace "
            "embeddings by default) or run `python -m src.ingestion.build_index --rebuild`."
        )
        if st.button("Build index now", type="primary"):
            with st.spinner("Building index… first run may download the embedding model"):
                ok, msg = ensure_index(settings)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    cid = _ensure_conversation(store, user_id)
    conv = store.get(cid, user_id)
    if conv:
        rename_col, cat_col = st.columns([0.7, 0.3])
        with rename_col:
            new_title = st.text_input(
                "Conversation title",
                value=conv.title,
                key=f"chat_title_{cid}",
            )
            if new_title != conv.title:
                store.rename(cid, user_id, new_title)
        with cat_col:
            st.caption(f"Category: {conv.category}")

    messages = store.list_messages(cid, user_id)

    if export:
        text = store.export_text(cid, user_id)
        if text:
            st.download_button(
                "Download conversation",
                data=text,
                file_name=f"supportpearlz_{cid}.txt",
                mime="text/plain",
                use_container_width=True,
            )

    if not messages:
        st.markdown("##### Try asking")
        cols = st.columns(2)
        for i, prompt in enumerate(SUGGESTED_PROMPTS):
            with cols[i % 2]:
                if st.button(prompt, key=f"chat_sug_{i}", use_container_width=True):
                    st.session_state.pending_prompt = prompt
                    st.rerun()

    for msg in messages:
        with st.chat_message(msg.role):
            st.markdown(msg.content)
            if msg.role == "assistant":
                render_assistant_meta(msg.meta)
                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    if st.button("Copy", key=f"copy_{msg.id}"):
                        st.session_state[f"copied_{msg.id}"] = msg.content
                        st.toast("Response ready — select and copy from the message above.")
                with b2:
                    if st.button("Helpful", key=f"up_{msg.id}"):
                        store.set_feedback(msg.id, cid, user_id, 1)
                        st.toast("Thanks for the feedback.")
                with b3:
                    if st.button("Not helpful", key=f"down_{msg.id}"):
                        store.set_feedback(msg.id, cid, user_id, -1)
                        st.toast("Feedback saved.")
                with b4:
                    if st.button("Regenerate", key=f"regen_{msg.id}"):
                        # Find preceding user message
                        prior_user = None
                        for earlier in reversed(messages):
                            if earlier.id < msg.id and earlier.role == "user":
                                prior_user = earlier.content
                                break
                        if prior_user:
                            st.session_state.pending_prompt = prior_user
                            st.session_state.regenerate_of = msg.id
                            st.rerun()

    pending = st.session_state.pop("pending_prompt", None)
    user_text = st.chat_input("Ask about warranty, filters, shipping, returns…")
    question = pending or user_text
    if not question:
        return

    store.add_message(cid, user_id, role="user", content=question)
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching Pearlz knowledge…"):
            # Reset agent memory and replay history for condensation quality
            agent = get_agent()
            if agent is not None:
                agent.reset_session()
                history = store.list_messages(cid, user_id)
                # Replay all but the just-added user turn (last) into memory as pairs
                # Simpler: ask() uses current memory; seed with previous turns
                prior = [m for m in history if m.content != question or m.role != "user"]
                # Actually history already includes the new user message at end.
                prior = history[:-1]
                for i in range(0, len(prior) - 1, 2):
                    if prior[i].role == "user" and prior[i + 1].role == "assistant":
                        agent.memory.add_user(prior[i].content)
                        agent.memory.add_ai(prior[i + 1].content)
            resp = _ask_agent(question)
        st.markdown(resp.answer)
        render_assistant_meta(resp.model_dump())
        store.add_message(
            cid,
            user_id,
            role="assistant",
            content=resp.answer,
            meta=resp.model_dump(),
        )
