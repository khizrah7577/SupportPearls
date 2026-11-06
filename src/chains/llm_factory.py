"""Chat model factory."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain_core.language_models.chat_models import BaseChatModel

if TYPE_CHECKING:
    from src.config import Settings

logger = logging.getLogger("supportpearlz.llm")


def get_chat_model(settings: Settings) -> BaseChatModel:
    provider = settings.llm_provider

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        kwargs: dict = {
            "model": settings.llm_model,
            "temperature": settings.llm_temperature,
            "api_key": settings.openai_api_key,
            "max_retries": settings.llm_max_retries,
            "timeout": settings.llm_timeout_seconds,
        }
        if settings.openai_api_base:
            kwargs["base_url"] = settings.openai_api_base
        logger.info(
            "Chat model: OpenAI %s (temperature=%s)",
            settings.llm_model,
            settings.llm_temperature,
        )
        return ChatOpenAI(**kwargs)

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        logger.info("Chat model: Ollama %s", settings.ollama_model)
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_retries=settings.llm_max_retries,
            timeout=settings.llm_timeout_seconds,
        )

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
        )

    raise ValueError(f"Unsupported LLM provider: {provider}")
