# Model Configuration

> **Status:** Complete
> **Reading Time:** 5 minutes
> **Audience:** Users choosing models, backend contributors
> **Related ADRs:** ADR-0001, ADR-0016, ADR-0018
> **Related APIs:** `GET`/`PUT /models/configuration`, `GET /models/effective`, `GET`/`PUT /settings/model`

---

## Executive Summary

RIP can use local models (Ollama) and hosted models (OpenAI-compatible APIs, Anthropic). Configuration is progressive: set one **primary** model and stop there, or override it per **capability** or per **task**. The **embedding** model is configured separately because changing it invalidates the search index. The Settings page shows which model every operation uses and why.

With no configuration saved, RIP uses your `RIP_OLLAMA_*` settings, exactly as before.

---

## How a model is chosen

For a generation task, the first configured level wins:

| Level | Setting | Example |
|-------|---------|---------|
| 3. Task | `tasks["chat.answer"]` | A specific model only for chat answers |
| 2. Capability | `capabilities["chat"]`, `capabilities["edit"]` | A stronger model for code editing |
| 1. Primary | `primary` (required) | The default for everything |

The embedding model is its own setting (`embedding`) and never follows the primary model.

If a configured model cannot do what is asked, or its API key is missing, RIP reports a clear error naming what to fix. It **never falls back** to another model or provider on its own.

---

## Configuration file

The file lives at `~/.rip/models.json` (override the location with `RIP_MODEL_CONFIG_PATH`). It is per user, so it can never be committed with a repository. Edit it, or send it to `PUT /api/v1/models/configuration`. Changes apply on the next request, with no restart.

API keys are **never** stored. Each provider names an environment variable (`api_key_env`), which is read when the model is used. Set the variable before starting RIP. The name must end in `_API_KEY` (so a configuration can never read, say, `AWS_SECRET_ACCESS_KEY`), and a key is only sent to a non-local server over `https://`.

Changes apply on the next request in every RIP process, including MCP servers started by agents and edits made to the file by hand: each request first checks whether the file changed.

### Example: local primary, hosted override for editing

```json
{
  "providers": {
    "ollama": { "type": "ollama" },
    "claude": { "type": "anthropic", "api_key_env": "ANTHROPIC_API_KEY" }
  },
  "primary": { "provider": "ollama", "model": "qwen3:8b" },
  "capabilities": {
    "edit": { "provider": "claude", "model": "claude-opus-5-5" }
  },
  "embedding": { "provider": "ollama", "model": "nomic-embed-text" }
}
```

### Provider types

| `type` | Covers | `base_url` | Embeddings |
|--------|--------|------------|------------|
| `ollama` | Local Ollama | Optional (defaults to `RIP_OLLAMA_BASE_URL`) | Yes |
| `openai_compatible` | OpenAI (`https://api.openai.com/v1`), OpenRouter, LM Studio (`http://localhost:1234/v1`), vLLM, Gemini's OpenAI-compatible endpoint | Required | Yes |
| `anthropic` | Anthropic Messages API, via the official SDK | Optional | No |

Each provider also accepts `timeout_seconds` (default 120).

### Thinking (Ollama reasoning models)

Reasoning models such as `qwen3` think before they answer, and RIP waits for that. Any Ollama generation model reference (`primary`, a capability or a task) accepts `"think": false` to turn it off, or `true` to force it; leave it out for the model's default. Measured with `qwen3:8b` on a repository question with about 3,000 tokens of context: 55 s with its default thinking, 19 s with `"think": false`. Answers stayed correct but a little less precise, so a sensible setup turns it off for chat and keeps it for edit planning:

```json
"tasks": {
  "chat.answer": { "provider": "ollama", "model": "qwen3:8b", "think": false }
}
```

`think` on a non-Ollama provider or on the embedding model is a configuration error rather than being ignored. The Settings page shows it next to the model.

### Operations

| Name | Level | Used by |
|------|-------|---------|
| `chat` | Capability | Repository chat |
| `edit` | Capability | Code editing |
| `edit.plan` | Task (under `edit`) | Writing search/replace edits from an instruction |
| `chat.answer` | Task (under `chat`) | Answering a chat question |
| `embedding` | Separate setting | Indexing and semantic search |

Only tasks that exist in code are accepted, so the advanced level never offers settings that do nothing.

---

## Privacy

With only Ollama configured, nothing leaves your machine (ADR-0001). Assigning an operation to a hosted provider sends that operation's input to the provider. For chat, that means your question plus the retrieved repository excerpts; for a hosted embedding model, it means every indexed file's content. This is opt-in per operation (ADR-0018).

---

## Changing the embedding model

Vectors from different embedding models cannot be compared, so the index records which model built it. After changing `embedding`:

- semantic search returns a clear "reindex required" error (HTTP 409) naming both models;
- the next explicit reindex rebuilds the index with the new model, clearing the old one only after the first new batch is embedded successfully.

Changing generation models never touches the index.

---

## Key Files

| File | Purpose |
|------|---------|
| `app/llm/config.py` | Configuration schema and validation |
| `app/llm/resolver.py` | Task → capability → primary resolution; effective-model table |
| `app/llm/store.py` | Per-user file, atomic save, `RIP_OLLAMA_*` defaults |
| `app/llm/factory.py` | Builds adapters; reads API keys from the environment |
| `app/llm/providers/` | OpenAI-compatible (`httpx`) and Anthropic (official SDK) adapters |
| `app/dependencies/providers.py` | `apply_model_configuration` saves and rebuilds dependent services |

---

## Known Limitations

- Each capability has one LLM call so far (`chat.answer`, `edit.plan`), so task overrides only matter once a capability has more than one.
- No native Gemini adapter; use Gemini's OpenAI-compatible endpoint.
- The Settings page shows the effective models and lets you pick the primary Ollama model. Editing hosted providers and overrides is done in the file or through the API.
