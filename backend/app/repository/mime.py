"""MIME type detection."""

from mimetypes import guess_type
from pathlib import Path


_EXTENSION_MIME_MAP = {
    ".py": "text/x-python",
    ".pyi": "text/x-python",
    ".js": "text/javascript",
    ".jsx": "text/javascript",
    ".mjs": "text/javascript",
    ".cjs": "text/javascript",
    ".ts": "text/typescript",
    ".tsx": "text/typescript",
    ".java": "text/x-java",
    ".kt": "text/x-kotlin",
    ".go": "text/x-go",
    ".rs": "text/x-rust",
    ".c": "text/x-c",
    ".cpp": "text/x-c++",
    ".cc": "text/x-c++",
    ".cxx": "text/x-c++",
    ".h": "text/x-c",
    ".hpp": "text/x-c++",
    ".cs": "text/x-csharp",
    ".php": "text/x-php",
    ".rb": "text/x-ruby",
    ".swift": "text/x-swift",
    ".scala": "text/x-scala",
    ".sql": "text/x-sql",
    ".json": "application/json",
    ".yaml": "text/yaml",
    ".yml": "text/yaml",
    ".xml": "text/xml",
    ".toml": "text/toml",
    ".ini": "text/plain",
    ".cfg": "text/plain",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".html": "text/html",
    ".css": "text/css",
    ".scss": "text/x-scss",
    ".sass": "text/x-sass",
    ".sh": "application/x-sh",
    ".ps1": "text/x-powershell",
}


_NAME_MIME_MAP = {
    "dockerfile": "text/x-dockerfile",
}


def detect_mime_type(
    path: Path,
) -> str | None:
    """Detect MIME type.

    Lookup order:

    1. Project-owned extension-to-MIME map.
    2. Python's ``mimetypes.guess_type()`` fallback.
    3. ``None``.
    """

    name_lower = path.name.lower()

    mapped = _NAME_MIME_MAP.get(
        name_lower,
    )

    if mapped is not None:
        return mapped

    suffix = path.suffix.lower()

    mapped = _EXTENSION_MIME_MAP.get(
        suffix,
    )

    if mapped is not None:
        return mapped

    mime_type, _ = guess_type(
        path,
    )

    return mime_type
