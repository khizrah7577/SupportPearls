"""Embed three sentences and print pairwise cosine similarities.

Usage:
    python scripts/embedding_diagnostic.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import load_settings
from src.retrieval.embeddings_factory import embedding_dimension, get_embeddings


def cosine(a: list[float], b: list[float]) -> float:
    va = np.array(a, dtype=float)
    vb = np.array(b, dtype=float)
    return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb)))


def main() -> int:
    settings = load_settings()
    settings.require_llm_credentials()
    embeddings = get_embeddings(settings)

    s1 = "The AquaPearl 500 Pro beeps three times when the sediment filter is full."
    s2 = "Three short beeps mean the pre-filter has reached saturation on the 500 Pro."
    s3 = "Pearlz ships next-day only to Karachi, Lahore and Islamabad."

    vectors = embeddings.embed_documents([s1, s2, s3])
    pairs = [("s1-s2 (paraphrases)", 0, 1), ("s1-s3 (unrelated)", 0, 2), ("s2-s3 (unrelated)", 1, 2)]

    print(f"Embedding model: {settings.embedding_model}")
    print(f"Documented dimension: {embedding_dimension(settings)}")
    print(f"Observed dimension: {len(vectors[0])}")
    print()
    for label, i, j in pairs:
        print(f"{label}: {cosine(vectors[i], vectors[j]):.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
