# Coding Standards

> **Status:** Complete
> **Last Updated:** Sprint 12.1

---

## Python

### Style

- Follow PEP 8 as enforced by Ruff
- Line length: 88 characters (Ruff default)
- Indentation: 4 spaces
- Blank lines: two between top-level definitions, one between methods

### Typing

- All function signatures must have type annotations
- All return types must be specified
- Prefer `Sequence` over `list` in abstract interfaces
- Use `Path` from `pathlib` for filesystem paths

### Imports

- One import per line
- Group by standard library, third-party, application
- Application imports use absolute paths: `from app.projects.service import ProjectService`
- No wildcard imports

### Docstrings

- Module docstring on first line
- Class docstring describing responsibility
- Method docstring when behavior isn't obvious from name
- Use `"""Triple double quotes"""`

### Naming

- Classes: `PascalCase`
- Functions and methods: `snake_case`
- Private attributes: `self._attribute` (single underscore)
- Constants: `UPPER_CASE`
- Modules: `snake_case.py`

### Error Handling

- Raise specific exception types (from `app/*/exceptions.py`)
- Catch specific exceptions — avoid bare `except:`
- Use `raise ... from error` for exception chaining

## Services

- Constructor injection for all dependencies
- No direct instantiation of dependencies inside services
- Store injected dependencies as `self._dependency_name`
- Methods accept `Path` for filesystem paths

## Validation

All code must pass before merge:

```bash
ruff check backend/
mypy backend/
pytest
```
