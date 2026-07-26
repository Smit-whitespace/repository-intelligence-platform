# Configuration Reference

> **Status:** Complete
> **Last Updated:** Sprint 12.1

---

## Settings Model

Configuration is managed by `app/core/config/settings.py`. Settings load from environment variables with sensible defaults.

## Storage

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `storage.root_directory` | `Path` | `~/.local-openclaw` | Application data root |

## Ollama

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ollama.base_url` | `str` | `http://localhost:11434` | Ollama server URL |
| `ollama.embedding_model` | `str` | `nomic-embed-text` | Embedding model name |
| `ollama.chat_model` | `str` | `qwen3:8b` | Chat model name |
| `ollama.num_ctx` | `int` | `4096` | Model context window |
| `ollama.num_predict` | `int` | `1024` | Maximum tokens to generate |

## Chroma

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `chroma.persist_directory` | `Path` | `{storage.root_directory}/chroma` | ChromaDB persistence path |
| `chroma.collection_name` | `str` | `repository_chunks` | Vector collection name |

## Loading Order

1. Environment variables (highest priority)
2. `.env` file in project root (if present)
3. Default values from settings model

## Example `.env`

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_CHAT_MODEL=qwen3:8b
STORAGE_ROOT_DIRECTORY=~/.local-openclaw
```
