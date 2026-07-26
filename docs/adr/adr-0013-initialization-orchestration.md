# ADR-0013: Initialization Orchestration

**Status:** Adopted (Sprint 12.1)

**Context:**

Project initialization requires multiple steps (metadata persistence, repository scanning, indexing). These steps must execute in order. The orchestration logic must not be in any of the existing services, as that would violate single-responsibility.

**Decision:**

`ProjectInitializationService` is a pure orchestration service. It contains no business logic, no validation, no error handling beyond what existing services provide, and no retries. It simply calls three existing services in sequence and returns the `Project`.

**Consequences:**

Positive:
- Each existing service remains focused on its single responsibility
- Orchestration is explicit, visible, and modifiable
- The service is trivially testable with mocks

Negative:
- No retry or recovery if any stage fails (deferred)
- No logging within the orchestrator (deferred)
- Synchronous — the caller waits for all three stages

**Alternatives Considered:**

- Embed orchestration in ProjectService: rejected — would move orchestration into business logic
- Embed orchestration in the API endpoint: rejected — routes should not contain orchestration logic
- Event-driven pipeline: rejected — complexity exceeds current requirements; can be added later
