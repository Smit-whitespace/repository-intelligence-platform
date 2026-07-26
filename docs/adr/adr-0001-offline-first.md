# ADR-0001: Offline-First Architecture

**Status:** Adopted

**Context:**

The project aims to provide a repository-aware AI coding assistant. Many developers work on sensitive codebases where cloud upload is not permitted, or work in environments with intermittent connectivity. Cloud-dependent architectures would exclude these users.

**Decision:**

The system must operate entirely on the local machine without requiring cloud services. All repository understanding, indexing, retrieval, and AI inference execute locally. Cloud synchronization is explicitly excluded from Version 1.

**Consequences:**

Positive:
- Privacy — repository data never leaves the local machine
- Availability — the system works offline
- Latency — no network round-trips for core operations

Negative:
- Model quality is limited by local LLM capabilities
- Storage and compute are constrained to local hardware
- No built-in backup or sync

**Alternatives Considered:**

- Hybrid local+cloud: rejected as it would increase complexity and exclude air-gapped users
- Cloud-only: rejected — contradicts core privacy requirement
