"""Attractive Streamlit UI for SupportPearlz with runtime OpenAI API key login.

Run from project root:
    streamlit run app.py
"""

from __future__ import annotations

import hashlib
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.chains.rag_chain import SupportPearlzAgent, build_agent
from src.chains.schemas import Confidence, DisplayResponse
from src.config import Settings, settings_with_overrides
from src.retrieval.vector_store import index_exists, read_index_meta
from src.utils.logging_setup import setup_logging

# ---------------------------------------------------------------------------
# Visual system — light surfaces use black text; dark surfaces use white text
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&family=Syne:wght@600;700;800&display=swap');

:root {
  --black: #0a0a0a;
  --ink: #111111;
  --ink-soft: #222222;
  --muted: #333333;
  --white: #ffffff;
  --teal: #0f7f86;
  --teal-deep: #0a5c62;
  --line: rgba(0,0,0,0.14);
  --shadow: 0 18px 50px rgba(0,0,0,0.10);
}

html, body, .stApp, .stMarkdown, .stMarkdown p, .stCaption, label, p, li,
h1, h2, h3, h4, h5, h6 {
  font-family: 'Figtree', sans-serif !important;
  color: var(--black) !important;
}

.stApp {
  background:
    radial-gradient(1200px 600px at 12% -10%, rgba(184,228,225,0.85), transparent 55%),
    radial-gradient(900px 500px at 95% 8%, rgba(243,235,224,0.9), transparent 50%),
    linear-gradient(165deg, #f7fcfb 0%, #eaf4f3 42%, #f8f4ee 100%);
  background-attachment: fixed;
}

#MainMenu, footer, header { visibility: hidden; }
div[data-testid="stToolbar"], div[data-testid="stDecoration"] { display: none; }

/* Kill BaseWeb tooltip leftovers that print "visibility" over the password field */
div[role="tooltip"] { display: none !important; }
[data-baseweb="tooltip"] { display: none !important; }

section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #ffffff, #eef7f6);
  border-right: 1px solid var(--line);
}
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {
  color: var(--black) !important;
}

.login-shell {
  max-width: 960px;
  margin: 1.2rem auto 0;
  animation: rise 0.55s ease-out both;
}
.login-brand {
  font-family: 'Syne', sans-serif !important;
  font-weight: 800;
  font-size: clamp(2.4rem, 5.5vw, 3.8rem);
  letter-spacing: -0.04em;
  line-height: 0.95;
  color: var(--black) !important;
  margin: 0 0 0.75rem 0;
}
.login-brand span { color: var(--teal-deep) !important; }
.login-tag {
  font-size: 1.02rem;
  color: var(--ink-soft) !important;
  max-width: 36rem;
  line-height: 1.55;
  margin: 0 0 1.2rem 0;
}
.login-aside {
  padding: 1.25rem 1.2rem;
  background: #ffffff;
  border: 1px solid var(--line);
  border-radius: 18px;
  box-shadow: var(--shadow);
}
.login-aside h3 {
  font-family: 'Syne', sans-serif !important;
  font-size: 1.1rem;
  margin: 0 0 0.65rem 0;
  color: var(--black) !important;
}
.login-aside ul {
  margin: 0;
  padding-left: 1.1rem;
  color: var(--ink-soft) !important;
  line-height: 1.65;
  font-size: 0.94rem;
}
.login-aside li { color: var(--ink-soft) !important; }
.login-label {
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--black) !important;
  margin-bottom: 0.45rem;
}
.login-hint {
  font-size: 0.84rem;
  color: var(--muted) !important;
  margin-top: 0.75rem;
  line-height: 1.45;
}
.login-hint code {
  color: var(--black) !important;
  background: #eef2f2 !important;
  padding: 0.05rem 0.3rem;
  border-radius: 4px;
}
.pearl-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0.85rem 0 0.15rem;
}
.pearl-chip {
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--black) !important;
  background: #e4f3f2;
  border: 1px solid rgba(0,0,0,0.12);
  padding: 0.26rem 0.6rem;
  border-radius: 999px;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin: 0.15rem 0 0.85rem;
}
.topbar-brand {
  font-family: 'Syne', sans-serif !important;
  font-weight: 800;
  font-size: 1.5rem;
  letter-spacing: -0.03em;
  color: var(--black) !important;
}
.topbar-brand span { color: var(--teal-deep) !important; }
.topbar-meta {
  font-size: 0.8rem;
  color: var(--black) !important;
  background: #ffffff;
  border: 1px solid var(--line);
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
}
.hero-strip {
  background: #ffffff;
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 0.95rem 1.1rem;
  margin-bottom: 0.9rem;
  box-shadow: 0 10px 28px rgba(0,0,0,0.05);
}
.hero-strip h2 {
  font-family: 'Syne', sans-serif !important;
  font-size: 1.2rem;
  margin: 0 0 0.2rem 0;
  color: var(--black) !important;
}
.hero-strip p {
  margin: 0;
  color: var(--ink-soft) !important;
  font-size: 0.92rem;
}

