"""Retriever construction and relevance gate."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from langchain_core.documents import Document

if TYPE_CHECKING:
    from langchain_chroma import Chroma

    from src.config import Settings

logger = logging.getLogger("supportpearlz.retriever")


@dataclass
class RetrievedChunk:
    label: str  # e.g. S1
    document: Document
    score: float

    @property
    def source(self) -> str:
        return str(self.document.metadata.get("source", "unknown"))

    @property
    def location(self) -> str:
        return str(self.document.metadata.get("location", ""))

    @property
    def chunk_id(self) -> str:
        return str(self.document.metadata.get("chunk_id", self.label))


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk] = field(default_factory=list)
    relevant: bool = False
    best_score: float = 0.0
    strategy: str = "similarity"
    gate_reason: str = ""


def retrieve(
    store: Chroma,
    query: str,
    settings: Settings,
    *,
    k: int | None = None,
    strategy: str | None = None,
    filter_metadata: dict[str, Any] | None = None,
) -> RetrievalResult:
    """Run retrieval with configurable strategy and apply the relevance gate."""
    k = k if k is not None else settings.retrieval_k
    strategy = strategy or settings.retrieval_strategy
    filter_dict = filter_metadata or None

    pairs: list[tuple[Document, float]] = []

    if strategy == "mmr":
        # MMR returns documents without scores — score via a follow-up similarity call
        docs = store.max_marginal_relevance_search(
            query,
            k=k,
            fetch_k=max(k * 4, 12),
            lambda_mult=settings.mmr_lambda,
            filter=filter_dict,
        )
        scored = {
            id(d): s
            for d, s in store.similarity_search_with_relevance_scores(
                query, k=max(k * 4, 12), filter=filter_dict
            )
        }
        # Match by content hash / page content
        content_scores = {
            d.page_content: float(s)
            for d, s in store.similarity_search_with_relevance_scores(
                query, k=max(k * 4, 12), filter=filter_dict
            )
        }
        pairs = [(d, content_scores.get(d.page_content, 0.0)) for d in docs]
        _ = scored  # kept for potential future id-based matching
    elif strategy == "threshold":
        pairs = list(
            store.similarity_search_with_relevance_scores(
                query, k=k, filter=filter_dict
            )
        )
        pairs = [(d, float(s)) for d, s in pairs if float(s) >= settings.score_threshold]
    else:
        pairs = [
            (d, float(s))
            for d, s in store.similarity_search_with_relevance_scores(
                query, k=k, filter=filter_dict
            )
        ]

    chunks = [
        RetrievedChunk(label=f"S{i}", document=doc, score=score)
        for i, (doc, score) in enumerate(pairs, start=1)
    ]
    best = max((c.score for c in chunks), default=0.0)
    relevant, reason = relevance_gate(chunks, settings.score_threshold)

    result = RetrievalResult(
        chunks=chunks if relevant else chunks,  # keep for logging even if gated
        relevant=relevant,
        best_score=best,
        strategy=strategy,
        gate_reason=reason,
    )
    if not relevant:
        logger.info(
            "Relevance gate FAILED: %s | best_score=%.4f threshold=%.4f",
            reason,
            best,
            settings.score_threshold,
        )
    else:
        logger.info(
            "Retrieved %d chunks (strategy=%s best=%.4f): %s",
            len(chunks),
            strategy,
            best,
            [(c.label, c.chunk_id, round(c.score, 4)) for c in chunks],
        )
    return result


def relevance_gate(
    chunks: list[RetrievedChunk],
    threshold: float,
) -> tuple[bool, str]:
    """
    Empirically calibrated gate:
    - empty result set → fail
    - best similarity score below threshold → fail
    Threshold must be recalibrated when embedding model or distance metric changes.
    """
    if not chunks:
        return False, "empty_result_set"
    best = max(c.score for c in chunks)
    if best < threshold:
        return False, f"best_score_below_threshold ({best:.4f} < {threshold})"
    return True, "passed"


def format_context_blocks(
    chunks: list[RetrievedChunk],
    *,
    max_chunks: int,
    max_chars: int,
) -> tuple[str, list[RetrievedChunk], bool]:
    """
    Label chunks as [S1] source=… location=… and concatenate.
    Returns (context_text, used_chunks, truncated).
    """
    used: list[RetrievedChunk] = []
    parts: list[str] = []
    total = 0
    truncated = False

    for chunk in chunks[:max_chunks]:
        header = (
            f"[{chunk.label}] source={chunk.source} "
            f"location={chunk.location} doc_type={chunk.document.metadata.get('doc_type', '')}"
        )
        body = chunk.document.page_content.strip()
        block = f"{header}\n{body}"
        if total + len(block) > max_chars and used:
            truncated = True
            break
        if total + len(block) > max_chars:
            remain = max_chars - total - len(header) - 1
            if remain < 100:
                truncated = True
                break
            body = body[:remain] + "…"
            block = f"{header}\n{body}"
            truncated = True
        parts.append(block)
        used.append(chunk)
        total += len(block) + 2

    if truncated:
        logger.warning(
            "Context truncated at %d chars / %d chunks", max_chars, len(used)
        )
    return "\n\n".join(parts), used, truncated
