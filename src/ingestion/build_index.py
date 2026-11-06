"""CLI entry point: build / rebuild the persistent vector index.

Usage:
    python -m src.ingestion.build_index
    python -m src.ingestion.build_index --rebuild
    python -m src.ingestion.build_index --search "how long is the warranty"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path when run as a module
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import load_settings
from src.ingestion.chunking import chunking_stats, split_documents
from src.ingestion.loaders import load_knowledge_base
from src.retrieval.embeddings_factory import embedding_dimension, get_embeddings
from src.retrieval.vector_store import (
    build_vector_store,
    index_exists,
    load_vector_store,
    print_similarity_hits,
    upsert_documents,
)
from src.utils.logging_setup import setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build SupportPearlz vector index")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete the existing index and rebuild from scratch",
    )
    parser.add_argument(
        "--upsert-source",
        type=str,
        default=None,
        help="Incrementally re-ingest a single source filename (delete-by-source + add)",
    )
    parser.add_argument(
        "--search",
        type=str,
        default=None,
        help="After load/build, run a similarity search debug query",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=4,
        help="Top-k for --search",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Write ingestion report to this file path",
    )
    return parser.parse_args()


def run_build(
    settings,
    *,
    rebuild: bool = False,
    upsert_source: str | None = None,
    search: str | None = None,
    k: int = 4,
    report_path: str | Path | None = None,
) -> int:
    """Programmatic index build used by CLI and Streamlit."""
    logger = setup_logging(settings.log_level, settings.log_file)
    # Index build only needs embedding credentials (HF/Ollama need none).
    settings.require_embedding_credentials()

    logger.info(
        "Index build starting | kb=%s | store=%s | embed=%s/%s | dim=%s",
        settings.knowledge_base_path,
        settings.vector_store_path,
        settings.embedding_provider,
        settings.embedding_model,
        embedding_dimension(settings),
    )

    result = load_knowledge_base(settings.knowledge_base_path)
    report = result.summary()
    print(report)
    if report_path:
        Path(report_path).write_text(report, encoding="utf-8")
        logger.info("Wrote ingestion report to %s", report_path)

    if result.files_loaded == 0:
        logger.error("No documents loaded — aborting index build")
        return 1

    chunks = split_documents(
        result.documents,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        strategy=settings.chunk_strategy,
    )
    stats = chunking_stats(chunks)
    print(
        f"\nChunks: {stats['count']} | mean={stats['mean_length']} "
        f"| max={stats['max_length']} | min={stats['min_length']}"
    )

    embeddings = get_embeddings(settings)

    if upsert_source:
        if not index_exists(settings.vector_store_path, settings.vector_store_collection):
            logger.error("No existing index to upsert into — run a full build first")
            return 1
        store = load_vector_store(embeddings, settings)
        subset = [c for c in chunks if c.metadata.get("source") == upsert_source]
        if not subset:
            logger.error("No chunks found for source=%s", upsert_source)
            return 1
        n = upsert_documents(store, subset, replace_sources=True)
        print(f"Upserted {n} chunks for source={upsert_source}")
    elif rebuild or not index_exists(
        settings.vector_store_path, settings.vector_store_collection
    ):
        store = build_vector_store(chunks, embeddings, settings, rebuild=rebuild)
        print(
            f"\nIndex built: collection={settings.vector_store_collection} "
            f"chunks={len(chunks)} path={settings.vector_store_path}"
        )
    else:
        store = load_vector_store(embeddings, settings)
        print(
            f"\nIndex already exists — loaded from disk (no re-embed). "
            f"Use --rebuild to force a full rebuild."
        )

    if search:
        print_similarity_hits(store, search, k=k)

    return 0


def main() -> int:
    args = parse_args()
    settings = load_settings()
    return run_build(
        settings,
        rebuild=args.rebuild,
        upsert_source=args.upsert_source,
        search=args.search,
        k=args.k,
        report_path=args.report,
    )


if __name__ == "__main__":
    raise SystemExit(main())
