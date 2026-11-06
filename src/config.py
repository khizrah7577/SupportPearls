"""Central configuration loaded from environment variables.

Run as a smoke check:
    python -m src.config
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseModel):
    """Validated runtime settings. Secrets are never printed in full."""

    # LLM
    llm_provider: Literal["openai", "ollama", "google", "anthropic"] = "openai"
    openai_api_base: str | None = None
    openai_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0
    llm_max_retries: int = 2
    llm_timeout_seconds: int = 60
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # Embeddings
    embedding_provider: Literal["openai", "huggingface", "ollama"] = "openai"
    embedding_model: str = "text-embedding-3-small"
    hf_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_batch_size: int = 64

    # Vector store
    vector_store_path: Path = Field(default=Path("data/vector_store"))
    vector_store_collection: str = "pearlz_kb"
    vector_store_distance: Literal["cosine", "l2", "ip"] = "cosine"

    # Chunking
    chunk_size: int = 800
    chunk_overlap: int = 120
    chunk_strategy: Literal["recursive", "markdown", "csv_row", "hybrid"] = "hybrid"

    # Retrieval
    retrieval_k: int = 4
    retrieval_strategy: Literal["similarity", "mmr", "threshold"] = "mmr"
    mmr_lambda: float = 0.5
    score_threshold: float = 0.35
    max_context_chars: int = 6000
    max_context_chunks: int = 4

    # Conversation
    history_window_turns: int = 6
    support_escalation_email: str = "support@pearlzhome.example"

    # Paths / logging
    knowledge_base_path: Path = Field(default=Path("data/knowledge_base"))
    log_level: str = "INFO"
    log_file: Path = Field(default=Path("logs/supportpearlz.log"))
    session_log_dir: Path = Field(default=Path("logs/sessions"))

    @field_validator(
        "vector_store_path",
        "knowledge_base_path",
        "log_file",
        "session_log_dir",
        mode="before",
    )
    @classmethod
    def _to_path(cls, value: object) -> Path:
        path = Path(str(value))
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path

    def active_embedding_model(self) -> str:
        """Model name that must match the persisted index."""
        if self.embedding_provider == "huggingface":
            return self.hf_embedding_model
        return self.embedding_model

    def require_embedding_credentials(self) -> None:
        """Fail loudly if embeddings need a missing key."""
        if self.embedding_provider == "openai" and not self.openai_api_key:
            raise RuntimeError(
                "Missing required environment variable OPENAI_API_KEY "
                "(required when EMBEDDING_PROVIDER=openai)."
            )

    def require_llm_credentials(self) -> None:
        """Fail loudly if the selected provider needs a missing key."""
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise RuntimeError(
                "Missing required environment variable OPENAI_API_KEY "
                "(required when LLM_PROVIDER=openai). Copy .env.example to .env."
            )
        self.require_embedding_credentials()

    def masked_dict(self) -> dict[str, object]:
        """Return settings with secrets masked for safe printing."""
        data = self.model_dump()
        key = data.get("openai_api_key")
        if isinstance(key, str) and key:
            data["openai_api_key"] = f"{key[:4]}…{key[-4:]}" if len(key) > 8 else "****"
        for path_key in (
            "vector_store_path",
            "knowledge_base_path",
            "log_file",
            "session_log_dir",
        ):
            data[path_key] = str(data[path_key])
        return data


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def load_settings(env_file: Path | None = None) -> Settings:
    """Load `.env` once and return a validated Settings object."""
    dotenv_path = env_file or (PROJECT_ROOT / ".env")
    # Project .env must win over stale shell/process env (e.g. old EMBEDDING_PROVIDER).
    load_dotenv(dotenv_path, override=True)

    try:
        return Settings(
            llm_provider=_env("LLM_PROVIDER", "openai"),  # type: ignore[arg-type]
            openai_api_base=_env("OPENAI_API_BASE"),
            openai_api_key=_env("OPENAI_API_KEY"),
            llm_model=_env("LLM_MODEL", "gpt-4o-mini") or "gpt-4o-mini",
            llm_temperature=float(_env("LLM_TEMPERATURE", "0.0") or "0.0"),
            llm_max_retries=int(_env("LLM_MAX_RETRIES", "2") or "2"),
            llm_timeout_seconds=int(_env("LLM_TIMEOUT_SECONDS", "60") or "60"),
            ollama_base_url=_env("OLLAMA_BASE_URL", "http://localhost:11434")
            or "http://localhost:11434",
            ollama_model=_env("OLLAMA_MODEL", "llama3.2") or "llama3.2",
            embedding_provider=_env("EMBEDDING_PROVIDER", "openai"),  # type: ignore[arg-type]
            embedding_model=_env("EMBEDDING_MODEL", "text-embedding-3-small")
            or "text-embedding-3-small",
            hf_embedding_model=_env(
                "HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
            )
            or "sentence-transformers/all-MiniLM-L6-v2",
            embedding_batch_size=int(_env("EMBEDDING_BATCH_SIZE", "64") or "64"),
            vector_store_path=_env("VECTOR_STORE_PATH", "data/vector_store"),
            vector_store_collection=_env("VECTOR_STORE_COLLECTION", "pearlz_kb")
            or "pearlz_kb",
            vector_store_distance=_env("VECTOR_STORE_DISTANCE", "cosine"),  # type: ignore[arg-type]
            chunk_size=int(_env("CHUNK_SIZE", "800") or "800"),
            chunk_overlap=int(_env("CHUNK_OVERLAP", "120") or "120"),
            chunk_strategy=_env("CHUNK_STRATEGY", "hybrid"),  # type: ignore[arg-type]
            retrieval_k=int(_env("RETRIEVAL_K", "4") or "4"),
            retrieval_strategy=_env("RETRIEVAL_STRATEGY", "mmr"),  # type: ignore[arg-type]
            mmr_lambda=float(_env("MMR_LAMBDA", "0.5") or "0.5"),
            score_threshold=float(_env("SCORE_THRESHOLD", "0.35") or "0.35"),
            max_context_chars=int(_env("MAX_CONTEXT_CHARS", "6000") or "6000"),
            max_context_chunks=int(_env("MAX_CONTEXT_CHUNKS", "4") or "4"),
            history_window_turns=int(_env("HISTORY_WINDOW_TURNS", "6") or "6"),
            support_escalation_email=_env(
                "SUPPORT_ESCALATION_EMAIL", "support@pearlzhome.example"
            )
            or "support@pearlzhome.example",
            knowledge_base_path=_env("KNOWLEDGE_BASE_PATH", "data/knowledge_base"),
            log_level=_env("LOG_LEVEL", "INFO") or "INFO",
            log_file=_env("LOG_FILE", "logs/supportpearlz.log"),
            session_log_dir=_env("SESSION_LOG_DIR", "logs/sessions"),
        )
    except (ValidationError, ValueError, TypeError) as exc:
        raise RuntimeError(f"Invalid configuration: {exc}") from exc


def settings_with_overrides(**overrides: object) -> Settings:
    """Return settings with runtime overrides (e.g. Streamlit-entered API key)."""
    base = load_settings()
    cleaned = {k: v for k, v in overrides.items() if v is not None}
    if not cleaned:
        return base
    return base.model_copy(update=cleaned)


# Eager singleton for `python -m src.config` and library imports.
try:
    settings = load_settings()
except RuntimeError:
    settings = None  # type: ignore[assignment]


def main() -> int:
    """Smoke-check: print masked config or a clear missing-key error."""
    try:
        cfg = load_settings()
        cfg.require_llm_credentials()
    except RuntimeError as exc:
        print(f"CONFIG ERROR: {exc}", file=sys.stderr)
        return 1

    print("SupportPearlz configuration loaded successfully.")
    print("-" * 48)
    for key, value in sorted(cfg.masked_dict().items()):
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
