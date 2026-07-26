# Guide: Adding API Endpoints

> **Status:** Complete
> **Last Updated:** Sprint 12.1

---

## Objective

Add a new REST endpoint while preserving API conventions and architectural boundaries.

## Steps

### 1. Define Request/Response Schemas

In `backend/app/<subsystem>/schemas.py` (or inline if simple):

```python
from pydantic import BaseModel


class MyRequest(BaseModel):
    """Request description."""

    value: str


class MyResponse(BaseModel):
    """Response description."""

    result: str
```

### 2. Create or Extend a Router

In `backend/app/api/routes/<subsystem>.py`:

```python
from fastapi import APIRouter, Depends

router = APIRouter(
    prefix="/<subsystem>",
    tags=["Subsystem"],
)
```

### 3. Add Endpoint

```python
@router.post(
    "/action",
    response_model=MyResponse,
    operation_id="myAction",
    summary="Short summary",
    description="Detailed description.",
    response_description="Response description.",
)
def my_action(
    request: MyRequest,
    service: MyService = Depends(get_my_service),
) -> MyResponse:
    """Docstring."""

    result = service.do_something(request.value)

    return MyResponse(result=result)
```

Rules:
- Endpoints delegate to services — no business logic in route functions
- Use `Depends()` for dependency injection
- Define `operation_id`, `summary`, `description` for Swagger documentation
- Import services from `app.dependencies.providers`

### 4. Register the Router

In `backend/app/api/router.py`:

```python
from app.api.routes.<subsystem> import router as <subsystem>_router

api_router.include_router(<subsystem>_router)
```

### 5. Verify

- Swagger UI at `/docs` shows the new endpoint
- Ruff, MyPy, Pytest pass

## Related

- [Adding a Backend Service](adding-backend-service.md)
- [API Reference](../../api/README.md)
