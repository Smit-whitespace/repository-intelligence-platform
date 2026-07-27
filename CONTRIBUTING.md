# Contributing to Repository Intelligence Platform (RIP)

Thank you for your interest in contributing.

## Getting Started

1. Read [START-HERE.md](docs/START-HERE.md) for a project overview.
2. Review the [architecture documentation](docs/architecture/README.md) to understand subsystem boundaries.
3. Set up your development environment following the [environment guide](docs/development/environment.md).

## How to Contribute

### Reporting Bugs

Open a [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md). Include steps to reproduce, expected behavior, actual behavior, and your environment.

### Suggesting Features

Open a [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md). Describe the problem, your proposed solution, and any alternatives.

### Submitting Changes

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Run the validation gates: `ruff check backend/ && mypy backend/app/ && pytest`
5. Submit a pull request using the [PR template](.github/PULL_REQUEST_TEMPLATE.md).

## Development Guidelines

- Follow the existing code style. The project uses Ruff for formatting and linting.
- Keep changes focused. Prefer small, atomic commits.
- Add tests for new functionality.
- Preserve subsystem boundaries. Do not move ownership between packages.
- Update documentation when changing behavior.

## Code of Conduct

This project follows a standard open-source code of conduct. Be respectful, constructive, and professional.

## Questions

Open a GitHub Discussion or refer to the [documentation](docs/).
