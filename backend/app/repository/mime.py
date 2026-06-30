"""MIME type detection."""

from mimetypes import guess_type
from pathlib import Path


def detect_mime_type(
    path: Path,
) -> str | None:
    """Detect MIME type."""

    mime_type, _ = guess_type(
        path,
    )

    return mime_type