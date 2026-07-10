# Sprint 5 — Repository-Aware Chat Foundation

## Sprint Objective

Deliver the first complete repository-aware chat workflow by integrating the completed Repository Intelligence and Retrieval Foundation with the chat layer. Sprint 5 will focus on orchestration rather than introducing new infrastructure. Existing repository scanning, indexing, embedding, vector storage, and retrieval components will be consumed through their established interfaces.

---

# Sprint Deliverables

By the end of Sprint 5, the following capabilities should exist:

### 1. Chat orchestration

Implement the service responsible for coordinating:

* query embedding,
* semantic retrieval,
* context assembly,
* LLM request construction,
* response generation.

This becomes the primary consumer of the completed Retrieval Foundation.

---

### 2. Context Assembly

Implement the approved Context Assembly subsystem.

Responsibilities include:

* selecting retrieved repository chunks,
* ordering retrieved context,
* token budgeting,
* prompt construction,
* preserving deterministic prompt generation.

The previously accepted architectural decision that Context Assembly is a distinct subsystem between Retrieval and Chat should now be realized.

---

### 3. Ollama Chat Integration

Extend the existing Ollama provider beyond embeddings to support chat completion while preserving provider abstraction boundaries.

Responsibilities:

* request serialization,
* streaming support,
* error handling,
* model configuration reuse.

---

### 4. Chat API

Implement the frozen API endpoints for repository-aware chat.

This includes:

* request validation,
* streaming responses,
* dependency injection,
* integration with the Chat Service.

The public API contracts defined during architecture remain unchanged.

---

### 5. Streaming

Complete Server-Sent Events (SSE) streaming support through the API layer using the existing response contract.

---

# Ordered Implementation Queue

The implementation order should minimize integration risk.

### Milestone 1

Context Assembly

Deliverables:

* context models,
* token budgeting,
* context selection,
* prompt builder.

---

### Milestone 2

Chat Provider

Deliverables:

* Ollama chat support,
* provider interface,
* streaming adapter.

---

### Milestone 3

Chat Service

Deliverables:

* orchestration,
* retrieval integration,
* prompt execution,
* response mapping.

---

### Milestone 4

API Integration

Deliverables:

* chat endpoints,
* SSE,
* dependency wiring.

---

### Milestone 5

Validation

Deliverables:

* unit tests,
* integration tests,
* Ruff,
* MyPy,
* Pytest.

---

# Definition of Done

Sprint 5 is complete when:

* repository-aware chat operates using semantic retrieval,
* Context Assembly produces deterministic prompts,
* chat responses stream through SSE,
* provider abstractions remain respected,
* no subsystem ownership violations exist,
* Ruff passes,
* MyPy passes,
* Pytest passes,
* documentation reflects the completed implementation.

---

# Engineering Constraints

The following remain unchanged:

* No architectural redesign.
* No modification of accepted ADRs.
* No speculative abstractions.
* No production refactoring without verified need.
* One implementation target at a time.
* Public interfaces remain stable unless explicitly approved.

---
