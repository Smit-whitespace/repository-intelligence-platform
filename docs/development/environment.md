# Environment Setup

> **Status:** Complete
> **Last Updated:** Sprint 12.1

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
cd local-openclaw

# Install Python dependencies
uv sync

# Activate the virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix

# Start the backend server
uv run uvicorn app.main:app --reload
```

## Configuration

Configuration is managed via `app/core/config/settings.py`. The settings model loads from environment variables with sensible defaults.

Key configuration:

| Setting | Default | Description |
|---------|---------|-------------|
| `storage.root_directory` | `~/.local-openclaw` | Application data directory |
| `ollama.base_url` | `http://localhost:11434` | Ollama server URL |
| `ollama.embedding_model` | `nomic-embed-text` | Embedding model |
| `ollama.chat_model` | `qwen3:8b` | Chat model |

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
# Backend health check
curl http://localhost:8000/health

# Expected: {"status":"healthy","application":"Repository Intelligence Platform (RIP)","version":"0.1.0"}
```
