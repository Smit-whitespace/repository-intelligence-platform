# Validation Workflow

> **Status:** Complete
> **Last Updated:** Sprint 12.1

---

## Gates

Three validation gates must pass before any sprint can be declared frozen:

## Ruff

```bash
uv run ruff check backend/
```

Checks: style, formatting, import sorting, common errors.

## MyPy

```bash
uv run mypy backend/
```

Checks: type correctness across the entire backend.

> [!NOTE] Pre-existing type errors in scripts are excluded from gate requirements. Only `backend/app/` type correctness is enforced.

## Pytest

```bash
uv run pytest
```

Runs all backend tests. Pre-existing test failures are documented in sprint freeze reports and do not block progress on unrelated changes.

## Pre-commit

If pre-commit is installed:

```bash
uv run pre-commit run --all-files
```

## Interpretation

| Result | Action |
|--------|--------|
| Ruff passes | Proceed |
| Ruff fails | Fix style issues before proceeding |
| MyPy passes | Proceed |
| MyPy fails | Fix type errors before proceeding |
| Pytest all pass | Full confidence |
| Pytest pre-existing failure | Verify it's not related to your change |

## CI (Planned)

CI pipeline will run all three gates on push and pull request.
