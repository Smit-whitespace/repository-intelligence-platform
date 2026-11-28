"""MCP tool definitions for one repository.

Every tool delegates to the same service method the REST API uses, so
path security, limits and error messages are identical across both.
Domain errors become MCP tool errors (``isError``) carrying the
service's message, which tells the agent what to change.

Blocking work runs in a worker thread, so a long reindex never stalls
the protocol loop (pings and cancellation keep working).
"""

from collections.abc import Awaitable, Callable
from enum import StrEnum
from pathlib import Path
from typing import Any, TypeVar

import anyio
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from app.core.version import APPLICATION_VERSION
from app.editing.exceptions import EditingError
from app.editing.proposal_service import ProposalService
from app.editing.proposals import (
    EditOperation,
    ProposalSource,
)
from app.indexing.exceptions import IndexingError
from app.indexing.freshness import IndexFreshness
from app.indexing.models import FreshnessResult, IndexingResult, IndexStatus
from app.indexing.service import IndexingService
from app.mcp_server.models import (
    ProposalDetail,
    ProposalList,
    ProposalSummary,
)
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

SERVER_VERSION = APPLICATION_VERSION

INSTRUCTIONS = """\
Repository Intelligence Platform (RIP): read-only tools for one repository.

- All paths are relative to the repository root, using "/" separators.
- Use search_text for exact strings and identifiers, find_symbols for
  where a Python class, function or method is defined, and
  search_semantic for "where is X handled" questions in plain language.
- Results are bounded. When a result says truncated, narrow the query
  (path_glob, a smaller line range) instead of repeating it.
- search_semantic needs an index. Check index_status first; call reindex
  if the project is not indexed or the index is incompatible. Once
  indexed, search_semantic updates the files changed since indexing
  before it searches (within a time limit; its result says when files
  were still pending), so there is no need to reindex after editing
  files. Use reindex to rebuild the whole index, for example after
  changing the embedding model.
- Files excluded by the repository's .gitignore are not listed, searched
  or indexed, but read_file can still open them by path.
- Secret-like files (.env, credentials, private keys) and the .git and
  .rip directories are never readable.
"""

class IndexStatusReport(IndexStatus):
    """``IndexStatus`` plus whether files changed since indexing."""

    freshness: FreshnessResult | None = None


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


class EditingMode(StrEnum):
    """What an MCP client may do with edits (``--editing``)."""

    OFF = "off"
    """No editing tools."""

    PROPOSE = "propose"
    """Propose and inspect edits; a person applies them in the RIP app."""

    APPLY = "apply"
    """Also apply and roll back proposals. Applying runs the project's
    validation commands, which execute repository code."""


_EDITING_INSTRUCTIONS = {
    EditingMode.OFF: "",
    EditingMode.PROPOSE: """\
- To change files, call propose_edit with search/replace operations. Each
  'search' must be copied exactly from the current file (read_file it
  first) and occur exactly once. Nothing is written: tell the user the
  proposal_id, and that they review and apply it on the RIP app's
  Editing page with this repository open as the project: {root}
""",
    EditingMode.APPLY: """\
- To change files, call propose_edit with search/replace operations. Each
  'search' must be copied exactly from the current file (read_file it
  first) and occur exactly once. Then apply_proposal writes it and runs
  the project's validation commands; rollback_proposal undoes it. There
  is no need to reindex after applying: search_semantic updates the
  changed files itself.
""",
}


