"""Interactive CLI chat for SupportPearlz.

Usage:
    python -m src.app_cli

Commands:
    /reset   — clear conversation history
    /quit    — exit
    /sources — show last citations again
    /filter <doc_type> — constrain next retrieval (policy|faq|pricing|manual|guide)
    /clearfilter — remove metadata filter
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.chains.rag_chain import build_agent
from src.config import load_settings
from src.retrieval.vector_store import index_exists, read_index_meta
from src.utils.logging_setup import setup_logging


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║  SupportPearlz — Pearlz Home Systems knowledge assistant     ║
║  Type your question. Commands: /reset  /quit  /help          ║
╚══════════════════════════════════════════════════════════════╝
"""


def main() -> int:
    settings = load_settings()
    logger = setup_logging(settings.log_level, settings.log_file)
    session_id = str(uuid.uuid4())[:8]
    logger.info("CLI session started id=%s", session_id)

    try:
        settings.require_llm_credentials()
    except RuntimeError as exc:
        print(f"CONFIG ERROR: {exc}")
        return 1

    if not index_exists(settings.vector_store_path, settings.vector_store_collection):
        print(
            "No vector index found. Build it first:\n"
            "  python -m src.ingestion.build_index\n"
        )
        return 1

    meta = read_index_meta(settings.vector_store_path) or {}
    try:
        agent = build_agent(settings)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to start agent: {exc}")
        logger.exception("Agent init failed")
        return 1

    print(BANNER)
    print(
        f"[Session {session_id} | knowledge base: {settings.vector_store_collection} "
        f"| {meta.get('chunk_count', '?')} chunks | embed={meta.get('embedding_model', '?')}]"
    )
    print()

    last_response = None
    active_filter: dict | None = None

    while True:
        try:
            user = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user:
            continue

        lower = user.lower()
        if lower in {"/quit", "/exit", "quit", "exit"}:
            print("Goodbye.")
            break
        if lower in {"/reset", "/clear"}:
            agent.reset_session()
            print("Bot > Session history cleared.\n")
            continue
        if lower in {"/help"}:
            print(__doc__)
            continue
        if lower.startswith("/filter"):
            parts = user.split(maxsplit=1)
            if len(parts) < 2:
                print("Usage: /filter <doc_type>")
                continue
            active_filter = {"doc_type": parts[1].strip()}
            print(f"Bot > Metadata filter set: {active_filter}\n")
            continue
        if lower == "/clearfilter":
            active_filter = None
            print("Bot > Metadata filter cleared.\n")
            continue
        if lower == "/sources":
            if last_response is None:
                print("Bot > No previous answer.\n")
            else:
                print(last_response.render())
                print()
            continue

        try:
            response = agent.ask(user, filter_metadata=active_filter)
            last_response = response
            print()
            print("Bot > " + response.render().replace("\n", "\n      "))
            if response.rewritten_query != response.original_query:
                print(f"\n      (rewritten query: {response.rewritten_query})")
            print()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unhandled turn error: %s", exc)
            print(
                f"Bot > Something went wrong processing that request. "
                f"Please try again or contact {settings.support_escalation_email}.\n"
                f"      (detail: {exc})\n"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
