"""Chroma vector store: create, persist, load, incremental update."""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

from langchain_core.documents import Document
from langchain_chroma import Chroma

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings

    from src.config import Settings

logger = logging.getLogger("supportpearlz.vector_store")

META_FILENAME = "index_meta.json"


def _meta_path(persist_dir: Path) -> Path:
    return persist_dir / META_FILENAME


def write_index_meta(persist_dir: Path, meta: dict[str, Any]) -> None:
    persist_dir.mkdir(parents=True, exist_ok=True)
    _meta_path(persist_dir).write_text(json.dumps(meta, indent=2), encoding="utf-8")


def read_index_meta(persist_dir: Path) -> dict[str, Any] | None:
    path = _meta_path(persist_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def index_exists(persist_dir: Path, collection: str) -> bool:
    meta = read_index_meta(persist_dir)
    if not meta:
        return False
    chroma_dir = persist_dir / "chroma"
    return meta.get("collection") == collection and chroma_dir.exists()


def build_vector_store(
    chunks: list[Document],
    embeddings: Embeddings,
    settings: Settings,
    *,
    rebuild: bool = False,
) -> Chroma:
    """Embed chunks and persist a Chroma collection to disk."""
    persist_dir = settings.vector_store_path
    chroma_dir = persist_dir / "chroma"

    if rebuild and persist_dir.exists():
        logger.info("Rebuild requested — removing existing store at %s", persist_dir)
        shutil.rmtree(persist_dir)

    persist_dir.mkdir(parents=True, exist_ok=True)
    chroma_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Building vector store: %d chunks -> collection=%s",
        len(chunks),
        settings.vector_store_collection,
    )
    store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=settings.vector_store_collection,
        persist_directory=str(chroma_dir),
        collection_metadata={"hnsw:space": settings.vector_store_distance},
    )

    write_index_meta(
        persist_dir,
        {
            "collection": settings.vector_store_collection,
            "embedding_provider": settings.embedding_provider,
            "embedding_model": settings.active_embedding_model(),
            "chunk_count": len(chunks),
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "distance": settings.vector_store_distance,
        },
    )
    logger.info("Vector store persisted to %s (%d chunks)", chroma_dir, len(chunks))
    return store


def load_vector_store(embeddings: Embeddings, settings: Settings) -> Chroma:
    """Load a previously persisted Chroma index (no re-embedding)."""
    persist_dir = settings.vector_store_path
    chroma_dir = persist_dir / "chroma"
    if not index_exists(persist_dir, settings.vector_store_collection):
        raise FileNotFoundError(
            f"No persisted vector store found at {persist_dir}. "
            "Run: python -m src.ingestion.build_index"
        )

    meta = read_index_meta(persist_dir) or {}
    expected = settings.active_embedding_model()
    stored_model = meta.get("embedding_model")
    stored_provider = meta.get("embedding_provider")
    if stored_model and stored_model != expected:
        raise RuntimeError(
            f"Embedding model mismatch: index was built with '{stored_model}' "
            f"(provider={stored_provider or 'unknown'}) but config has '{expected}' "
            f"(provider={settings.embedding_provider}). "
            "Set EMBEDDING_PROVIDER/HF_EMBEDDING_MODEL to match the index, "
            "or rebuild: python -m src.ingestion.build_index --rebuild"
        )

    logger.info(
        "Loading vector store from disk (no re-embed): %s | meta=%s",
        chroma_dir,
        meta,
    )
    return Chroma(
        collection_name=settings.vector_store_collection,
        embedding_function=embeddings,
        persist_directory=str(chroma_dir),
    )


def load_or_build(
    chunks: list[Document] | None,
    embeddings: Embeddings,
    settings: Settings,
    *,
    rebuild: bool = False,
) -> Chroma:
    if not rebuild and index_exists(
        settings.vector_store_path, settings.vector_store_collection
    ):
        return load_vector_store(embeddings, settings)
    if chunks is None:
        raise ValueError("chunks required when building a new index")
    return build_vector_store(chunks, embeddings, settings, rebuild=rebuild)


def delete_by_source(store: Chroma, source: str) -> int:
    """Remove all chunks whose metadata.source matches (for incremental update)."""
    try:
        existing = store.get(where={"source": source})
    except Exception:  # noqa: BLE001
        # Older chroma filter fallback: fetch all and filter
        existing = store.get()
        ids = [
            i
            for i, m in zip(existing["ids"], existing["metadatas"] or [])
            if (m or {}).get("source") == source
        ]
        if ids:
            store.delete(ids=ids)
            return len(ids)
        return 0

    ids = existing.get("ids") or []
    if ids:
        store.delete(ids=ids)
        logger.info("Deleted %d chunks for source=%s", len(ids), source)
    return len(ids)


def upsert_documents(
    store: Chroma,
    documents: list[Document],
    *,
    replace_sources: bool = True,
) -> int:
    """Incrementally update: optionally delete-by-source then add."""
    if replace_sources:
        sources = {d.metadata.get("source", "") for d in documents}
        for source in sources:
            if source:
                delete_by_source(store, source)
    store.add_documents(documents)
    return len(documents)


def similarity_search_debug(
    store: Chroma,
    query: str,
    k: int = 4,
) -> list[tuple[Document, float]]:
    """Return (doc, score) pairs. Score is similarity (higher is better for cosine)."""
    pairs = store.similarity_search_with_relevance_scores(query, k=k)
    return [(doc, float(score)) for doc, score in pairs]


def print_similarity_hits(
    store: Chroma,
    query: str,
    k: int = 4,
) -> None:
    hits = similarity_search_debug(store, query, k=k)
    print(f"\nQuery: {query!r}  (k={k})")
    print("-" * 72)
    for i, (doc, score) in enumerate(hits, start=1):
        src = doc.metadata.get("source", "?")
        loc = doc.metadata.get("location", "")
        preview = doc.page_content[:200].replace("\n", " ")
        print(f"[{i}] score={score:.4f}  source={src}  location={loc}")
        print(f"    {preview}…")
        print()
