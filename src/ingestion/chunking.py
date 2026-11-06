"""Chunking strategies with metadata preservation."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

logger = logging.getLogger("supportpearlz.chunking")


def make_recursive_splitter(
    chunk_size: int,
    chunk_overlap: int,
) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
        is_separator_regex=False,
    )


def _ensure_chunk_ids(chunks: list[Document]) -> list[Document]:
    for i, chunk in enumerate(chunks):
        source = chunk.metadata.get("source", "unknown")
        location = chunk.metadata.get("location", "")
        chunk.metadata["chunk_id"] = f"{source}::{location}::{i}"
        chunk.metadata["chunk_index"] = i
    return chunks


def split_documents(
    documents: list[Document],
    chunk_size: int = 800,
    chunk_overlap: int = 120,
    strategy: str = "hybrid",
) -> list[Document]:
    """Split documents. CSV rows and short sections are kept whole when possible."""
    splitter = make_recursive_splitter(chunk_size, chunk_overlap)
    chunks: list[Document] = []

    for doc in documents:
        doc_type = doc.metadata.get("doc_type", "")
        source = str(doc.metadata.get("source", "")).lower()

        # Pricing CSV: already one row per document — do not split further
        if doc_type == "pricing" or source.endswith(".csv"):
            if len(doc.page_content) <= chunk_size * 2:
                chunks.append(doc)
                continue

        if strategy in {"markdown", "hybrid"} and source.endswith(".md"):
            md_chunks = _split_markdown_aware(doc, chunk_size, chunk_overlap, splitter)
            chunks.extend(md_chunks)
            continue

        parts = splitter.split_documents([doc])
        # RecursiveCharacterTextSplitter copies metadata; assert source survived
        for part in parts:
            if "source" not in part.metadata:
                part.metadata["source"] = doc.metadata.get("source", "unknown")
            if "doc_type" not in part.metadata:
                part.metadata["doc_type"] = doc.metadata.get("doc_type", "guide")
        chunks.extend(parts)

    chunks = _ensure_chunk_ids(chunks)
    lengths = [len(c.page_content) for c in chunks]
    if lengths:
        logger.info(
            "Chunking complete: count=%d mean=%d max=%d strategy=%s size=%d overlap=%d",
            len(chunks),
            int(sum(lengths) / len(lengths)),
            max(lengths),
            strategy,
            chunk_size,
            chunk_overlap,
        )
    return chunks


def _split_markdown_aware(
    doc: Document,
    chunk_size: int,
    chunk_overlap: int,
    fallback: RecursiveCharacterTextSplitter,
) -> list[Document]:
    headers = [("#", "h1"), ("##", "h2"), ("###", "h3")]
    try:
        md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers)
        header_docs = md_splitter.split_text(doc.page_content)
    except Exception:  # noqa: BLE001
        return fallback.split_documents([doc])

    out: list[Document] = []
    for hd in header_docs:
        # Merge original metadata with heading metadata
        merged: dict[str, Any] = {**doc.metadata, **hd.metadata}
        heading_parts = [
            str(merged.get(k))
            for k in ("h1", "h2", "h3")
            if merged.get(k)
        ]
        if heading_parts:
            merged["location"] = " > ".join(heading_parts)
            merged["section"] = merged["location"]
        section_doc = Document(page_content=hd.page_content, metadata=merged)
        if len(section_doc.page_content) > chunk_size:
            out.extend(fallback.split_documents([section_doc]))
        else:
            out.append(section_doc)
    return out or fallback.split_documents([doc])


def chunking_stats(chunks: list[Document]) -> dict[str, float | int]:
    lengths = [len(c.page_content) for c in chunks] or [0]
    return {
        "count": len(chunks),
        "mean_length": round(sum(lengths) / len(lengths), 1),
        "max_length": max(lengths),
        "min_length": min(lengths),
    }
