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
$env:LOC_OLLAMA_CHAT_MODEL="qwen3.6"
$env:LOC_OLLAMA_EMBEDDING_MODEL="nomic-embed-text"
```

## Ollama Setup

Install Ollama, then install the required models:

```powershell
ollama pull qwen3.6
ollama pull nomic-embed-text
```

Verify Ollama is running:

```powershell
ollama list
```

## Start Backend

From `backend`:

```powershell
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

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

From the repository root:

```powershell
uv run ruff check .
uv run mypy backend/app
uv run pytest
```

## Troubleshooting

- If `/api/v1/models` fails, confirm Ollama is running and `LOC_OLLAMA_BASE_URL` points to it.
- If chat fails, confirm the active chat model appears in `ollama list`.
- If retrieval fails, confirm the embedding model appears in `ollama list`.
- If storage fails, confirm the process can create and write `.local_openclaw`.
- If `uv` is not found, install `uv` or add it to `PATH`.
