"""Repository Workspace service.

A ``RepositoryWorkspace`` is bound to one registered project root when it
is opened. Every tool takes repository-relative paths and resolves them
through one function, ``_resolve``, which is the path-security boundary:
absolute paths, paths that escape the root (including through symlinks)
and paths inside protected directories are rejected there and nowhere
else.

All tools are read-only and bounded: each has an explicit size, count or
time cap, and every result says when it was cut short.
"""

import io
import os
import stat
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import StrEnum
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath, PureWindowsPath

import regex as regex_engine

from app.core.storage.locations import (
    is_protected_path,
    is_registered_project,
    is_valid_path_text,
    project_chroma_directory,
)
from app.indexing.retrieval_models import SearchQuery
from app.indexing.retrieval_service import RetrievalService
from app.repository.ignore import RepositoryIgnoreRules
from app.workspace.exceptions import (
    FileTooLargeError,
    NotATextFileError,
    UnregisteredWorkspaceError,
    WorkspaceError,
    WorkspaceFileNotFoundError,
    WorkspacePathError,
)
from app.workspace.models import (
    EntryKind,
    FileContent,
    SemanticHit,
    SemanticSearchResult,
    Symbol,
    SymbolKind,
    SymbolSearchResult,
    TextMatch,
    TextSearchResult,
    TreeEntry,
    TreeListing,
)
from app.workspace.symbols import (
    PYTHON_SUFFIXES,
    PythonSymbolExtractor,
)

_SECRET_FILE_NAMES = frozenset(
    {
        ".env",
        ".envrc",
        ".netrc",
        "_netrc",
        ".npmrc",
        ".pypirc",
        ".git-credentials",
        ".pgpass",
        "credentials",
        "credentials.json",
    },
)

_SECRET_SUFFIXES = frozenset(
    {
        ".pem",
        ".key",
        ".p12",
        ".pfx",
        ".jks",
        ".keystore",
    },
)

_SSH_PRIVATE_KEY_PREFIXES = (
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
)

_SAFE_TEMPLATE_SUFFIXES = (
    ".example",
    ".sample",
    ".template",
    ".dist",
)


def _is_secret_like(
    path: Path,
) -> bool:
    """Return whether a file probably holds credentials.

    Workspace tools may feed file content to hosted models, so files
    that conventionally hold secrets are never read or searched.
    Templates such as ``.env.example`` stay readable, and so do SSH
    public keys (``id_rsa.pub``).

    Callers must pass the resolved path: a symlink's own name says
    nothing about what it points at.
    """

    name = path.name.casefold()

    if name.endswith(_SAFE_TEMPLATE_SUFFIXES):
        return False

    if name in _SECRET_FILE_NAMES or path.suffix.casefold() in _SECRET_SUFFIXES:
        return True

    if name.startswith(_SSH_PRIVATE_KEY_PREFIXES) and not name.endswith(".pub"):
        return True

    return name.startswith(".env.")


@dataclass(frozen=True)
class _Entry:
    """One visible entry found while walking the repository."""

    path: Path
    """Where the entry appears in the repository."""

    resolved: Path
    """What it points at (the same path unless it is a link)."""

    is_directory: bool

    descend: bool

    size: int


class _WalkLimitReached(Exception):
    """Raised when a walk passes ``RepositoryWorkspace.MAX_WALK_ENTRIES``."""


_REPARSE_POINT = getattr(
    stat,
    "FILE_ATTRIBUTE_REPARSE_POINT",
    0x400,
)


def _is_link_entry(
    entry: os.DirEntry[str],
) -> bool:
    """Return whether an entry redirects somewhere else.

    Covers symlinks, Windows junctions (``is_symlink`` is False for them)
    and any other reparse point.
    """

    if entry.is_symlink() or entry.is_junction():
        return True

    attributes = getattr(
        entry.stat(
            follow_symlinks=False,
        ),
        "st_file_attributes",
        0,
    )

    return bool(attributes & _REPARSE_POINT)


def _split_lines(
    text: str,
) -> list[str]:
    """Split text into lines, keeping line endings.

    Splits only on ``\\n``, ``\\r\\n`` and ``\\r``, so line numbers match
    what editors show. (``str.splitlines`` also splits on form feeds and
    Unicode separators, which would shift every later line number.)
    """

    return list(
        io.StringIO(
            text,
            newline="",
        ),
    )


