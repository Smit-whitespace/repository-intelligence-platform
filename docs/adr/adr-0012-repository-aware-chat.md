# ADR-0012: Repository-Aware Chat Pipeline

**Status:** Adopted

**Context:**

Chat responses should be informed by the repository context. The simplest approach is to include relevant code snippets in the prompt. The pipeline must retrieve context without coupling chat to indexing or vector search internals.

**Decision:**

The chat pipeline is: `User Query → RetrievalService.search() → ContextAssembly.assemble() → ChatProvider.generate()`. ChatService orchestrates these steps. It never performs indexing or vector store writes.

**Consequences:**

Positive:
- Chat is decoupled from indexing and vector store internals
- Each pipeline stage is independently testable
- Pipeline is simple enough to trace end-to-end

Negative:
- Chat quality depends entirely on retrieval quality
- No conversation history management beyond single request-response
- No streaming in the current API

**Alternatives Considered:**

- Embed search results directly in ChatService: rejected — would couple chat to search internals
- Delegate everything to ContextAssembly: rejected — would blur orchestration with prompt building
