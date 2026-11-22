"""MCP tool definitions for one repository.

Every tool delegates to the same service method the REST API uses, so
path security, limits and error messages are identical across both.
Domain errors become MCP tool errors (``isError``) carrying the
service's message, which tells the agent what to change.

Blocking work runs in a worker thread, so a long reindex never stalls
the protocol loop (pings and cancellation keep working).
"""

from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

import anyio
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from app.editing.exceptions import EditingError
from app.indexing.exceptions import IndexingError
from app.indexing.models import IndexingResult, IndexStatus
from app.indexing.service import IndexingService
from app.workspace.exceptions import WorkspaceError
from app.workspace.models import (
    FileContent,
    SemanticSearchResult,
    SymbolKind,
    SymbolSearchResult,
    TextSearchResult,
    TreeListing,
)
from app.workspace.service import (
    RepositoryWorkspace,
    SymbolMatch,
)

SERVER_NAME = "rip"

SERVER_VERSION = "0.1.0"

INSTRUCTIONS = """\
Repository Intelligence Platform (RIP): read-only tools for one repository.

- All paths are relative to the repository root, using "/" separators.
- Use search_text for exact strings and identifiers, find_symbols for
  where a Python class, function or method is defined, and
  search_semantic for "where is X handled" questions in plain language.
- Results are bounded. When a result says truncated, narrow the query
  (path_glob, a smaller line range) instead of repeating it.
- search_semantic needs an index. Check index_status first; call reindex
  if the project is not indexed or the index is incompatible, and after
  editing files so search sees the new content. Reindexing only embeds
  changed files, so it is cheap to repeat.
- Files excluded by the repository's .gitignore are not listed, searched
  or indexed, but read_file can still open them by path.
- Secret-like files (.env, credentials, private keys) and the .git and
  .local_openclaw directories are never readable.
"""

_READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)

_T = TypeVar("_T")


async def _call(
    function: Callable[[], _T],
) -> _T:
    """Run a blocking service call off the event loop.

    Known domain errors are reported to the client as tool errors with
    their message; anything else is left to the SDK, which reports it
    as an unexpected error without internal details.
    """

    try:
        return await anyio.to_thread.run_sync(
            function,
        )

    except (WorkspaceError, IndexingError, EditingError) as error:
        raise ToolError(
            str(error),
        ) from error


def build_server(
    workspace: RepositoryWorkspace,
    indexing_service: IndexingService,
) -> MCPServer:
    """Create an MCP server exposing tools for one bound workspace."""

    server = MCPServer(
        name=SERVER_NAME,
        title="Repository Intelligence Platform",
        version=SERVER_VERSION,
        instructions=INSTRUCTIONS,
    )

    root: Path = workspace.root

    @server.tool(
        annotations=_READ_ONLY,
    )
    async def read_file(
        path: str,
        start_line: int = 1,
        end_line: int | None = None,
    ) -> FileContent:
        """Read lines of a UTF-8 text file (up to 2,000 lines per call).

        Line numbers are 1-based and inclusive; omit end_line to read to
        the end. When the result is truncated, continue from
        next_start_line.
        """

        return await _call(
            lambda: workspace.read_file(
                path=path,
                start_line=start_line,
                end_line=end_line,
            ),
        )

    @server.tool(
        annotations=_READ_ONLY,
    )
    async def list_tree(
        path: str = "",
        max_depth: int = 2,
        offset: int = 0,
        limit: int = 500,
    ) -> TreeListing:
        """List files and directories below a directory ("" is the root).

        Dependency, cache and protected directories are skipped. Use
        offset and limit to page through large trees.
        """

        return await _call(
            lambda: workspace.list_tree(
                path=path,
                max_depth=max_depth,
                offset=offset,
                limit=limit,
            ),
        )

    @server.tool(
        annotations=_READ_ONLY,
    )
    async def search_text(
        query: str,
        regex: bool = False,
        case_sensitive: bool = False,
        path_glob: str | None = None,
        limit: int = 100,
    ) -> TextSearchResult:
        """Find lines containing text, or matching a regex when regex=true.

        path_glob filters repository-relative paths with fnmatch rules,
        where "*" also matches "/" (e.g. "*.py", "backend/*").
        """

        return await _call(
            lambda: workspace.search_text(
                query=query,
                regex=regex,
                case_sensitive=case_sensitive,
                path_glob=path_glob,
                limit=limit,
            ),
        )

    @server.tool(
        annotations=_READ_ONLY,
    )
    async def find_symbols(
        query: str,
        kind: SymbolKind | None = None,
        match: SymbolMatch = SymbolMatch.EXACT,
        limit: int = 50,
    ) -> SymbolSearchResult:
        """Find where classes, functions and methods are defined (Python).

        Use a dotted query such as "Class.method" for a specific method.
        match is exact (case-sensitive), prefix or contains. The result
        lists the languages searched; other languages need search_text.
        """

        return await _call(
            lambda: workspace.find_symbols(
                query=query,
                kind=kind,
                match=match,
                limit=limit,
            ),
        )

    @server.tool(
        annotations=_READ_ONLY,
    )
    async def search_semantic(
        query: str,
        limit: int = 10,
    ) -> SemanticSearchResult:
        """Find code by meaning, e.g. "where are file edits applied".

        Returns ranked chunks with paths and line ranges; scores only
        rank results within one query. Returns indexed=false when the
        project has no index yet (call reindex).
        """

        return await _call(
            lambda: workspace.search_semantic(
                query=query,
                limit=limit,
            ),
        )

    @server.tool(
        annotations=_READ_ONLY,
    )
    async def index_status() -> IndexStatus:
        """Report whether the repository is indexed, and with which model.

        compatible=false means search_semantic will fail until reindex.
        """

        return await _call(
            lambda: indexing_service.status(
                root,
            ),
        )

    @server.tool(
        annotations=ToolAnnotations(
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        ),
    )
    async def reindex() -> IndexingResult:
        """Bring the semantic search index up to date with the repository.

        Only new or changed files are embedded; unchanged files keep their
        vectors, and deleted or newly .gitignored files are removed. The
        first run (or a run after the embedding model changed) embeds
        everything and can take minutes on a large repository. Only RIP's
        own index is written; repository files are never modified. Fails
        if another process is indexing.
        """

        return await _call(
            lambda: indexing_service.index_repository(
                root,
            ),
        )

    return server
