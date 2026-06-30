"""Repository ignore rules."""

from pathlib import Path


_INTERNAL_EXCLUDED_DIRECTORIES = {
    ".local_openclaw",
}


def should_ignore(
    path: Path,
) -> bool:
    """Return whether a path should be ignored."""

    return path.name in _INTERNAL_EXCLUDED_DIRECTORIES