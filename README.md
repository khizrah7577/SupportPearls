# SupportPearlz

Premium Streamlit application for **Pearlz Home Systems** — a grounded LangChain RAG customer-support assistant with real user accounts, conversation history, citations, and a modern SaaS-style UI.

## Features

- **Secure auth** — signup / login / password reset with **bcrypt** password hashes (SQLite)
- **Dashboard** — welcome, usage stats from your real conversations, recent chats, suggested prompts
- **Premium chat** — grounded RAG answers, citations, confidence badges, regenerate, feedback, export
- **History** — search, rename, categorize, delete; conversations isolated per user
- **Settings** — profile, preferred model, session API key, password change
- **RAG pipeline** — persistent Chroma index, query condensation, structured outputs, refusals

## Quick start (local)

```bash
cd SupportPearls
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
```

Generate binary KB docs (PDF / DOCX) if needed:

```bash
python scripts/generate_kb_binaries.py
```

Build the vector index once:

```bash
python -m src.ingestion.build_index --rebuild
```

Launch the app:

```bash
streamlit run app.py
```

1. Create an account on the login screen  
2. Open **Settings** and paste your OpenAI API key (session-only), **or** set `OPENAI_API_KEY` in `.env` / Streamlit secrets  
3. Start chatting  

CLI still available: `python -m src.app_cli`

## Streamlit Cloud

1. Connect the GitHub repo `khizrah7577/SupportPearls`  
2. Main file: `app.py`  
3. Branch: `main`  
4. In **Secrets**, add:

```toml
OPENAI_API_KEY = "sk-..."
```

5. Deploy. On first run, open Chat → **Build index now** if the vector store is empty (Cloud does not ship the local Chroma folder).

> Note: user accounts and chat history use SQLite under `data/app.db`. On Streamlit Cloud the filesystem can reset when the app sleeps/redeploys — for production persistence use an external database.

## Environment

See `.env.example`. Important:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Chat (and OpenAI embeddings if selected) |
| `EMBEDDING_PROVIDER` | `huggingface` (default local) or `openai` |
| `LLM_MODEL` | Chat model |
| `RETRIEVAL_K` / `SCORE_THRESHOLD` | Retriever policy |

## Project layout

```
app.py                      # Streamlit entry
src/
  auth/                     # bcrypt auth + SQLite users
  storage/                  # conversations & messages
  services/                 # RAG agent lifecycle
  ui/                       # theme, components, views
  ingestion/ retrieval/ chains/   # LangChain RAG core
data/knowledge_base/        # authored Pearlz documents
```

## Security

- Passwords are **bcrypt-hashed** — never stored in plain text  
- API keys are **not** stored in the user database (session / secrets / `.env` only)  
- `.env`, `.venv`, `data/app.db`, and `data/vector_store/` are gitignored  

## License / academic integrity

Course assignment prototype for AAI–407 / PRAC–03. Knowledge base content is fictional.
