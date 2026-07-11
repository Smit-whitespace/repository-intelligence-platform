# Sprint 5 Engineering Plan (Draft)

## 1. Sprint Identity

**Sprint:** Sprint 5
**Status:** Planning → Pending Approval
**Prerequisite:** Sprint 4 Frozen ✅

---

# 2. Sprint Objective

Deliver the **Repository-Aware Chat Foundation** by integrating the completed Repository Intelligence and Retrieval Foundation with a chat orchestration layer, while preserving the frozen architecture and subsystem boundaries.

Sprint 5 is an **integration sprint**, not an infrastructure sprint. Its purpose is to compose the completed Sprint 4 subsystems into the first end-to-end repository-aware interaction workflow.

---

# 3. Scope

## In Scope

* Chat domain models.
* Chat provider abstraction.
* Ollama chat provider implementation.
* Chat orchestration service.
* Context assembly between retrieval and chat.
* Chat API endpoints.
* SSE response streaming.
* Dependency injection wiring.
* Behavioral tests.
* Ruff, MyPy, and Pytest validation.

---

## Out of Scope

The following remain explicitly deferred:

* Multi-agent workflows.
* Autonomous repository editing.
* Memory subsystem.
* Long-term conversation memory.
* Git integration.
* Authentication.
* Cloud synchronization.
* Plugin architecture.
* Tool execution beyond the existing approved capabilities.
* Frontend enhancements beyond backend support.

---

# 4. Sprint Dependencies

Sprint 5 consumes the following completed Sprint 4 subsystems without modification:

* Configuration
* Logging
* Dependency Injection
* Repository Scanner
* Metadata Extraction
* Repository Chunking
* Embedding Provider
* ChromaVectorStore
* Repository Indexer
* Retrieval Service
* Existing REST infrastructure

These are treated as stable implementation dependencies.

---

# 5. Milestones

## Milestone 1 — Chat Domain

Deliverables:

* Chat request models.
* Chat response models.
* Streaming event models.
* Chat provider interface.
* Chat exceptions.

Validation:

* Unit tests.
* Ruff.
* MyPy.

---

## Milestone 2 — Context Assembly

Deliverables:

* Context assembly models.
* Prompt context builder.
* Token budgeting.
* Retrieved chunk formatting.
* Deterministic prompt generation.

Validation:

* Unit tests.
* Prompt determinism tests.

---

## Milestone 3 — Chat Provider

Deliverables:

* Ollama chat provider.
* Streaming implementation.
* Error translation.
* Provider integration tests.

---

## Milestone 4 — Chat Service

Deliverables:

* Retrieval orchestration.
* Context assembly integration.
* Chat provider invocation.
* Streaming orchestration.

Validation:

* Service tests.
* Integration tests.

---

## Milestone 5 — API Integration

Deliverables:

* Chat endpoints.
* SSE responses.
* Dependency wiring.
* Request validation.

Validation:

* API tests.
* Streaming tests.

---

## Milestone 6 — Sprint Validation

Deliverables:

* Ruff PASS.
* MyPy PASS.
* Pytest PASS.
* Sprint retrospective.
* Documentation synchronization.

---

# 6. Ordered Implementation Queue

The implementation order will be:

1. `backend/app/chat/models.py`
2. `backend/app/chat/providers.py`
3. `backend/app/chat/exceptions.py`
4. `backend/app/chat/service.py`
5. Context assembly implementation.
6. Ollama chat provider.
7. Dependency provider updates.
8. Chat API routes.
9. Tests.
10. Validation.

Each implementation target will be completed, reviewed, and validated before moving to the next.

---

# 7. Engineering Constraints

Throughout Sprint 5:

* Preserve frozen architecture.
* Preserve subsystem ownership.
* Preserve accepted ADRs.
* Do not modify Sprint 4 production code unless correcting a verified defect.
* Do not perform speculative refactoring.
* Work one file at a time.
* Validate continuously.

---

# 8. Definition of Done

Sprint 5 is complete when:

* Repository-aware chat operates using semantic retrieval.
* Context assembly produces deterministic prompts.
* Chat provider integrates with Ollama.
* Chat responses are exposed through the backend API.
* SSE streaming functions correctly.
* Behavioral tests pass.
* Ruff passes.
* MyPy passes.
* Pytest passes.
* Sprint documentation is synchronized.

---

# 9. Exit Criteria

Sprint 5 may be frozen when:

* All milestones are complete.
* No verified implementation defects remain.
* All quality gates pass.
* The implementation conforms to the frozen architecture.
* The repository is in a releasable engineering state for the Sprint 5 scope.

---

