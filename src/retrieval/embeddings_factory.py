"""Embedding model factory — same model must be used for index and query."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings

    from src.config import Settings

logger = logging.getLogger("supportpearlz.embeddings")

# Documented dimensions for report / diagnostics
EMBEDDING_DIMENSIONS: dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "nomic-embed-text": 768,
}


def get_embeddings(settings: Settings) -> Embeddings:
    provider = settings.embedding_provider
    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        kwargs: dict = {
            "model": settings.embedding_model,
            "api_key": settings.openai_api_key,
            "chunk_size": settings.embedding_batch_size,
        }
        if settings.openai_api_base:
            kwargs["base_url"] = settings.openai_api_base
        logger.info("Using OpenAI embeddings: %s", settings.embedding_model)
        return OpenAIEmbeddings(**kwargs)

    if provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings

        logger.info("Using HuggingFace embeddings: %s", settings.hf_embedding_model)
        return HuggingFaceEmbeddings(
            model_name=settings.hf_embedding_model,
            encode_kwargs={"normalize_embeddings": True},
        )

    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        logger.info("Using Ollama embeddings: %s", settings.embedding_model)
        return OllamaEmbeddings(
            model=settings.embedding_model,
            base_url=settings.ollama_base_url,
        )

    raise ValueError(f"Unsupported embedding provider: {provider}")


def embedding_dimension(settings: Settings) -> int | None:
    if settings.embedding_provider == "huggingface":
        return EMBEDDING_DIMENSIONS.get(settings.hf_embedding_model)
    return EMBEDDING_DIMENSIONS.get(settings.embedding_model)