div[data-testid="stChatMessage"] {
  background: #ffffff;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.3rem 0.5rem;
  margin-bottom: 0.5rem;
  box-shadow: 0 8px 20px rgba(0,0,0,0.04);
}
div[data-testid="stChatMessage"] p,
div[data-testid="stChatMessage"] span,
div[data-testid="stChatMessage"] li {
  color: var(--black) !important;
  line-height: 1.55;
}

.cite-box {
  margin-top: 0.65rem;
  padding: 0.7rem 0.85rem;
  border-radius: 12px;
  background: #f3faf9;
  border: 1px solid rgba(0,0,0,0.10);
}
.cite-box .title {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--black) !important;
  margin-bottom: 0.35rem;
}
.cite-item { font-size: 0.85rem; color: var(--black) !important; margin: 0.22rem 0; }
.cite-snip {
  display: block;
  color: var(--muted) !important;
  font-size: 0.78rem;
  margin-top: 0.08rem;
  font-style: italic;
}
.badge-row { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.55rem; }
.badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
}
.badge-high { background: var(--teal-deep); color: var(--white) !important; }
.badge-partial { background: #8a6418; color: var(--white) !important; }
.badge-none { background: #9a3d2a; color: var(--white) !important; }
.badge-rewrite { background: #1a1a1a; color: var(--white) !important; }

/* Light buttons → black text */
div.stButton > button {
  border-radius: 12px !important;
  font-weight: 700 !important;
  border: 1px solid rgba(0,0,0,0.16) !important;
  background: #ffffff !important;
  color: var(--black) !important;
}
div.stButton > button p,
div.stButton > button span,
div.stButton > button div { color: var(--black) !important; }

/* Dark primary → white text */
div.stButton > button[kind="primary"],
div.stButton > button[data-testid="baseButton-primary"],
button[kind="primary"] {
  background: linear-gradient(135deg, #0a5c62, #0f7f86) !important;
  color: var(--white) !important;
  border: none !important;
  box-shadow: 0 10px 24px rgba(15,127,134,0.28) !important;
}
div.stButton > button[kind="primary"] *,
div.stButton > button[data-testid="baseButton-primary"] *,
button[kind="primary"] * {
  color: var(--white) !important;
}

/* Inputs / selects — white bg, black text */
div[data-testid="stTextInput"] input,
div[data-baseweb="input"] input,
div[data-baseweb="select"] > div,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
textarea,
div[data-testid="stChatInput"] textarea {
  background: #ffffff !important;
  color: var(--black) !important;
  border: 1px solid rgba(0,0,0,0.18) !important;
  border-radius: 12px !important;
  -webkit-text-fill-color: var(--black) !important;
  caret-color: var(--black) !important;
}
div[data-testid="stSelectbox"] span,
div[data-baseweb="select"] span,
div[data-baseweb="select"] div {
  color: var(--black) !important;
}
div[data-testid="stTextInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stCheckbox"] label,
div[data-testid="stCheckbox"] span {
  color: var(--black) !important;
}
::placeholder { color: #555555 !important; opacity: 1 !important; }

/* Keep chat input dock visible and readable */
div[data-testid="stChatInput"] {
  background: transparent !important;
}
div[data-testid="stBottom"] {
  background: linear-gradient(180deg, transparent, rgba(247,252,251,0.95) 30%) !important;
}

div[data-testid="stAlert"] p,
div[data-testid="stAlert"] span { color: var(--black) !important; }

@keyframes rise {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
"""

SUGGESTIONS = [
    "My AquaPearl 500 keeps beeping three times — what should I do?",
    "How long is the warranty on the AquaPearl 500 Pro?",
    "How much does a replacement sediment filter cost?",
    "Do you offer student discounts?",
    "What's the return window if I opened the box?",
    "Can I get next-day delivery to Skardu?",
]


def _inject_css() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def _mask_key(key: str) -> str:
    key = (key or "").strip()
    if len(key) <= 10:
        return "••••••••"
    return f"{key[:7]}…{key[-4:]}"


def _looks_like_openai_key(key: str) -> bool:
    key = key.strip()
    if len(key) < 20:
        return False
    if key in {"sk-your-key-here", "sk-xxxxxxxx", "sk-test"}:
        return False
    return bool(re.match(r"^sk-[A-Za-z0-9_\-]{16,}$", key))


def _init_state() -> None:
    defaults: dict[str, Any] = {
        "authenticated": False,
        "api_key": "",
        "llm_model": "gpt-4o-mini",
        "session_id": str(uuid.uuid4())[:8],
        "messages": [],
        "agent_ready": False,
        "index_meta": {},
        "doc_filter": None,
        "login_error": "",
        "build_error": "",
        "auto_build_attempted": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _agent_cache_key(api_key: str, settings: Settings) -> str:
    digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]
    return (
        f"{digest}:{settings.llm_model}:{settings.embedding_provider}:"
        f"{settings.embedding_model}:{settings.hf_embedding_model}:"
        f"{settings.vector_store_collection}"
    )


@st.cache_resource(show_spinner=False)
def _cached_agent(cache_key: str, api_key: str, llm_model: str) -> SupportPearlzAgent:
    _ = cache_key
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["LLM_MODEL"] = llm_model
    settings = settings_with_overrides(openai_api_key=api_key, llm_model=llm_model)
    setup_logging(settings.log_level, settings.log_file)
    return build_agent(settings)


def _get_settings(api_key: str | None = None) -> Settings:
    key = api_key or st.session_state.get("api_key") or None
    model = st.session_state.get("llm_model") or "gpt-4o-mini"
    overrides: dict[str, object] = {"llm_model": model}
    if key:
        os.environ["OPENAI_API_KEY"] = key
        os.environ["LLM_MODEL"] = model
        overrides["openai_api_key"] = key
    return settings_with_overrides(**overrides)


def _build_index(settings: Settings) -> tuple[bool, str]:
    """Build or rebuild the persistent vector index. Returns (ok, message)."""
    try:
        from src.ingestion.build_index import run_build

        code = run_build(settings, rebuild=True)
        if code != 0:
            return False, "Index build exited with an error. Check logs/supportpearlz.log."
        if not index_exists(settings.vector_store_path, settings.vector_store_collection):
            return False, "Build finished but index files were not found on disk."
        _cached_agent.clear()
        return True, "Index built successfully."
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def _ensure_agent() -> SupportPearlzAgent | None:
    settings = _get_settings()
    if not index_exists(settings.vector_store_path, settings.vector_store_collection):
        return None
    cache_key = _agent_cache_key(st.session_state.api_key, settings)
    agent = _cached_agent(cache_key, st.session_state.api_key, st.session_state.llm_model)
    st.session_state.agent_ready = True
    st.session_state.index_meta = read_index_meta(settings.vector_store_path) or {}
    return agent


def _render_login() -> None:
    st.markdown(
        """
        <div class="login-shell">
          <div class="login-brand">Support<span>Pearlz</span></div>
          <p class="login-tag">
            Instant, cited answers from Pearlz product manuals, warranty, shipping,
            and support policies — grounded in your knowledge base, never guessed.
          </p>
          <div class="pearl-chip-row">
            <span class="pearl-chip">Grounded RAG</span>
            <span class="pearl-chip">Source citations</span>
            <span class="pearl-chip">Honest refusals</span>
            <span class="pearl-chip">Multi-turn memory</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)

    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        st.markdown(
            '<div class="login-label">Connect with your OpenAI key</div>',
            unsafe_allow_html=True,
        )
        api_key = st.text_input(
            "OpenAI API key",
            type="password",
            placeholder="sk-… or sk-proj-…",
            label_visibility="collapsed",
            key="login_api_key_input",
            help="Used only in this browser session. Not written to disk by the UI.",
        )
        model = st.selectbox(
            "Chat model",
            options=["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"],
            index=0,
        )
        st.checkbox(
            "Keep key for this browser tab only (session memory)",
            value=True,
            key="remember_key_checkbox",
        )

        col_a, col_b = st.columns(2)
        with col_a:
            connect = st.button("Enter workspace", type="primary", use_container_width=True)
        with col_b:
            demo_hint = st.button("How it works", use_container_width=True)

        if demo_hint:
            st.info(
                "1) Paste your OpenAI API key → 2) We load (or build) the Pearlz vector index → "
                "3) Ask in plain language. Follow-ups like “is that covered?” are rewritten "
                "automatically. If docs don’t support an answer, SupportPearlz refuses instead of guessing."
            )

        if st.session_state.login_error:
            st.error(st.session_state.login_error)

        st.markdown(
            """
            <p class="login-hint">
              Chat uses your OpenAI key. Embeddings use a local HuggingFace model by default,
              so the knowledge index can be built without burning embedding tokens.
              Prefer a restricted key with a spend limit.
            </p>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            """
            <div class="login-aside">
              <h3>Built for Pearlz support</h3>
              <ul>
                <li>Answers only from indexed Pearlz documents</li>
                <li>Citations with file + location on every claim</li>
                <li>Confidence: high / partial / none</li>
                <li>Escalation path when the KB has a gap</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        settings_preview = _get_settings()
        has_index = index_exists(
            settings_preview.vector_store_path,
            settings_preview.vector_store_collection,
        )
        if has_index:
            meta = read_index_meta(settings_preview.vector_store_path) or {}
            st.success(
                f"Knowledge index ready · `{settings_preview.vector_store_collection}`"
                + (f" · {meta.get('chunk_count', '?')} chunks" if meta else "")
            )
        else:
            st.warning(
                "No vector index on disk yet. After you enter the workspace, "
                "the app will build it automatically (or use **Build index now**)."
            )

    if connect:
        st.session_state.login_error = ""
        candidate = (api_key or "").strip()
        if not candidate:
            env_settings = settings_with_overrides()
            candidate = (env_settings.openai_api_key or "").strip()

        if not candidate or not _looks_like_openai_key(candidate):
            st.session_state.login_error = (
                "Paste a valid OpenAI API key starting with sk- (not the placeholder)."
            )
            st.rerun()

        os.environ["OPENAI_API_KEY"] = candidate
        os.environ["LLM_MODEL"] = model
        st.session_state.api_key = candidate
        st.session_state.llm_model = model

        try:
            cfg = settings_with_overrides(openai_api_key=candidate, llm_model=model)
            cfg.require_llm_credentials()
        except RuntimeError as exc:
            st.session_state.login_error = str(exc)
            st.rerun()

        st.session_state.authenticated = True
        st.session_state.messages = []
        st.session_state.auto_build_attempted = False
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.rerun()


def _confidence_badge(conf: Confidence) -> str:
    cls = {
        Confidence.high: "badge-high",
        Confidence.partial: "badge-partial",
        Confidence.none: "badge-none",
    }[conf]
    return f'<span class="badge {cls}">Confidence · {conf.value}</span>'


def _render_response_meta(resp: DisplayResponse) -> None:
    badges = [_confidence_badge(resp.confidence)]
    if resp.refusal or not resp.answered:
        badges.append('<span class="badge badge-none">Refusal / escalate</span>')
    if resp.rewritten_query and resp.rewritten_query != resp.original_query:
        safe = (
            resp.rewritten_query.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        badges.append(f'<span class="badge badge-rewrite">Rewritten · {safe}</span>')
    st.markdown(f'<div class="badge-row">{"".join(badges)}</div>', unsafe_allow_html=True)

    if resp.citations:
        items = []
        for i, cite in enumerate(resp.citations, start=1):
            snip = (
                f'<span class="cite-snip">“{cite.snippet[:140]}”</span>'
                if cite.snippet
                else ""
            )
            items.append(
                f'<div class="cite-item"><strong>[{i}]</strong> {cite.display()}{snip}</div>'
            )
        st.markdown(
            f'<div class="cite-box"><div class="title">Sources used</div>{"".join(items)}</div>',
            unsafe_allow_html=True,
        )
    elif resp.refusal or not resp.answered:
        st.markdown(
            '<div class="cite-box"><div class="title">Sources used</div>'
            '<div class="cite-item">None — no supporting documentation found</div></div>',
            unsafe_allow_html=True,
        )


def _sidebar(agent: SupportPearlzAgent | None) -> None:
    settings = _get_settings()
    with st.sidebar:
        st.markdown("### Session")
        st.caption(
            f"ID `{st.session_state.session_id}` · key `{_mask_key(st.session_state.api_key)}`"
        )

        if st.button("New conversation", use_container_width=True):
            if agent is not None:
                agent.reset_session()
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())[:8]
            st.rerun()

        if st.button("Sign out", use_container_width=True):
            _cached_agent.clear()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.divider()
        st.markdown("### Knowledge base")
        has_index = index_exists(settings.vector_store_path, settings.vector_store_collection)
        meta = read_index_meta(settings.vector_store_path) or {}
        if has_index:
            st.success("Index loaded from disk")
            if meta:
                st.caption(
                    f"Chunks: {meta.get('chunk_count', '—')} · "
                    f"Embed: {meta.get('embedding_model', settings.embedding_model)}"
                )
        else:
            st.error("Index missing")

        if st.button("Build / rebuild index", type="primary", use_container_width=True):
            with st.spinner("Building persistent vector index… first run may download the embedding model"):
                ok, msg = _build_index(settings)
                if ok:
                    st.session_state.build_error = ""
                    st.success(msg)
                    st.rerun()
                else:
                    st.session_state.build_error = msg
                    st.error(msg)

        if st.session_state.build_error:
            st.caption(f"Last build error: {st.session_state.build_error}")

        st.divider()
        st.markdown("### Retrieval filter")
        filter_choice = st.selectbox(
            "Limit by document type",
            options=["(all)", "policy", "faq", "pricing", "manual", "guide", "handbook"],
            index=0,
        )
        st.session_state.doc_filter = (
            None if filter_choice == "(all)" else {"doc_type": filter_choice}
        )

        st.divider()
        st.markdown("### Try asking")
        for i, q in enumerate(SUGGESTIONS[:4]):
            if st.button(q, key=f"sug_{i}", use_container_width=True):
                st.session_state._pending_question = q
                st.rerun()


def _ask(agent: SupportPearlzAgent, question: str) -> DisplayResponse:
    return agent.ask(question, filter_metadata=st.session_state.get("doc_filter"))


def _render_chat(agent: SupportPearlzAgent | None) -> None:
    """Always render the chat input. Gate answering on agent availability."""
    settings = _get_settings()
    meta = st.session_state.get("index_meta") or read_index_meta(settings.vector_store_path) or {}
    chunk_bit = f" · {meta.get('chunk_count')} chunks" if meta.get("chunk_count") else ""

    st.markdown(
        f"""
        <div class="topbar">
          <div class="topbar-brand">Support<span>Pearlz</span></div>
          <div class="topbar-meta">KB · {settings.vector_store_collection}{chunk_bit}</div>
        </div>
        <div class="hero-strip">
          <h2>Ask anything about Pearlz products &amp; policies</h2>
          <p>Answers are grounded in your documents. Follow-ups are rewritten automatically. Gaps become honest refusals.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if agent is None:
        st.warning(
            "The knowledge index is not ready yet. Click **Build / rebuild index** in the sidebar "
            "(or wait if auto-build is running). The chat box below stays available."
        )

    if not st.session_state.messages:
        cols = st.columns(2)
        for i, q in enumerate(SUGGESTIONS):
            with cols[i % 2]:
                if st.button(q, key=f"main_sug_{i}", use_container_width=True):
                    st.session_state._pending_question = q
                    st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("meta"):
                _render_response_meta(DisplayResponse.model_validate(msg["meta"]))

    # ALWAYS mount chat input so the text box is visible
    pending = st.session_state.pop("_pending_question", None)
    user_text = st.chat_input(
        "Ask about warranty, filters, shipping, returns…",
        key="main_chat_input",
    )
    question = pending or user_text
    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        if agent is None:
            err = (
                "I can’t answer yet because the knowledge index isn’t built. "
                "Use **Build / rebuild index** in the sidebar, then ask again."
            )
            st.warning(err)
            st.session_state.messages.append(
                {"role": "assistant", "content": err, "meta": None}
            )
            return

        with st.spinner("Searching Pearlz knowledge…"):
            try:
                resp = _ask(agent, question)
            except Exception as exc:  # noqa: BLE001
                err = f"Something went wrong talking to the model or the index. Details: {exc}"
                st.error(err)
                st.session_state.messages.append(
                    {"role": "assistant", "content": err, "meta": None}
                )
                return
        st.markdown(resp.answer)
        _render_response_meta(resp)
        st.session_state.messages.append(
            {"role": "assistant", "content": resp.answer, "meta": resp.model_dump()}
        )


def main() -> None:
    st.set_page_config(
        page_title="SupportPearlz",
        page_icon="💧",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_css()
    _init_state()

    if not st.session_state.authenticated:
        _render_login()
        return

    settings = _get_settings()

    # Auto-build index once after login if missing
    if (
        not index_exists(settings.vector_store_path, settings.vector_store_collection)
        and not st.session_state.auto_build_attempted
    ):
        st.session_state.auto_build_attempted = True
        with st.spinner(
            "Building knowledge index for the first time… "
            "(downloads a small local embedding model if needed)"
        ):
            ok, msg = _build_index(settings)
            if not ok:
                st.session_state.build_error = msg

    agent: SupportPearlzAgent | None = None
    try:
        agent = _ensure_agent()
    except FileNotFoundError:
        agent = None
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not start the agent: {exc}")
        agent = None

    _sidebar(agent)
    _render_chat(agent)


if __name__ == "__main__":
    main()
