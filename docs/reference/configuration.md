# Configuration Reference

> **Status:** Complete
> **Last Updated:** Sprint 13

---

## Settings Model

Configuration is managed by `app/core/config/models.py` (`ApplicationSettings` and nested settings models), built by `EnvironmentSettings` in `app/core/config/provider.py`. Settings load from environment variables (prefix `LOC_`) with sensible defaults; unknown `LOC_*` keys are ignored.

## Server

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `LOC_SERVER_HOST` | `str` | `127.0.0.1` | HTTP bind host |
| `LOC_SERVER_PORT` | `int` | `8000` | HTTP bind port |

## Logging

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `LOC_LOGGING_LEVEL` | `str` | `INFO` | Log level |
| `LOC_LOGGING_JSON_LOGS` | `bool` | `False` | Structured JSON logs |

## Ollama

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `LOC_OLLAMA_BASE_URL` | `str` | `http://localhost:11434` | Ollama server URL |
| `LOC_OLLAMA_EMBEDDING_MODEL` | `str` | `nomic-embed-text` | Embedding model name |
| `LOC_OLLAMA_CHAT_MODEL` | `str` | `qwen3:8b` | Chat model name |
| `LOC_OLLAMA_TIMEOUT_SECONDS` | `int` | `120` | Ollama request timeout |

## Chroma

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `LOC_CHROMA_COLLECTION_NAME` | `str` | `repository_chunks` | Vector collection name |

> [!IMPORTANT] There is **no persist-directory setting.** The ChromaDB persistence directory is derived from the opened project root: `<project root>/.local_openclaw/index/chroma`. Persistence identity never depends on the process working directory (see [ADR-0010](../adr/adr-0010-filesystem-persistence.md)).

## Indexing

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `LOC_INDEXING_CHUNK_SIZE` | `int` | `512` | Chunk size (characters) |
| `LOC_INDEXING_CHUNK_OVERLAP` | `int` | `64` | Chunk overlap |

## Legacy (Ignored) Keys

The following keys existed before Sprint 13 and are **ignored** by the settings loader. They are retained in the sample `.env` only as documentation of the former CWD-based behavior:

| Key | Former meaning |
|-----|----------------|
| `LOC_STORAGE_ROOT_DIRECTORY` | Former application data root |
| `LOC_CHROMA_PERSIST_DIRECTORY` | Former ChromaDB persistence path |
| `LOC_OLLAMA_MODEL_NAME` | Former chat model name (use `LOC_OLLAMA_CHAT_MODEL`) |

## Loading Order

1. Environment variables (highest priority)
2. `.env` file in the project root (path resolved from the backend module location — not the process CWD)
3. Default values from settings model

## Example `.env`

```env
LOC_SERVER_HOST=127.0.0.1
LOC_SERVER_PORT=8000
LOC_OLLAMA_BASE_URL=http://localhost:11434
LOC_OLLAMA_EMBEDDING_MODEL=nomic-embed-text
LOC_OLLAMA_CHAT_MODEL=qwen3:8b
LOC_CHROMA_COLLECTION_NAME=repository_chunks
LOC_INDEXING_CHUNK_SIZE=512
LOC_INDEXING_CHUNK_OVERLAP=64
```
