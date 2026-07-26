# ADR-0016: Embedding Model Selection

**Status:** Adopted

**Context:**

Semantic indexing and retrieval require an embedding model to convert text into vector representations. The model choice affects retrieval quality, resource usage, and latency. Several local embedding models are available through Ollama.

**Decision:**

`nomic-embed-text` is the default embedding model, served through `OllamaEmbeddingProvider`. The model is configurable through settings. All embedding goes through the `EmbeddingProvider` interface, so the model can be changed without affecting other subsystems.

**Consequences:**

Positive:
- Local execution — no external API calls
- `EmbeddingProvider` interface isolates the rest of the system from model changes
- Model can be swapped via configuration

Negative:
- Model quality is limited by local inference capabilities
- `nomic-embed-text` may not match cloud embedding quality
- Embedding dimension is fixed per model — changing models may require re-indexing

**Alternatives Considered:**

- Cloud embedding APIs (OpenAI, etc.): rejected — violates offline-first
- Sentence transformers (local): viable alternative but requires additional Python dependencies
- Ollama-native models: chosen for consistency with chat provider
