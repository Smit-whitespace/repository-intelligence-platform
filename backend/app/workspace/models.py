"""Repository Workspace result models.

Every list result is bounded and says whether it was truncated, so a
client always knows when it is seeing a partial answer.
"""

from enum import StrEnum

from pydantic import BaseModel
from pydantic import Field


class FileContent(BaseModel):
    """A line range of one text file."""

    path: str = Field(
        description="Repository-relative POSIX path.",
    )

    start_line: int = Field(
        description="First returned line (1-based).",
    )

    end_line: int = Field(
        description="Last returned line (1-based, inclusive). Less than "
        "start_line when the range is empty.",
    )

    total_lines: int

    content: str = Field(
        description="The returned lines, with their original line endings.",
    )

    truncated: bool = Field(
        description="True when the line cap cut the requested range short.",
    )

    next_start_line: int | None = Field(
        default=None,
        description="Where to continue reading when truncated.",
    )


class EntryKind(StrEnum):
    """Kind of tree entry."""

    FILE = "file"

    DIRECTORY = "directory"


class TreeEntry(BaseModel):
    """One file or directory in a tree listing."""

    path: str

    kind: EntryKind

    size_bytes: int | None = None


class TreeListing(BaseModel):
    """A page of a directory tree."""

    path: str = Field(
        description="The listed directory (empty string for the root).",
    )

    entries: list[TreeEntry]

    total_entries: int = Field(
        description="Entries within max_depth before pagination.",
    )

    offset: int

    truncated: bool


class TextMatch(BaseModel):
    """One matching line."""

    path: str

    line: int

    column: int = Field(
        description="1-based column of the first match on the line.",
    )

    text: str = Field(
        description="The matching line, shortened if very long.",
    )


class TextSearchResult(BaseModel):
    """Text search matches."""

    matches: list[TextMatch]

    files_searched: int

    truncated: bool

    truncation_reason: str | None = None


class SymbolKind(StrEnum):
    """Kind of code symbol."""

    CLASS = "class"

    FUNCTION = "function"

    METHOD = "method"


class Symbol(BaseModel):
    """A symbol definition."""

    name: str

    qualified_name: str = Field(
        description="Dotted name within the file, e.g. ``Class.method``.",
    )

    kind: SymbolKind

    is_async: bool = False

    path: str

    start_line: int = Field(
        description="First line, including decorators.",
    )

    end_line: int


class SymbolSearchResult(BaseModel):
    """Symbol definitions matching a query."""

    symbols: list[Symbol]

    truncated: bool

    truncation_reason: str | None = None

    languages: list[str] = Field(
        description="Languages whose definitions are searched.",
    )

    files_with_syntax_errors: list[str] = Field(
        default_factory=list,
        description="Files skipped because they could not be parsed.",
    )


class SemanticHit(BaseModel):
    """One semantically relevant chunk."""

    path: str

    start_line: int

    end_line: int

    chunk_type: str

    score: float = Field(
        description=(
            "Relative ranking score within this query only; test files are "
            "weighted lower so the code they test ranks first."
        ),
    )

    content: str


class SemanticSearchResult(BaseModel):
    """Semantic search results."""

    indexed: bool = Field(
        description="False when the project has never been indexed; "
        "results are then always empty.",
    )

    hits: list[SemanticHit]
