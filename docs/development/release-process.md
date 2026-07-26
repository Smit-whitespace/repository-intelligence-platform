# Release Process

> **Status:** Complete
> **Last Updated:** Sprint 12.1

---

## Versioning

The project uses semantic versioning: `MAJOR.MINOR.PATCH`.

Current version: `0.1.0` (pre-1.0 development)

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
- Tag the release: `git tag v0.1.<sprint>`
- Declare sprint frozen

### 5. Post-Freeze

- No further changes to frozen sprint
- Begin planning next sprint
- Historical sprint documents remain immutable

## Technical Debt

- All accepted technical debt is documented in the sprint freeze report
- Debt is tracked per-sprint, not in a global backlog
- Deferred work is explicitly listed — not forgotten
