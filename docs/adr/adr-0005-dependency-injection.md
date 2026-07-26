# ADR-0005: Dependency Injection Convention

**Status:** Adopted

**Context:**

The backend requires a consistent mechanism for wiring dependencies. FastAPI supports dependency injection via `Depends()`, but service-level dependencies must be constructed somewhere. Without conventions, dependency construction would scatter across API routes and modules.

**Decision:**

All service-level dependency construction is centralized in `app/dependencies/providers.py`. Each provider function is decorated with `@lru_cache(maxsize=1)` for singleton scoping and named `get_<service_name>()`. Services receive their dependencies through constructor injection.

**Consequences:**

Positive:
- Single location for dependency graph
- Singleton semantics prevent accidental duplicate construction
- Services remain testable — dependencies can be injected manually in tests
- No service directly instantiates its own dependencies

Negative:
- Provider file can grow large as new services are added
- `lru_cache` provides application-level singletons, not request-scoped dependencies

**Alternatives Considered:**

- Dependency injection containers (e.g., `dependency-injector`): rejected — unnecessary abstraction for the current scope
- Direct instantiation in routes: rejected — couples routes to construction logic
