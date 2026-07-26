# Testing Guide

> **Status:** Complete
> **Last Updated:** Sprint 12.1

---

## Test Structure

Tests mirror the backend source structure:

```
backend/tests/
    api/            # API endpoint tests
    indexing/       # Indexing service tests
    projects/       # Project service tests
    repository/     # Repository scanner, chunker, service tests
    editing/        # Editing service tests
    chat/           # Chat service tests
    context_assembly/
```

## Running Tests

```bash
# All tests
uv run pytest

# Specific file
uv run pytest backend/tests/repository/test_scanner.py

# Specific test
uv run pytest backend/tests/repository/test_scanner.py::test_ignore_patterns

# With coverage
uv run pytest --cov=app
```

## Test Conventions

- Tests use `pytest` (not `unittest`)
- Fixtures for shared setup (e.g., temp directories, mock services)
- Test files named `test_<module>.py`
- Test functions named `test_<behavior>`
- One assertion concept per test
- Mock external dependencies (Ollama, ChromaDB, filesystem) when testing service logic

## Testing Patterns

### Service Tests

```python
def test_service_method():
    mock_dep = Mock()
    service = MyService(dependency=mock_dep)
    result = service.method()
    assert result == expected
```

### API Tests

Use FastAPI `TestClient`:

```python
client = TestClient(app)

def test_endpoint():
    response = client.post("/endpoint", json={...})
    assert response.status_code == 200
```

### What to Test

- Service orchestration (mocked dependencies)
- API request/response contracts
- Error cases (invalid input, missing resources)
- Edge cases (empty repositories, non-text files)

### What Not to Test

- Implementation internals (test public interfaces)
- Third-party library behavior
- Configuration loading (test settings model separately)
