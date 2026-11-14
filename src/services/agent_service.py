"""RAG agent lifecycle for the Streamlit UI."""

from __future__ import annotations

import hashlib
import os
from typing import Any

import streamlit as st

from src.chains.rag_chain import SupportPearlzAgent, build_agent
from src.config import Settings, settings_with_overrides
from src.retrieval.vector_store import index_exists, read_index_meta
from src.utils.logging_setup import setup_logging


def resolve_openai_api_key() -> str | None:
    """Prefer session key, then Streamlit secrets, then environment."""
    key = (st.session_state.get("openai_api_key") or "").strip()
    if key:
        return key
    try:
        secrets_key = st.secrets.get("OPENAI_API_KEY", "")
        if secrets_key:
            return str(secrets_key).strip()
    except Exception:  # noqa: BLE001 — secrets.toml may be absent locally
        pass
    env_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    return env_key or None


def get_runtime_settings() -> Settings:
    key = resolve_openai_api_key()
    model = st.session_state.get("llm_model") or "gpt-4o-mini"
    overrides: dict[str, Any] = {"llm_model": model}
    if key:
        os.environ["OPENAI_API_KEY"] = key
        overrides["openai_api_key"] = key
    os.environ["LLM_MODEL"] = model
    return settings_with_overrides(**overrides)


@st.cache_resource(show_spinner=False)
def _cached_agent(cache_key: str, api_key: str, llm_model: str) -> SupportPearlzAgent:
    _ = cache_key
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["LLM_MODEL"] = llm_model
    settings = settings_with_overrides(openai_api_key=api_key, llm_model=llm_model)
    setup_logging(settings.log_level, settings.log_file)
    return build_agent(settings)


def clear_agent_cache() -> None:
    _cached_agent.clear()


def ensure_index(settings: Settings | None = None) -> tuple[bool, str]:
    settings = settings or get_runtime_settings()
    if index_exists(settings.vector_store_path, settings.vector_store_collection):
        meta = read_index_meta(settings.vector_store_path) or {}
        return True, f"Index ready ({meta.get('chunk_count', '?')} chunks)"
    try:
        from src.ingestion.build_index import run_build

        settings.require_embedding_credentials()
        code = run_build(settings, rebuild=True)
        if code != 0:
            return False, "Index build failed. Check application logs."
        clear_agent_cache()
        meta = read_index_meta(settings.vector_store_path) or {}
        return True, f"Index built ({meta.get('chunk_count', '?')} chunks)"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def get_agent() -> SupportPearlzAgent | None:
    api_key = resolve_openai_api_key()
    if not api_key:
        return None
    settings = get_runtime_settings()
    if not index_exists(settings.vector_store_path, settings.vector_store_collection):
        return None
    digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]
    cache_key = (
        f"{digest}:{settings.llm_model}:{settings.embedding_provider}:"
        f"{settings.active_embedding_model()}:{settings.vector_store_collection}"
    )
    return _cached_agent(cache_key, api_key, settings.llm_model)
