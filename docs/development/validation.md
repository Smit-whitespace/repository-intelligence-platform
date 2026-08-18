# Validation Workflow

> **Status:** Complete
> **Last Updated:** Sprint 13

---

## Gates

Three validation gates must pass before any sprint can be declared frozen. All gates run from the `backend/` directory.

## Ruff

```bash
uv run ruff check app tests scripts eval
```

Ruff may also be run from the repository root:

```bash
uv run ruff check backend/app backend/tests backend/scripts backend/eval
```

Checks: style, formatting, import sorting, common errors.

## MyPy

```bash
uv run python -m mypy app
```

Checks: type correctness across the entire backend.

> [!NOTE] Pre-existing type errors in scripts are excluded from gate requirements. Only `backend/app/` type correctness is enforced.

## Pytest

```bash
uv run python -m pytest tests -q
```

Runs all backend tests. Pre-existing test failures are documented in sprint freeze reports and do not block progress on unrelated changes.

> [!WARNING] On Windows, running `uv` itself from the repository root can fail with `uv trampoline failed to canonicalize script path`. This is an environment/tooling quirk, not an application failure — run the gates from `backend/`, or invoke the project virtual environment directly (`.venv\Scripts\python.exe -m pytest tests -q`).

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
