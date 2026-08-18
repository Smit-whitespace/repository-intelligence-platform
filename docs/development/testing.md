# Testing Guide

> **Status:** Complete
> **Last Updated:** Sprint 13

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

Run from the `backend/` directory:

```bash
# All tests
uv run python -m pytest tests -q

# Specific file
uv run python -m pytest tests/repository/test_scanner.py

# Specific test
uv run python -m pytest tests/repository/test_scanner.py::test_ignore_patterns

# With coverage
uv run python -m pytest --cov=app
```

> On Windows, invoking `uv` from the repository root can fail with `uv trampoline failed to canonicalize script path` (environment quirk). Running from `backend/` avoids it; alternatively use the virtual environment directly: `.venv\Scripts\python.exe -m pytest tests -q`.

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
