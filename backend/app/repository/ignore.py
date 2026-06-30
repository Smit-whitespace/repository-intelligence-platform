"""Repository ignore rules."""

from pathlib import Path


_INTERNAL_EXCLUDED_NAMES = {
    ".git",
    ".local_openclaw",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    "node_modules",
}


def should_ignore(
    path: Path,
) -> bool:
    """Return whether a path should be ignored."""

    return path.name in _INTERNAL_EXCLUDED_NAMES