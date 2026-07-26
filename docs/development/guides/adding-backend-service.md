# Guide: Adding a Backend Service

> **Status:** Complete
> **Last Updated:** Sprint 12.1

---

## Objective

Add a new orchestration or business-logic service to the backend while preserving DI conventions and subsystem boundaries.

## Steps

### 1. Define the Service Class

Create `backend/app/<subsystem>/service.py`:

```python
"""Service description."""

from pathlib import Path


class MyNewService:
    """Service responsibility description."""

    def __init__(
        self,
        dependency: SomeDependency,
    ) -> None:
        """Initialize the service."""

        self._dependency = dependency

    def do_something(
        self,
        root_directory: Path,
    ) -> SomeResult:
        """Description."""
        # Delegation only — no business logic in orchestration services
        return self._dependency.method(root_directory)
```

Rules:
- Constructor injection for all dependencies
- No direct instantiation of dependencies
- Store dependencies as `self._dependency_name`
- Type-annotate all methods

### 2. Add Provider Function

In `backend/app/dependencies/providers.py`:

```python
@lru_cache(maxsize=1)
def get_my_new_service() -> MyNewService:
    """Return the service."""

    return MyNewService(
        dependency=get_existing_provider(),
    )
```

Rules:
- `@lru_cache(maxsize=1)` for singleton scope
- Reuse existing provider functions — never duplicate construction logic
- Name: `get_<service_name>()`

### 3. Wire into API (if needed)

```python
from app.dependencies.providers import get_my_new_service
from app.<subsystem>.service import MyNewService

@router.post("/endpoint")
def my_endpoint(
    service: MyNewService = Depends(get_my_new_service),
) -> ResponseModel:
    """Description."""
    result = service.do_something(...)
    return ResponseModel(...)
```

### 4. Verify

- Ruff check
- MyPy check
- Tests pass

## Related

- [Coding Standards](../standards.md)
- [Adding API Endpoints](adding-api-endpoints.md)
- ADR-0005: Dependency Injection
