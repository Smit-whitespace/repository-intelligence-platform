"""Programming language detection."""

from pathlib import Path


_EXTENSION_LANGUAGE_MAP = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".java": "Java",
    ".kt": "Kotlin",
    ".go": "Go",
    ".rs": "Rust",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c": "C",
    ".h": "C",
    ".hpp": "C++",
    ".cs": "C#",
    ".php": "PHP",
    ".rb": "Ruby",
    ".swift": "Swift",
    ".scala": "Scala",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".xml": "XML",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "Configuration",
    ".md": "Markdown",
    ".txt": "Text",
    ".sh": "Shell",
    ".ps1": "PowerShell",
    ".dockerfile": "Docker",
}


def detect_language(
    path: Path,
) -> str | None:
    """Detect language from file extension."""

    suffix = path.suffix.lower()

    if path.name.lower() == "dockerfile":
        return "Docker"

    return _EXTENSION_LANGUAGE_MAP.get(
        suffix,
    )