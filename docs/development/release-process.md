# Release Process

> **Status:** Complete
> **Last Updated:** Sprint 12.1

---

## Versioning

The project uses semantic versioning: `MAJOR.MINOR.PATCH`.

Current version: `1.2.0`.

The version lives in three files that must agree; a test
(`backend/tests/test_version.py`) fails if they drift:

- `backend/app/core/version.py`: the API, the OpenAPI document and the MCP
  server read `APPLICATION_VERSION` here.
- `pyproject.toml`: the Python package version.
- `frontend/package.json` (and the root entries of `package-lock.json`): the
  sidebar shows it, injected at build time by `vite.config.ts`.

## Continuous Integration

`.github/workflows/ci.yml` runs on every pull request and on every push to
`main`:

- **Backend:** Ruff, MyPy (`app` and `eval`) and Pytest, on Linux.
- **Frontend:** type check, ESLint and Vitest.

A pull request should merge only when both jobs pass. To make that a rule
rather than a habit, require the `Backend` and `Frontend` checks in the
repository's branch protection settings for `main`.

## Cutting a Release

1. Bump the version in the three files above, in a pull request.
2. Merge it once CI passes.
3. Tag the merge commit on `main` with an annotated tag and push it:

   ```powershell
   git switch main
   git pull
   git tag -a v1.2.0 -m "v1.2.0"
   git push origin v1.2.0
   ```

Tags before `v1.0.0` (up to `v0.13.0`) mark the sprint freezes below.

## Release Checklist

Each sprint follows these steps:

### 1. Implementation

- Complete all approved slices for the sprint
- Each slice is independently verified (Ruff + MyPy)

### 2. Validation

- Run all three gates: Ruff, MyPy, Pytest
- Document any pre-existing failures
- Fix all new failures introduced by the sprint

### 3. Documentation

- Update sprint freeze document
- Update architecture documentation if subsystems changed
- Update ADRs if new decisions were made
- Record technical debt and deferred work

### 4. Freeze

- Produce Sprint Freeze Report
- Commit all changes
- Tag the release (see Cutting a Release)
- Declare sprint frozen

### 5. Post-Freeze

- No further changes to frozen sprint
- Begin planning next sprint
- Historical sprint documents remain immutable

## Technical Debt

- All accepted technical debt is documented in the sprint freeze report
- Debt is tracked per-sprint, not in a global backlog
- Deferred work is explicitly listed — not forgotten
