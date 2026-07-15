"""Repository API schemas."""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class RepositoryEntryResponse(BaseModel):
    """Repository entry response."""

    name: str = Field(
        description="File or directory name.",
        examples=[
            "README.md",
        ],
    )

    relative_path: Path = Field(
        description="Repository-relative path.",
        examples=[
            "README.md",
        ],
    )

    is_directory: bool = Field(
        description="Whether the entry is a directory.",
        examples=[
            False,
        ],
    )

    size_bytes: int | None = Field(
        description="File size in bytes, or null for directories.",
        examples=[
            1024,
        ],
    )

    modified_at: datetime | None = Field(
        description="Last modification timestamp when available.",
        examples=[
            "2026-07-15T10:30:00Z",
        ],
    )

    language: str | None = Field(
        description="Detected programming or markup language.",
        examples=[
            "Markdown",
        ],
    )

    sha256: str | None = Field(
        description="SHA-256 digest for text files when available.",
        examples=[
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
        ],
    )

    is_text_file: bool | None = Field(
        description="Whether the file is classified as text.",
        examples=[
            True,
        ],
    )

    mime_type: str | None = Field(
        description="Detected MIME type when available.",
        examples=[
            "text/markdown",
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "README.md",
                "relative_path": "README.md",
                "is_directory": False,
                "size_bytes": 1024,
                "modified_at": "2026-07-15T10:30:00Z",
                "language": "Markdown",
                "sha256": (
                    "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
                ),
                "is_text_file": True,
                "mime_type": "text/markdown",
            },
        },
    )


class RepositorySummaryResponse(BaseModel):
    """Repository summary response."""

    files: int = Field(
        description="Number of files in the repository scan.",
        examples=[
            42,
        ],
    )

    directories: int = Field(
        description="Number of directories in the repository scan.",
        examples=[
            7,
        ],
    )

    total_size_bytes: int = Field(
        description="Total byte size of scanned files.",
        examples=[
            4096,
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "files": 42,
                "directories": 7,
                "total_size_bytes": 4096,
            },
        },
    )


class RepositoryIndexResponse(BaseModel):
    """Repository index response."""

    summary: RepositorySummaryResponse = Field(
        description="Aggregate repository scan summary.",
    )

    entries: list[RepositoryEntryResponse] = Field(
        description="Scanned repository entries.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "summary": {
                    "files": 42,
                    "directories": 7,
                    "total_size_bytes": 4096,
                },
                "entries": [
                    {
                        "name": "README.md",
                        "relative_path": "README.md",
                        "is_directory": False,
                        "size_bytes": 1024,
                        "modified_at": "2026-07-15T10:30:00Z",
                        "language": "Markdown",
                        "sha256": (
                            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
                        ),
                        "is_text_file": True,
                        "mime_type": "text/markdown",
                    },
                ],
            },
        },
    )
