# ADR-0017: Prompt Construction Strategy

**Status:** Adopted

**Context:**

Retrieved repository context must be formatted into a prompt for the LLM. The prompt structure (system instruction, context placement, formatting) significantly affects response quality. The strategy must be consistent but replaceable.

**Decision:**

Prompt construction is owned by `DefaultContextAssembly`. The prompt consists of three message types:

1. **System instruction** — "You are a repository-aware coding assistant..."
2. **Repository context** — formatted as `File: <path>\n\n<content>` blocks
3. **User query** — the original user question

This follows a simple, effective pattern. The `ContextAssembly` interface allows alternative strategies to be implemented without changing chat orchestration.

**Consequences:**

Positive:
- Simple, traceable prompt structure
- Context assembly is independent of chat and retrieval
- Prompt strategy can be swapped via dependency injection

Negative:
- Fixed system instruction — no user customization
- No interleaving of retrieved results with conversation history
- No handling of context window overflow beyond what the LLM provides

**Alternatives Considered:**

- Dynamic prompt optimization via another LLM call: rejected — complexity exceeds current needs
- Multi-turn conversation prompts: deferred — requires conversation history management
- XML/structured formatting: rejected — Markdown-style formatting is simpler and well-understood by LLMs
