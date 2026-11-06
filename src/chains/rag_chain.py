"""Composed RAG chain: condense → retrieve → gate → generate → cite."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from langchain_chroma import Chroma
from langchain_core.language_models.chat_models import BaseChatModel

from src.chains.llm_factory import get_chat_model
from src.chains.memory import ConversationMemory, condense_question
from src.chains.prompts import build_rag_prompt
from src.chains.schemas import (
    Confidence,
    DisplayResponse,
    GroundedResponse,
    SourceCitation,
)
from src.retrieval.embeddings_factory import get_embeddings
from src.retrieval.retriever import format_context_blocks, retrieve
from src.retrieval.vector_store import load_vector_store

if TYPE_CHECKING:
    from src.config import Settings

logger = logging.getLogger("supportpearlz.rag")


class SupportPearlzAgent:
    """End-to-end conversational RAG agent."""

    def __init__(
        self,
        settings: Settings,
        *,
        store: Chroma | None = None,
        llm: BaseChatModel | None = None,
    ) -> None:
        self.settings = settings
        settings.require_llm_credentials()
        self.embeddings = get_embeddings(settings)
        self.store = store or load_vector_store(self.embeddings, settings)
        self.llm = llm or get_chat_model(settings)
        self.memory = ConversationMemory(window_turns=settings.history_window_turns)
        self.prompt = build_rag_prompt()
        # Structured output with schema validation
        self.structured_llm = self.llm.with_structured_output(GroundedResponse)

    def reset_session(self) -> None:
        self.memory.reset()
        logger.info("Session memory reset")

    def ask(
        self,
        question: str,
        *,
        filter_metadata: dict[str, Any] | None = None,
        use_history: bool = True,
    ) -> DisplayResponse:
        """Answer one user turn and update conversation memory."""
        t0 = time.perf_counter()
        original = question.strip()
        if not original:
            return self._refusal(
                "Please enter a question.",
                original,
                original,
                flags=["empty_query"],
            )

        try:
            rewritten = (
                condense_question(self.llm, original, self.memory)
                if use_history
                else original
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Query condensation failed: %s", exc)
            rewritten = original

        try:
            retrieval = retrieve(
                self.store,
                rewritten,
                self.settings,
                filter_metadata=filter_metadata,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Retrieval failed: %s", exc)
            return self._user_error(
                "I could not search the knowledge base right now. "
                f"Please try again shortly or contact {self.settings.support_escalation_email}.",
                original,
                rewritten,
                flags=["retrieval_error"],
            )

        latency_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "Turn | original=%r | rewritten=%r | relevant=%s | best=%.4f | latency_ms=%.0f",
            original,
            rewritten,
            retrieval.relevant,
            retrieval.best_score,
            latency_ms,
        )

        if not retrieval.relevant:
            response = self._refusal(
                (
                    "I could not find this in the Pearlz documentation. "
                    "I will not guess. Please contact "
                    f"{self.settings.support_escalation_email} for help from a human agent."
                ),
                original,
                rewritten,
                flags=["refusal", "relevance_gate"],
            )
            self._commit_turn(original, response.answer)
            return response

        context, used_chunks, truncated = format_context_blocks(
            retrieval.chunks,
            max_chunks=self.settings.max_context_chunks,
            max_chars=self.settings.max_context_chars,
        )
        if truncated:
            logger.info("Context truncation flag set for query=%r", rewritten)

        allowed_labels = {c.label for c in used_chunks}
        label_to_chunk = {c.label: c for c in used_chunks}

        grounded = self._generate(context, original, rewritten)
        display = self._resolve_citations(
            grounded,
            label_to_chunk,
            allowed_labels,
            original,
            rewritten,
            best_score=retrieval.best_score,
        )
        self._commit_turn(original, display.answer)
        logger.info(
            "Answered | answered=%s confidence=%s sources=%s refusal=%s",
            display.answered,
            display.confidence.value,
            [c.label for c in display.citations],
            display.refusal,
        )
        return display

    def _generate(
        self,
        context: str,
        original: str,
        rewritten: str,
    ) -> GroundedResponse:
        history_text = self.memory.format_history()
        payload = {
            "context": context,
            "question": original,
            "chat_history": history_text,
            "escalation_email": self.settings.support_escalation_email,
        }

        try:
            result = self.structured_llm.invoke(self.prompt.format_prompt(**payload).to_messages())
            if isinstance(result, GroundedResponse):
                return result
            return GroundedResponse.model_validate(result)
        except Exception as first_exc:  # noqa: BLE001
            logger.warning("Structured output failed (%s); retrying once", first_exc)
            try:
                result = self.structured_llm.invoke(
                    self.prompt.format_prompt(**payload).to_messages()
                )
                if isinstance(result, GroundedResponse):
                    return result
                return GroundedResponse.model_validate(result)
            except Exception as second_exc:  # noqa: BLE001
                logger.exception("Structured output failed after retry: %s", second_exc)
                # Fallback: try plain generation then coerce
                try:
                    raw = self.llm.invoke(self.prompt.format_prompt(**payload).to_messages())
                    text = raw.content if hasattr(raw, "content") else str(raw)
                    return GroundedResponse(
                        answer=str(text),
                        sources=[],
                        confidence=Confidence.partial,
                        answered=True,
                        flags=["schema_fallback"],
                    )
                except Exception as api_exc:  # noqa: BLE001
                    logger.exception("LLM API failure: %s", api_exc)
                    return GroundedResponse(
                        answer=(
                            "I'm temporarily unable to generate an answer due to a service error. "
                            f"Please try again or contact {self.settings.support_escalation_email}."
                        ),
                        sources=[],
                        confidence=Confidence.none,
                        answered=False,
                        flags=["api_error"],
                    )

    def _resolve_citations(
        self,
        grounded: GroundedResponse,
        label_to_chunk: dict[str, Any],
        allowed_labels: set[str],
        original: str,
        rewritten: str,
        *,
        best_score: float,
    ) -> DisplayResponse:
        valid_labels: list[str] = []
        for label in grounded.sources:
            normalised = label.strip().upper()
            if not normalised.startswith("S"):
                # Accept bare numbers
                if normalised.isdigit():
                    normalised = f"S{normalised}"
            # Preserve original casing used in blocks (S1, S2…)
            match = next((a for a in allowed_labels if a.upper() == normalised.upper()), None)
            if match:
                if match not in valid_labels:
                    valid_labels.append(match)
            else:
                logger.warning("Dropping fabricated/unknown citation label: %s", label)

        # De-duplicate by (source, location)
        citations: list[SourceCitation] = []
        seen_keys: set[tuple[str, str]] = set()
        for label in valid_labels:
            chunk = label_to_chunk[label]
            key = (chunk.source, chunk.location)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            snippet = chunk.document.page_content.strip().replace("\n", " ")[:180]
            citations.append(
                SourceCitation(
                    label=label,
                    source=chunk.source,
                    location=chunk.location,
                    snippet=snippet,
                )
            )

        confidence = grounded.confidence
        # Lower confidence if citations were invalid or score is weak
        if grounded.answered and not citations and "api_error" not in grounded.flags:
            confidence = Confidence.partial
            if "citation_mismatch" not in grounded.flags:
                grounded.flags.append("citation_mismatch")

        if best_score < self.settings.score_threshold + 0.1 and confidence == Confidence.high:
            confidence = Confidence.partial

        refusal = (not grounded.answered) or confidence == Confidence.none
        if refusal and not citations:
            # Ensure refusal messaging is clear even if model hedged
            pass

        return DisplayResponse(
            answer=grounded.answer,
            citations=citations,
            confidence=confidence,
            answered=grounded.answered and not refusal,
            flags=list(grounded.flags),
            rewritten_query=rewritten,
            original_query=original,
            refusal=refusal,
        )

    def _refusal(
        self,
        message: str,
        original: str,
        rewritten: str,
        *,
        flags: list[str],
    ) -> DisplayResponse:
        return DisplayResponse(
            answer=message,
            citations=[],
            confidence=Confidence.none,
            answered=False,
            flags=flags,
            rewritten_query=rewritten,
            original_query=original,
            refusal=True,
        )

    def _user_error(
        self,
        message: str,
        original: str,
        rewritten: str,
        *,
        flags: list[str],
    ) -> DisplayResponse:
        return DisplayResponse(
            answer=message,
            citations=[],
            confidence=Confidence.none,
            answered=False,
            flags=flags,
            rewritten_query=rewritten,
            original_query=original,
            refusal=True,
        )

    def _commit_turn(self, user_text: str, ai_text: str) -> None:
        self.memory.add_user(user_text)
        self.memory.add_ai(ai_text)


def build_agent(settings: Settings) -> SupportPearlzAgent:
    return SupportPearlzAgent(settings)
