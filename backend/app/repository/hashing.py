"""SHA-256 hashing utilities."""

from hashlib import sha256
from pathlib import Path


_CHUNK_SIZE = 64 * 1024


def calculate_sha256(
    file_path: Path,
) -> str:
    """Calculate SHA-256 hash for a file."""

    digest = sha256()

    with file_path.open(
        "rb",
    ) as file:
        while chunk := file.read(
            _CHUNK_SIZE,
        ):
            digest.update(
                chunk,
            )

    return digest.hexdigest()