def build_server(
    workspace: RepositoryWorkspace,
    indexing_service: IndexingService,
    proposal_service: ProposalService | None = None,
    editing_mode: EditingMode = EditingMode.OFF,
    before_call: Callable[[], None] | None = None,
    index_freshness: IndexFreshness | None = None,
) -> MCPServer:
    """Create an MCP server exposing tools for one bound workspace.

    Editing tools are registered only when a proposal service is given
    and ``editing_mode`` allows them; a tool that is not registered
    cannot be called at all.
    """

    if proposal_service is None:
        editing_mode = EditingMode.OFF

    server = MCPServer(
        name=SERVER_NAME,
        title="Repository Intelligence Platform",
        version=SERVER_VERSION,
        instructions=INSTRUCTIONS
        + _EDITING_INSTRUCTIONS[editing_mode].format(
            root=workspace.root,
        ),
    )

    root: Path = workspace.root

    async def call(
        function: Callable[[], _T],
    ) -> _T:
        # Refresh state other processes may have changed (the model
        # configuration) before each tool runs.
        if before_call is not None:
            before_call()

        return await _call(
            function,
        )

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

        return await call(
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

        return await call(
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

        return await call(
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

        return await call(
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

        def search() -> SemanticSearchResult:
            # Update changed files first; the workspace never indexes.
            index = (
                index_freshness.refresh(
                    root,
                )
                if index_freshness is not None
                else None
            )

            return workspace.search_semantic(
                query=query,
                limit=limit,
            ).model_copy(
                update={
                    "index": index,
                },
            )

        return await call(
            search,
        )

    @server.tool(
        annotations=_READ_ONLY,
    )
    async def index_status() -> IndexStatusReport:
        """Report whether the repository is indexed, and with which model.

        compatible=false means search_semantic will fail until reindex.
        freshness says whether files changed since indexing; it is only
        read here, never updated.
        """

        def report() -> IndexStatusReport:
            return IndexStatusReport(
                **indexing_service.status(
                    root,
                ).model_dump(),
                freshness=(
                    index_freshness.status(
                        root,
                    )
                    if index_freshness is not None
                    else None
                ),
            )

        return await call(
            report,
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
        if another index update is running for this project.
        """

        result = await call(
            lambda: indexing_service.index_repository(
                root,
            ),
        )

        # Nothing could be indexed (typically: the embedding provider is
        # down). Report it as a failure, so the agent does not assume the
        # index is current.
        if result.failed_files and not result.indexed_files:
            details = (
                result.diagnostics.failed_files_details
                if result.diagnostics
                else []
            )

            reason = details[0].message if details else "unknown error"

            raise ToolError(
                f"Reindex failed for all {result.failed_files} files: "
                f"{reason} The existing index was kept.",
            )

        return result

    if editing_mode is not EditingMode.OFF:
        assert proposal_service is not None

        _add_editing_tools(
            server=server,
            root=root,
            proposal_service=proposal_service,
            allow_apply=editing_mode is EditingMode.APPLY,
            call=call,
        )

    return server


def _add_editing_tools(
    server: MCPServer,
    root: Path,
    proposal_service: ProposalService,
    allow_apply: bool,
    call: Callable[[Callable[[], Any]], Awaitable[Any]],
) -> None:
    """Register proposal tools; apply and rollback only when allowed."""

    @server.tool(
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=False,
            open_world_hint=False,
        ),
    )
    async def propose_edit(
        edits: list[EditOperation],
        description: str,
    ) -> ProposalDetail:
        """Propose file changes as search/replace operations.

        Each operation replaces 'search' (copied exactly from the current
        file, occurring exactly once) with 'replace'; an empty 'search'
        creates a new file. Operations on the same file apply in order.
        Line endings need not match: '\\n' in 'search' also matches a
        '\\r\\n' file, and 'replace' is written with the file's own line
        endings. Nothing is written to the repository: the result is a
        stored proposal with a unified diff. If an operation is wrong, the
        error says which one and why; fix it and propose again.
        """

        return ProposalDetail.of(
            await call(
                lambda: proposal_service.propose(
                    repository_root=root,
                    operations=edits,
                    description=description,
                    source=ProposalSource.AGENT,
                ),
            ),
        )

    @server.tool(
        annotations=_READ_ONLY,
    )
    async def get_proposal(
        proposal_id: str,
    ) -> ProposalDetail:
        """Return a proposal's diff, status and validation results."""

        return ProposalDetail.of(
            await call(
                lambda: proposal_service.get(
                    repository_root=root,
                    proposal_id=proposal_id,
                ),
            ),
        )

    @server.tool(
        annotations=_READ_ONLY,
    )
    async def list_proposals(
        limit: int = 20,
    ) -> ProposalList:
        """List recent proposals, newest first, without diffs.

        Each entry gives the status and per-file line counts; call
        get_proposal for a proposal's diff.
        """

        views = await call(
            lambda: proposal_service.list(
                repository_root=root,
                limit=max(
                    1,
                    min(
                        limit,
                        200,
                    ),
                ),
            ),
        )

        return ProposalList(
            proposals=[ProposalSummary.of(view) for view in views],
        )

    if not allow_apply:
        return

    @server.tool(
        annotations=ToolAnnotations(
            read_only_hint=False,
            destructive_hint=True,
            idempotent_hint=False,
            open_world_hint=False,
        ),
    )
    async def apply_proposal(
        proposal_id: str,
        run_validation: bool = True,
    ) -> ProposalDetail:
        """Write a pending proposal to the repository.

        A snapshot is taken first, and the write is all-or-nothing. Fails
        if any file changed since the proposal was made (propose again).
        Then the project's validation commands run unless run_validation
        is false; check the result's validation field.
        """

        return ProposalDetail.of(
            await call(
                lambda: proposal_service.apply(
                    repository_root=root,
                    proposal_id=proposal_id,
                    validate=run_validation,
                ),
            ),
        )

    @server.tool(
        annotations=ToolAnnotations(
            read_only_hint=False,
            destructive_hint=True,
            idempotent_hint=False,
            open_world_hint=False,
        ),
    )
    async def rollback_proposal(
        proposal_id: str,
    ) -> ProposalDetail:
        """Undo an applied proposal from its snapshot.

        Refuses if a file changed after the proposal was applied, so later
        work is never overwritten.
        """

        return ProposalDetail.of(
            await call(
                lambda: proposal_service.rollback(
                    repository_root=root,
                    proposal_id=proposal_id,
                ),
            ),
        )
