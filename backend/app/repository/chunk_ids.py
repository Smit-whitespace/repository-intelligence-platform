"""Repository chunk identifier generation."""

from hashlib import sha256

from app.repository.models import RepositoryEntry


def generate_chunk_id(
    entry: RepositoryEntry,
    start_line: int,
    end_line: int,
) -> str:
    """Generate a deterministic chunk identifier."""

    if entry.sha256 is None:
        raise ValueError(
            "Repository entry must contain a SHA-256 hash.",
        )

    identifier = (
        f"{entry.relative_path.as_posix()}:"
        f"{entry.sha256}:"
        f"{start_line}:"
        f"{end_line}"
    )

    return sha256(
        identifier.encode(
            "utf-8",
        )
    ).hexdigest()