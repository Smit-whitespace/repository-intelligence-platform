# ADR-0007: Context Assembly

**Status:** Adopted

**Context:**

Retrieved search results must be assembled into a prompt for the LLM. The prompt structure (system instructions, context formatting, query placement) may evolve independently of retrieval and chat logic. Hard-coding prompt construction in ChatService would make it difficult to change.

**Decision:**

Context assembly is a separate abstraction (`ContextAssembly` interface). The default implementation (`DefaultContextAssembly`) builds a `ChatPrompt` with a system instruction, retrieved context, and user query. ChatService depends on `ContextAssembly` but does not construct prompts directly.

**Consequences:**

Positive:
- Prompt strategy can change without modifying chat orchestration
- Multiple context assembly implementations can coexist
- Testable independently of chat and retrieval

Negative:
- Additional abstraction layer
- Default prompt is fixed — no user customization exposed

**Alternatives Considered:**

- Prompt construction in ChatService: rejected — couples chat to prompt format
- Prompt construction in frontend: rejected — would expose prompt internals to client
