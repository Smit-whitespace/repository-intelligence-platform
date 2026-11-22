# ADR-0018: Opt-In Hosted Model Providers

**Status:** Adopted (amends ADR-0001)

**Context:**

ADR-0001 requires all AI inference to run locally. That kept repository code on the user's machine, but it also limits answer quality to what local hardware can run, and it makes RIP unusable as a shared intelligence layer for users who already work with hosted models (OpenAI, Anthropic, Gemini). V1 needs configurable models: a primary model, per-capability and per-task overrides, and a separate embedding model, any of which may be local or hosted.

Sending repository code to a hosted API is a real privacy decision, so it cannot happen by default or by accident.

**Decision:**

- Support hosted providers alongside Ollama, behind one configuration (`app/llm/`): Ollama, any OpenAI-compatible API, and Anthropic.
- **Local stays the default.** With no saved configuration, RIP uses Ollama from the existing `LOC_OLLAMA_*` settings, so ADR-0001's behavior is unchanged unless the user configures a hosted provider.
- **Hosted use is explicit and per operation.** A hosted model only runs for the operations the configuration assigns to it, and the Settings page shows the effective model and its source for every operation.
- **Credentials stay out of files.** The configuration stores only the name of the environment variable holding a key. Keys are read at call time and never written to disk or returned by the API.
- **Configuration is per user, not per project** (`~/.local_openclaw/models.json`), so it can never be committed with a repository.
- **No silent fallback.** If the chosen model or provider fails, RIP reports the error. It never retries on another model or provider, and Anthropic's server-side refusal fallback is deliberately not enabled.
- **Embeddings are configured separately** and never follow the primary model. Changing them never reindexes on its own; the index compatibility check (ADR-0016 follow-up) reports the mismatch until the user reindexes.

**Consequences:**

Positive:
- Users choose quality, cost and privacy per operation instead of all-or-nothing.
- Air-gapped users are unaffected; nothing hosted is contacted unless configured.

Negative:
- With a hosted provider configured, repository excerpts (retrieved chunks and questions) are sent to that provider. This is documented in the model configuration guide.
- One more dependency (the official `anthropic` SDK) and more code paths to test. The adapters are tested against mocked transports, so tests never need keys or network access.

**Alternatives Considered:**

- Keep local-only: rejected; it blocks the V1 goal of serving users and agents who rely on hosted models.
- Per-project configuration: rejected; credentials and model choices are personal, and files inside a repository risk being committed.
- An abstraction library (for example LiteLLM): rejected; a large dependency for three adapters, and its own fallback and retry behavior would conflict with "no silent fallback".
