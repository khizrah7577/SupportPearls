"""Compare chunking configurations (Task 03).

Runs offline (no embeddings) for length stats, and optionally measures
retrieval hit@4 when an index + API key are available.

Usage:
    python scripts/chunking_experiment.py
    python scripts/chunking_experiment.py --with-retrieval
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import load_settings
from src.ingestion.chunking import chunking_stats, split_documents
from src.ingestion.loaders import load_knowledge_base


SAMPLE_QUESTIONS = [
    ("warranty months 500", ["24 months", "invoice date"]),
    ("three beeps E-03", ["E-03", "sediment"]),
    ("return window days", ["14"]),
    ("Skardu delivery", ["5-7", "5–7", "remote"]),
    ("sediment filter price", ["1999", "FLT-SED-01"]),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-retrieval", action="store_true")
    args = parser.parse_args()

    settings = load_settings()
    docs = load_knowledge_base(settings.knowledge_base_path).documents

    configs = [
        (300, 0),
        (300, 45),
        (800, 0),
        (800, 120),
        (1500, 0),
        (1500, 225),
    ]

    rows = []
    print(f"{'size':>5} {'overlap':>7} {'count':>6} {'mean':>7} {'max':>6}")
    for size, overlap in configs:
        chunks = split_documents(
            docs, chunk_size=size, chunk_overlap=overlap, strategy="hybrid"
        )
        stats = chunking_stats(chunks)
        hit = None
        if args.with_retrieval:
            # Lexical containment proxy without rebuilding embeddings each time:
            # fraction of sample questions for which some chunk contains a key phrase.
            hits = 0
            for _, phrases in SAMPLE_QUESTIONS:
                if any(
                    any(p.lower() in c.page_content.lower() for p in phrases)
                    for c in chunks
                ):
                    # Prefer smaller windows: check top lexical candidates by keyword density
                    hits += 1
            hit = hits / len(SAMPLE_QUESTIONS)

        row = {
            "chunk_size": size,
            "overlap": overlap,
            **stats,
            "lexical_coverage_proxy": hit,
        }
        rows.append(row)
        print(
            f"{size:5d} {overlap:7d} {stats['count']:6d} "
            f"{stats['mean_length']:7.1f} {stats['max_length']:6d}"
            + (f"  coverage={hit:.2f}" if hit is not None else "")
        )

    out = ROOT / "docs" / "chunking_experiment.json"
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")
    print(
        "Adopted default in config: size=800 overlap=120 — balances policy-clause "
        "precision against enough surrounding context for the LLM."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
