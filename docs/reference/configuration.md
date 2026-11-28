# Configuration Reference

> **Status:** Complete
> **Last Updated:** Sprint 14

---

## Settings Model

Configuration is managed by `app/core/config/models.py` (`ApplicationSettings` and nested settings models), built by `EnvironmentSettings` in `app/core/config/provider.py`. Settings load from environment variables, or the repository's `.env` file, with the prefix `RIP_` and sensible defaults; unknown `RIP_*` keys are ignored. The former prefix `LOC_` still works: a setting given only as `LOC_*` is used, and a warning names the `RIP_*` variable to rename it to ([ADR-0021](../adr/adr-0021-rip-storage-and-settings-names.md)).

## Server

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `RIP_SERVER_HOST` | `str` | `127.0.0.1` | HTTP bind host |
| `RIP_SERVER_PORT` | `int` | `8000` | HTTP bind port |
| `RIP_SERVER_ALLOWED_HOSTS` | `str` | `localhost,127.0.0.1` | Comma-separated `Host` header values the API accepts; anything else gets HTTP 400. This blocks DNS-rebinding attacks from web pages. Add a name here only if you deliberately reach the API through it. |

### Models

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `RIP_MODEL_CONFIG_PATH` | `str` | `~/.rip/models.json` | Model configuration file (providers, primary model, overrides, embedding). Until it exists, the `RIP_OLLAMA_*` settings below are the configuration. See [Model Configuration](../architecture/backend/models.md). |

### Security

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `RIP_INTEGRITY_KEY_PATH` | `str` | `~/.rip/integrity.key` | Key that signs proposals, snapshots and validation commands ([ADR-0019](../adr/adr-0019-signed-project-state.md)). Created on first use. |
| `RIP_API_TOKEN_PATH` | `str` | `~/.rip/api.token` | Token every REST request except `/health` must send as `Authorization: Bearer <token>` ([ADR-0020](../adr/adr-0020-local-api-token.md)). Created on first use; delete it to issue a new one. |
| `RIP_SERVER_FRONTEND_URL` | `str` | `http://localhost:5173` | Where the RIP app runs: the base of the sign-in link printed at startup, and an origin allowed to call the API from a browser. Must start with `http://` or `https://` (the backend refuses to start otherwise). |

### Frontend

| Setting | Where | Default | Description |
|---------|-------|---------|-------------|
| `RIP_BACKEND_URL` | shell environment for `npm run dev` | `http://127.0.0.1:8000` | Target of the Vite dev proxy for `/api` |
| `VITE_API_BASE_URL` | `frontend/.env.local` (git-ignored) | unset (`/api/v1` through the proxy) | Full API base URL, bypassing the proxy; see `frontend/.env.example` |

## Logging

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `RIP_LOGGING_LEVEL` | `str` | `INFO` | Log level |
| `RIP_LOGGING_JSON_LOGS` | `bool` | `False` | Structured JSON logs |

## Ollama

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `RIP_OLLAMA_BASE_URL` | `str` | `http://localhost:11434` | Ollama server URL |
| `RIP_OLLAMA_EMBEDDING_MODEL` | `str` | `nomic-embed-text` | Embedding model name |
| `RIP_OLLAMA_CHAT_MODEL` | `str` | `qwen3:8b` | Chat model name |
| `RIP_OLLAMA_TIMEOUT_SECONDS` | `int` | `120` | Ollama request timeout |

## Chroma

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `RIP_CHROMA_COLLECTION_NAME` | `str` | `repository_chunks` | Vector collection name |

> [!IMPORTANT] There is **no persist-directory setting.** The ChromaDB persistence directory is derived from the opened project root: `<project root>/.rip/index/chroma`. Persistence identity never depends on the process working directory (see [ADR-0010](../adr/adr-0010-filesystem-persistence.md)).

## Indexing

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `RIP_INDEXING_CHUNK_SIZE` | `int` | `512` | Chunk size (characters) |
| `RIP_INDEXING_CHUNK_OVERLAP` | `int` | `64` | Chunk overlap |
| `RIP_INDEXING_REFRESH_SECONDS` | `int` | `15` | Most time spent updating files changed since indexing before a chat answer or semantic search; the rest finishes in the background and the answer notes the files it may miss. `0` turns automatic updates off (changes are still reported). An index built with a different embedding model is never updated automatically. |

## Legacy (Ignored) Keys

The following keys existed before Sprint 13 and are **ignored** by the settings loader. They are retained in the sample `.env` only as documentation of the former CWD-based behavior:

| Key | Former meaning |
|-----|----------------|
| `RIP_STORAGE_ROOT_DIRECTORY` | Former application data root |
| `RIP_CHROMA_PERSIST_DIRECTORY` | Former ChromaDB persistence path |
| `RIP_OLLAMA_MODEL_NAME` | Former chat model name (use `RIP_OLLAMA_CHAT_MODEL`) |

## Loading Order

1. Environment variables (highest priority)
2. `.env` file in the project root (path resolved from the backend module location — not the process CWD)
3. Default values from settings model

## Example `.env`

```env
RIP_SERVER_HOST=127.0.0.1
RIP_SERVER_PORT=8000
RIP_OLLAMA_BASE_URL=http://localhost:11434
RIP_OLLAMA_EMBEDDING_MODEL=nomic-embed-text
RIP_OLLAMA_CHAT_MODEL=qwen3:8b
RIP_CHROMA_COLLECTION_NAME=repository_chunks
RIP_INDEXING_CHUNK_SIZE=512
RIP_INDEXING_CHUNK_OVERLAP=64
```
