# SupportPearlz

Retrieval-augmented customer support knowledge agent for **Pearlz Home Systems**, built with Python and LangChain.

Ingestion builds a **persistent** Chroma index once. The query path loads that index from disk, rewrites follow-ups into standalone questions, retrieves relevant chunks, and generates a **schema-validated** answer with citations — or refuses when the knowledge base does not support an answer.

## Prerequisites

- Python **3.10–3.12** recommended (3.13+ may work depending on wheel availability)
- An OpenAI API key **or** a local Ollama instance
- ~500 MB disk for dependencies / local embedding models

Recorded environment for this submission: see `python --version` after creating the venv.

## Quick start

```bash
cd SupportPearls
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # then edit .env with your API key
```

### 1. Generate binary KB documents (PDF / DOCX)

Markdown and CSV files are already in `data/knowledge_base/`. Generate the PDFs and DOCX once:

```bash
python scripts/generate_kb_binaries.py
```

### 2. Build the vector index (once per KB update)

```bash
python -m src.ingestion.build_index --rebuild
```

Smoke-check similarity search:

```bash
python -m src.ingestion.build_index --search "how long is the warranty"
```

### 3. Chat — Streamlit UI (recommended)

```bash
streamlit run app.py
```

Opens a branded login screen where you paste your **OpenAI API key at runtime** (session-only; not written to disk by the UI). After connecting you get multi-turn chat with citations, confidence badges, follow-up rewriting, and a sidebar to rebuild the index or filter by document type.

### 4. Chat — CLI

```bash
python -m src.app_cli
```

Commands inside the CLI: `/reset`, `/quit`, `/filter policy`, `/clearfilter`, `/sources`.

### 5. Configuration smoke check

```bash
python -m src.config
```

## Environment variables

See `.env.example` for the full list. Important keys:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Required when using OpenAI for LLM or embeddings |
| `LLM_PROVIDER` / `LLM_MODEL` | Chat model selection |
| `EMBEDDING_PROVIDER` / `EMBEDDING_MODEL` | Must match the model used to build the index |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | Chunking tunables |
| `RETRIEVAL_K` / `RETRIEVAL_STRATEGY` / `SCORE_THRESHOLD` | Retriever policy |
| `VECTOR_STORE_PATH` | Persisted Chroma directory (git-ignored) |

**No API keys or magic numbers belong in business logic** — change behaviour via `.env`.

### Local / free path (Ollama + HuggingFace)

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
EMBEDDING_PROVIDER=huggingface
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

Rebuild the index after changing the embedding model.

## Project layout

```
supportpearlz/
├── data/knowledge_base/     # authored Pearlz documents (10+)
├── data/vector_store/       # persisted Chroma index (git-ignored)
├── src/
│   ├── config.py
│   ├── app_cli.py
│   ├── app_streamlit.py     # Streamlit UI + API-key login
│   ├── ingestion/           # loaders, chunking, build_index
│   ├── retrieval/           # vector store, retriever, embeddings
│   ├── chains/              # prompts, schemas, memory, rag_chain
│   └── utils/logging_setup.py
├── app.py                   # streamlit run app.py
├── evaluation/              # test_questions.json + run_eval.py
├── scripts/                 # KB generators + diagnostics
└── docs/                    # architecture, report, screenshots
```

## Evaluation

```bash
python -m evaluation.run_eval
```

Results land in `evaluation/results/` as JSON + a readable table.

## Incremental policy updates

If e.g. `refund_returns_policy.md` changes:

```bash
python -m src.ingestion.build_index --upsert-source refund_returns_policy.md
```

This **deletes chunks by source** then re-inserts — avoiding stale+new contradictions from a naive append. Full rebuild: `--rebuild`.

## Diagnostics

```bash
python scripts/embedding_diagnostic.py
python scripts/chunking_experiment.py --with-retrieval
```

## Known limitations

- Relevance score scales are store/model specific; recalibrate `SCORE_THRESHOLD` after any embedding change.
- Query condensation can mis-resolve referents on abrupt topic switches (logged as original vs rewritten).
- Auto-eval scoring is heuristic; Task 11 report should include manual verdicts.
- Hybrid search / reranker are optional advanced challenges, not required for the core mark set.

## License / academic integrity

Course assignment prototype for AAI–407 / PRAC–03. Knowledge base content is fictional.
