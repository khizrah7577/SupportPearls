"""Chat history windowing and query condensation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from src.chains.prompts import build_condense_prompt

if TYPE_CHECKING:
    pass

logger = logging.getLogger("supportpearlz.memory")


class ConversationMemory:
    """Bounded per-session chat history (last N turns)."""

    def __init__(self, window_turns: int = 6) -> None:
        self.window_turns = window_turns
        self._messages: list[BaseMessage] = []

    def add_user(self, text: str) -> None:
        self._messages.append(HumanMessage(content=text))
        self._trim()

    def add_ai(self, text: str) -> None:
        self._messages.append(AIMessage(content=text))
        self._trim()

    def reset(self) -> None:
        self._messages.clear()

    def _trim(self) -> None:
        # Each turn ≈ 2 messages (human + ai); keep last N turns
        max_messages = self.window_turns * 2
        if len(self._messages) > max_messages:
            self._messages = self._messages[-max_messages:]

    @property
    def messages(self) -> list[BaseMessage]:
        return list(self._messages)

    def format_history(self) -> str:
        if not self._messages:
            return "(no prior turns)"
        lines: list[str] = []
        for msg in self._messages:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            lines.append(f"{role}: {content}")
        return "\n".join(lines)


def condense_question(
    llm: BaseChatModel,
    question: str,
    history: ConversationMemory,
) -> str:
    """
    Rewrite the latest question + history into a standalone retrieval query.

    If there is no history, return the question unchanged (saves a round-trip).
    """
    if not history.messages:
        return question.strip()

    prompt = build_condense_prompt()
    chain = prompt | llm
    raw = chain.invoke(
        {
            "chat_history": history.format_history(),
            "question": question,
        }
    )
    if hasattr(raw, "content"):
        text = raw.content
    else:
        text = str(raw)
    standalone = str(text).strip().strip('"').strip("'")
    logger.info(
        "Query condensation | original=%r | rewritten=%r",
        question,
        standalone,
    )
    return standalone or question.strip()
