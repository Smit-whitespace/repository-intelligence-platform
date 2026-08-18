# Repository Intelligence Platform (RIP) Startup

## Prerequisites

- Python 3.12
- `uv`
- Ollama
- Git

## Backend Setup

From the repository root:

```powershell
uv sync
```

Optional environment overrides use the existing `LOC_` prefix:

```powershell
$env:LOC_SERVER_HOST="127.0.0.1"
$env:LOC_SERVER_PORT="8000"
$env:LOC_OLLAMA_BASE_URL="http://localhost:11434"
$env:LOC_OLLAMA_CHAT_MODEL="qwen3:8b"
$env:LOC_OLLAMA_EMBEDDING_MODEL="nomic-embed-text"
```

> The `LOC_STORAGE_ROOT_DIRECTORY` and `LOC_CHROMA_PERSIST_DIRECTORY` keys in the sample `.env` are legacy and ignored. Persistence identity is derived from the opened project root, never from the process working directory: `<project root>/.local_openclaw/` contains `project.json`, `index/chroma/`, and `snapshots/`.

## Ollama Setup

Install Ollama, then install the required models:

```powershell
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

Verify Ollama is running:

```powershell
ollama list
```

## Start Backend

From `backend`:

```powershell
uv run python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

On Windows, `uv` itself may fail from the repository root with `uv trampoline failed to canonicalize script path` — this is an environment/tooling issue, not an application failure. Two reliable alternatives:

```powershell
# 1. Run from the backend/ directory (as above)

# 2. Use the project virtual environment directly
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The backend resolves all project persistence from the opened project root, so its own working directory does not affect where indexes are stored.

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

Frontend startup status:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/system/status
```

## Frontend Setup

From the `frontend` directory:

```powershell
npm run dev
```

## Quality Gates

All gates may be run from the `backend` directory:

```powershell
uv run ruff check app tests scripts eval
uv run python -m mypy app
uv run python -m pytest tests -q
```

Ruff may also be run from the repository root:

```powershell
uv run ruff check backend/app backend/tests backend/scripts backend/eval
```

> MyPy and Pytest are reliable when run from `backend/`. Running them from the repository root can hit the Windows `uv` trampoline issue above.

## Troubleshooting

- If `/api/v1/models` fails, confirm Ollama is running and `LOC_OLLAMA_BASE_URL` points to it.
- If chat fails, confirm the active chat model appears in `ollama list`.
- If retrieval fails, confirm the embedding model appears in `ollama list`.
- If storage fails, confirm the process can create and write `.local_openclaw` inside the opened project root.
- If `uv` is not found, install `uv` or add it to `PATH`.
- If `uv run` fails with `uv trampoline failed to canonicalize script path`, use the project virtual environment directly (see Start Backend).