def _decode(
    data: bytes,
) -> str:
    """Decode UTF-8 text, rejecting binary content."""

    if b"\x00" in data[:8192]:
        raise NotATextFileError(
            "File is binary.",
        )

    try:
        return data.decode(
            "utf-8",
        )

    except UnicodeDecodeError as error:
        raise NotATextFileError(
            "File is not valid UTF-8 text.",
        ) from error


class SymbolMatch(StrEnum):
    """How a symbol query is compared with symbol names."""

    EXACT = "exact"
    """Case-sensitive equality with the name or the qualified name."""

    PREFIX = "prefix"
    """Case-insensitive prefix of the name or qualified name."""

    CONTAINS = "contains"
    """Case-insensitive substring of the name or qualified name."""


class RepositoryWorkspace:
    """Read-only repository tools bound to one registered project."""

    MAX_FILE_BYTES = 1_000_000
    MAX_READ_LINES = 2_000
    MAX_TREE_DEPTH = 20
    MAX_TREE_LIMIT = 2_000
    MAX_QUERY_LENGTH = 500
    MAX_TEXT_RESULTS = 500
    MAX_SCANNED_LINE_LENGTH = 10_000
    MAX_MATCH_TEXT_LENGTH = 300
    TEXT_SEARCH_TIME_BUDGET_SECONDS = 10.0
    SYMBOL_SEARCH_TIME_BUDGET_SECONDS = 10.0
    MAX_WALK_ENTRIES = 100_000
    MAX_SYMBOL_RESULTS = 500
    MAX_SEMANTIC_RESULTS = 50

    def __init__(
        self,
        root: Path,
        retrieval_service: RetrievalService,
        symbol_extractor: PythonSymbolExtractor,
    ) -> None:
        """Bind to an already validated root. Use ``open`` instead."""

        self._root = root

        self._retrieval_service = retrieval_service

        self._symbol_extractor = symbol_extractor

    @classmethod
    def open(
        cls,
        root_directory: str | Path,
        retrieval_service: RetrievalService,
        symbol_extractor: PythonSymbolExtractor,
    ) -> "RepositoryWorkspace":
        """Open a workspace on a registered project root."""

        root = Path(
            root_directory,
        ).resolve()

        if not root.is_dir():
            raise WorkspaceFileNotFoundError(
                "Repository root does not exist or is not a directory.",
            )

        if not is_registered_project(
            root,
        ):
            raise UnregisteredWorkspaceError(
                "Repository root is not a registered RIP project. "
                "Open the project in RIP first.",
            )

        return cls(
            root=root,
            retrieval_service=retrieval_service,
            symbol_extractor=symbol_extractor,
        )

    @property
    def root(
        self,
    ) -> Path:
        """The resolved project root."""

        return self._root

    # --- Tools -----------------------------------------------------------

    def read_file(
        self,
        path: str,
        start_line: int = 1,
        end_line: int | None = None,
    ) -> FileContent:
        """Return a line range of a text file.

        At most ``MAX_READ_LINES`` lines are returned per call; a longer
        range is truncated and ``next_start_line`` says where to resume.
        """

        if start_line < 1:
            raise WorkspaceError(
                "start_line must be at least 1.",
            )

        if end_line is not None and end_line < start_line:
            raise WorkspaceError(
                "end_line must not be less than start_line.",
            )

        target = self._resolve(
            path,
        )

        if not target.is_file():
            raise WorkspaceFileNotFoundError(
                f"File not found: {path}",
            )

        lines = _split_lines(
            self._read_text(
                target,
            ),
        )

        total_lines = len(
            lines,
        )

        requested_end = (
            total_lines
            if end_line is None
            else min(
                end_line,
                total_lines,
            )
        )

        returned_end = min(
            requested_end,
            start_line + self.MAX_READ_LINES - 1,
        )

        truncated = returned_end < requested_end

        return FileContent(
            path=self._relative(
                target,
            ),
            start_line=start_line,
            end_line=returned_end,
            total_lines=total_lines,
            content="".join(
                lines[start_line - 1 : returned_end],
            ),
            truncated=truncated,
            next_start_line=(
                returned_end + 1
                if truncated
                else None
            ),
        )

    def list_tree(
        self,
        path: str = "",
        max_depth: int = 2,
        offset: int = 0,
        limit: int = 500,
    ) -> TreeListing:
        """List files and directories below a directory.

        Ignored directories (``node_modules``, ``.venv``, caches) and
        protected directories are left out. Entries are in depth-first
        order, sorted by name within each directory.
        """

        self._check_range(
            "max_depth",
            max_depth,
            1,
            self.MAX_TREE_DEPTH,
        )

        self._check_range(
            "limit",
            limit,
            1,
            self.MAX_TREE_LIMIT,
        )

        if offset < 0:
            raise WorkspaceError(
                "offset must not be negative.",
            )

        target = self._resolve(
            path,
        )

        if not target.is_dir():
            raise WorkspaceFileNotFoundError(
                f"Directory not found: {path}",
            )

        # Only the requested page is materialized; the rest is counted.
        page: list[TreeEntry] = []

        total_entries = 0

        walk_limit_reached = False

        try:
            for entry in self._iter_entries(
                directory=target,
                max_depth=max_depth,
            ):
                if offset <= total_entries < offset + limit:
                    page.append(
                        TreeEntry(
                            path=self._relative(
                                entry.path,
                            ),
                            kind=(
                                EntryKind.DIRECTORY
                                if entry.is_directory
                                else EntryKind.FILE
                            ),
                            size_bytes=None if entry.is_directory else entry.size,
                        ),
                    )

                total_entries += 1

        except _WalkLimitReached:
            walk_limit_reached = True

        return TreeListing(
            path=self._relative(
                target,
            ),
            entries=page,
            total_entries=total_entries,
            offset=offset,
            truncated=walk_limit_reached or offset + len(page) < total_entries,
        )

    def search_text(
        self,
        query: str,
        regex: bool = False,
        case_sensitive: bool = False,
        path_glob: str | None = None,
        limit: int = 100,
    ) -> TextSearchResult:
        """Find lines containing a literal string or regular expression.

        ``path_glob`` is matched against repository-relative POSIX paths
        with ``fnmatch`` rules, where ``*`` also matches ``/`` (so
        ``*.py`` matches Python files in every directory).

        The whole search, including every single regex match, is bounded
        by ``TEXT_SEARCH_TIME_BUDGET_SECONDS``: matching uses the
        ``regex`` engine's per-call timeout, so a catastrophically
        backtracking pattern (ReDoS) cannot pin a server thread.
        """

        self._check_query(
            query,
        )

        self._check_range(
            "limit",
            limit,
            1,
            self.MAX_TEXT_RESULTS,
        )

        try:
            pattern = regex_engine.compile(
                query if regex else regex_engine.escape(query),
                regex_engine.VERSION0
                | (0 if case_sensitive else regex_engine.IGNORECASE),
            )

        except regex_engine.error as error:
            raise WorkspaceError(
                f"Invalid regular expression: {error}",
            ) from error

        deadline = (
            time.monotonic()
            + self.TEXT_SEARCH_TIME_BUDGET_SECONDS
        )

        time_budget_reason = (
            "Stopped after "
            f"{self.TEXT_SEARCH_TIME_BUDGET_SECONDS:g} seconds; "
            "narrow the search with path_glob or a simpler pattern."
        )

        matches: list[TextMatch] = []

        files_searched = 0

        files = self._iter_text_files(
            path_glob=path_glob,
        )

        while True:
            try:
                file_path, relative_path, text = next(
                    files,
                )

            except StopIteration:
                break

            except _WalkLimitReached:
                return TextSearchResult(
                    matches=matches,
                    files_searched=files_searched,
                    truncated=True,
                    truncation_reason=(
                        f"Stopped after visiting {self.MAX_WALK_ENTRIES} "
                        "entries; narrow the search with path_glob."
                    ),
                )

            files_searched += 1

            for line_number, line in enumerate(
                _split_lines(
                    text,
                ),
                start=1,
            ):
                line = line.rstrip(
                    "\r\n",
                )

                remaining = deadline - time.monotonic()

                try:
                    if remaining <= 0:
                        raise TimeoutError

                    match = pattern.search(
                        line[: self.MAX_SCANNED_LINE_LENGTH],
                        timeout=remaining,
                    )

                except TimeoutError:
                    return TextSearchResult(
                        matches=matches,
                        files_searched=files_searched,
                        truncated=True,
                        truncation_reason=time_budget_reason,
                    )

                if match is None:
                    continue

                matches.append(
                    TextMatch(
                        path=relative_path,
                        line=line_number,
                        column=match.start() + 1,
                        text=self._shorten(
                            line,
                            match.start(),
                        ),
                    ),
                )

                if len(matches) >= limit:
                    return TextSearchResult(
                        matches=matches,
                        files_searched=files_searched,
                        truncated=True,
                        truncation_reason=f"Stopped at the limit of {limit} matches.",
                    )

        return TextSearchResult(
            matches=matches,
            files_searched=files_searched,
            truncated=False,
        )

    def find_symbols(
        self,
        query: str,
        kind: SymbolKind | None = None,
        match: SymbolMatch = SymbolMatch.EXACT,
        limit: int = 50,
    ) -> SymbolSearchResult:
        """Find class, function and method definitions (Python only).

        A query containing ``.`` is compared with qualified names, so
        ``EditingService.apply`` finds that method specifically.
        """

        self._check_query(
            query,
        )

        self._check_range(
            "limit",
            limit,
            1,
            self.MAX_SYMBOL_RESULTS,
        )

        symbols: list[Symbol] = []

        syntax_errors: list[str] = []

        deadline = (
            time.monotonic()
            + self.SYMBOL_SEARCH_TIME_BUDGET_SECONDS
        )

        stop_reason: str | None = None

        try:
            for file_path, relative_path, text in self._iter_text_files(
                suffixes=PYTHON_SUFFIXES,
            ):
                if time.monotonic() > deadline:
                    stop_reason = (
                        "Stopped after "
                        f"{self.SYMBOL_SEARCH_TIME_BUDGET_SECONDS:g} seconds."
                    )
                    break

                file_symbols = self._symbol_extractor.extract(
                    absolute_path=file_path,
                    relative_path=relative_path,
                    source=text,
                )

                if file_symbols is None:
                    syntax_errors.append(
                        relative_path,
                    )
                    continue

                symbols.extend(
                    symbol
                    for symbol in file_symbols
                    if (kind is None or symbol.kind is kind)
                    and self._symbol_matches(
                        symbol,
                        query,
                        match,
                    )
                )

        except _WalkLimitReached:
            stop_reason = (
                f"Stopped after visiting {self.MAX_WALK_ENTRIES} entries."
            )

        if stop_reason is None and len(symbols) > limit:
            stop_reason = f"Stopped at the limit of {limit} definitions."

        return SymbolSearchResult(
            symbols=symbols[:limit],
            truncated=stop_reason is not None,
            truncation_reason=stop_reason,
            languages=[
                "Python",
            ],
            files_with_syntax_errors=syntax_errors[:20],
        )

    def search_semantic(
        self,
        query: str,
        limit: int = 10,
    ) -> SemanticSearchResult:
        """Return indexed chunks ranked by semantic similarity.

        Uses the project's existing index; it does not index anything.
        Raises ``IndexIncompatibleError`` when the index was built with a
        different embedding model than the configured one.
        """

        self._check_query(
            query,
        )

        self._check_range(
            "limit",
            limit,
            1,
            self.MAX_SEMANTIC_RESULTS,
        )

        if not project_chroma_directory(
            self._root,
        ).exists():
            return SemanticSearchResult(
                indexed=False,
                hits=[],
            )

        response = self._retrieval_service.search(
            SearchQuery(
                query=query,
                limit=limit,
                root_directory=str(
                    self._root,
                ),
            ),
        )

        hits = [
            SemanticHit(
                path=result.metadata.relative_path.as_posix(),
                start_line=result.boundary.start_line,
                end_line=result.boundary.end_line,
                chunk_type=result.boundary.chunk_type.value,
                score=result.similarity_score,
                content=result.content,
            )
            for result in response.results
        ]

        hits.sort(
            key=lambda hit: hit.score,
            reverse=True,
        )

        return SemanticSearchResult(
            indexed=True,
            hits=hits,
        )

    # --- Path safety -----------------------------------------------------

    def _resolve(
        self,
        path: str,
    ) -> Path:
        """Resolve a repository-relative path safely.

        The single path-security boundary for every tool.
        """

        raw = path.strip()

        if raw in (
            "",
            ".",
        ):
            return self._root

        if (
            PurePosixPath(raw).is_absolute()
            or PureWindowsPath(raw).is_absolute()
            or PureWindowsPath(raw).drive
        ):
            raise WorkspacePathError(
                "Paths must be relative to the repository root.",
            )

        if not is_valid_path_text(
            raw,
        ):
            raise WorkspacePathError(
                "Path contains characters that are not allowed.",
            )

        candidate = (
            self._root
            / raw.replace(
                "\\",
                "/",
            )
        ).resolve()

        relative = self._relative_path(
            candidate,
        )

        if relative is None:
            raise WorkspacePathError(
                "Path is outside the repository.",
            )

        if is_protected_path(
            relative,
        ):
            raise WorkspacePathError(
                "Path is inside a protected directory.",
            )

        return candidate

    def _relative_path(
        self,
        absolute_path: Path,
    ) -> Path | None:
        """Return the path relative to the root, or None if outside it."""

        try:
            return absolute_path.relative_to(
                self._root,
            )

        except ValueError:
            return None

    def _relative(
        self,
        absolute_path: Path,
    ) -> str:
        """Return a repository-relative POSIX path ('' for the root)."""

        relative = self._relative_path(
            absolute_path,
        )

        if relative is None or str(relative) == ".":
            return ""

        return relative.as_posix()

    def _read_text(
        self,
        target: Path,
    ) -> str:
        """Read a resolved file as text, enforcing the read policy."""

        if _is_secret_like(
            target,
        ):
            raise WorkspacePathError(
                "File looks like it holds secrets; workspace tools do not read it.",
            )

        size = target.stat().st_size

        if size > self.MAX_FILE_BYTES:
            raise FileTooLargeError(
                f"File is {size} bytes; the limit is {self.MAX_FILE_BYTES}.",
            )

        return _decode(
            target.read_bytes(),
        )

    # --- Traversal -------------------------------------------------------

    def _iter_entries(
        self,
        directory: Path,
        max_depth: int | None,
    ) -> Iterator[_Entry]:
        """Yield every visible entry below a directory, depth first.

        Entries are sorted by name within each directory. The walk:

        - never descends into a directory that does not resolve to
          itself. That covers symlinks, Windows junctions (which
          ``is_symlink`` does not report) and other reparse points, so
          traversal cannot leave the root and cannot loop;
        - reports a link only when its target is inside the root and
          outside protected directories, carrying the resolved target so
          callers apply their policies to what will actually be read;
        - is iterative, so a very deep tree cannot overflow the stack;
        - stops with ``_WalkLimitReached`` after ``MAX_WALK_ENTRIES``.
        """

        stack: list[tuple[Iterator[os.DirEntry[str]], int]] = [
            (
                self._sorted_children(
                    directory,
                ),
                1,
            ),
        ]

        visited = 0

        # Fresh per walk, so an edited .gitignore applies to the next call.
        ignore_rules = RepositoryIgnoreRules(
            self._root,
        )

        while stack:
            children, depth = stack[-1]

            entry = next(
                children,
                None,
            )

            if entry is None:
                stack.pop()
                continue

            item = self._classify(
                entry,
                ignore_rules,
            )

            if item is None:
                continue

            visited += 1

            if visited > self.MAX_WALK_ENTRIES:
                raise _WalkLimitReached

            yield item

            if item.descend and (max_depth is None or depth < max_depth):
                stack.append(
                    (
                        self._sorted_children(
                            item.path,
                        ),
                        depth + 1,
                    ),
                )

    @staticmethod
    def _sorted_children(
        directory: Path,
    ) -> Iterator[os.DirEntry[str]]:
        """Return a directory's entries sorted by name (none if unreadable)."""

        try:
            with os.scandir(
                directory,
            ) as iterator:
                return iter(
                    sorted(
                        iterator,
                        key=lambda entry: entry.name,
                    ),
                )

        except OSError:
            return iter(
                (),
            )

    def _classify(
        self,
        entry: os.DirEntry[str],
        ignore_rules: RepositoryIgnoreRules,
    ) -> "_Entry | None":
        """Describe one directory entry, or None if it must stay hidden.

        Hidden: protected paths, names RIP always skips, anything the
        repository's git ignore rules exclude, and links that leave the
        root.
        """

        entry_path = Path(
            entry.path,
        )

        if is_protected_path(
            Path(
                entry.name,
            ),
        ):
            return None

        try:
            if _is_link_entry(
                entry,
            ):
                resolved = entry_path.resolve(
                    strict=True,
                )

                relative = self._relative_path(
                    resolved,
                )

                if relative is None or is_protected_path(
                    relative,
                ):
                    return None

            else:
                resolved = entry_path

            is_directory = resolved.is_dir()

            if ignore_rules.is_ignored(
                entry_path,
                is_directory=is_directory,
            ):
                return None

            # A directory is only walked into when it is not a redirect.
            descend = is_directory and resolved == entry_path

            size = 0 if is_directory else resolved.stat().st_size

        except (OSError, RuntimeError):
            return None

        return _Entry(
            path=entry_path,
            resolved=resolved,
            is_directory=is_directory,
            descend=descend,
            size=size,
        )

    def _iter_text_files(
        self,
        path_glob: str | None = None,
        suffixes: frozenset[str] | None = None,
    ) -> Iterator[tuple[Path, str, str]]:
        """Yield (resolved_path, relative_path, text) for searchable files.

        Skips secret-like, oversized, binary and non-UTF-8 files. Every
        check runs on the resolved target, so a symlink named
        ``notes.txt`` that points at ``.env`` is skipped too.
        """

        for entry in self._iter_entries(
            directory=self._root,
            max_depth=None,
        ):
            if entry.is_directory or entry.size > self.MAX_FILE_BYTES:
                continue

            if suffixes is not None and entry.resolved.suffix.casefold() not in suffixes:
                continue

            relative_path = self._relative(
                entry.path,
            )

            if path_glob and not fnmatchcase(
                relative_path,
                path_glob,
            ):
                continue

            if _is_secret_like(
                entry.path,
            ) or _is_secret_like(
                entry.resolved,
            ):
                continue

            try:
                text = _decode(
                    entry.resolved.read_bytes(),
                )

            except (OSError, NotATextFileError):
                continue

            yield entry.resolved, relative_path, text

    # --- Helpers ---------------------------------------------------------

    def _check_query(
        self,
        query: str,
    ) -> None:
        if not query.strip():
            raise WorkspaceError(
                "query must not be empty.",
            )

        if len(query) > self.MAX_QUERY_LENGTH:
            raise WorkspaceError(
                f"query must be at most {self.MAX_QUERY_LENGTH} characters.",
            )

    @staticmethod
    def _check_range(
        name: str,
        value: int,
        minimum: int,
        maximum: int,
    ) -> None:
        if not minimum <= value <= maximum:
            raise WorkspaceError(
                f"{name} must be between {minimum} and {maximum}.",
            )

    def _shorten(
        self,
        line: str,
        match_start: int,
    ) -> str:
        """Shorten a long line to a window around the match."""

        if len(line) <= self.MAX_MATCH_TEXT_LENGTH:
            return line

        start = max(
            0,
            match_start - self.MAX_MATCH_TEXT_LENGTH // 3,
        )

        window = line[start : start + self.MAX_MATCH_TEXT_LENGTH]

        prefix = "…" if start > 0 else ""

        suffix = "…" if start + self.MAX_MATCH_TEXT_LENGTH < len(line) else ""

        return f"{prefix}{window}{suffix}"

    @staticmethod
    def _symbol_matches(
        symbol: Symbol,
        query: str,
        match: SymbolMatch,
    ) -> bool:
        candidate = (
            symbol.qualified_name
            if "." in query
            else symbol.name
        )

        if match is SymbolMatch.EXACT:
            return candidate == query

        if match is SymbolMatch.PREFIX:
            return candidate.casefold().startswith(
                query.casefold(),
            )

        return query.casefold() in candidate.casefold()


WorkspaceOpener = Callable[[str | Path], RepositoryWorkspace]
"""Opens a workspace on a project root; injected into REST and MCP."""
