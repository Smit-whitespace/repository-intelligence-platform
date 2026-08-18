# Environment Setup

> **Status:** Complete
> **Last Updated:** Sprint 13

---

## Prerequisites

| Dependency | Version | Purpose |
|-----------|---------|---------|
| Python | >= 3.12, < 3.13 | Backend runtime |
| Node.js | ^18 or ^20 | Frontend build |
| Ollama | Latest | Local LLM and embedding inference |
| Git | Latest | Version control |

## Backend Setup

```bash
# Clone the repository
git clone <repository-url>
cd repository-intelligence-platform

# Install Python dependencies
uv sync

# Activate the virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix

# Start the backend server (from the backend/ directory)
cd backend
uv run python -m uvicorn app.main:app --reload
```

On Windows, if `uv` fails with `uv trampoline failed to canonicalize script path`, launch the backend through the project's virtual environment directly:

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

> The backend resolves all project persistence from the **opened project root** (`<project root>/.local_openclaw/`), never from the process working directory. The backend may be started from any directory.

## Configuration

Configuration is managed via `app/core/config/models.py` (`ApplicationSettings`) and assembled from `EnvironmentSettings` in `app/core/config/provider.py`. Settings load from environment variables (prefix `LOC_`) with sensible defaults. See the [Configuration Reference](../reference/configuration.md).

Key configuration:

| Setting | Default | Description |
|---------|---------|-------------|
| `LOC_SERVER_HOST` / `LOC_SERVER_PORT` | `127.0.0.1` / `8000` | HTTP server |
| `LOC_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `LOC_OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model |
| `LOC_OLLAMA_CHAT_MODEL` | `qwen3:8b` | Chat model |
| Persist directory | `<project root>/.local_openclaw/index/chroma` | Derived from the opened project — not configurable |

## Required Ollama Models

```bash
ollama pull nomic-embed-text
ollama pull qwen3:8b  # or another chat model
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Verification

```bash
# Backend health check (API is versioned under /api/v1)
curl http://localhost:8000/api/v1/health

# Expected: {"status":"healthy","application":"Repository Intelligence Platform (RIP)","version":"0.1.0"}
```
