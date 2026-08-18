"""Repository file type detection."""

from pathlib import Path


_TEXT_EXTENSIONS = {
    ".py",
    ".pyi",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".kt",
    ".go",
    ".rs",
    ".c",
    ".cpp",
    ".cc",
    ".cxx",
    ".h",
    ".hpp",
    ".cs",
    ".php",
    ".rb",
    ".swift",
    ".scala",
    ".sql",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".toml",
    ".ini",
    ".cfg",
    ".md",
    ".txt",
    ".html",
    ".css",
    ".scss",
    ".sass",
    ".sh",
    ".ps1",
    ".mjs",
    ".cjs",
}


def is_text_file(
    path: Path,
) -> bool:
    """Return whether a file is considered text."""

    if path.name.lower() == "dockerfile":
        return True

    return path.suffix.lower() in _TEXT_EXTENSIONS