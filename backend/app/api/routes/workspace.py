"""Repository Workspace endpoints.

Thin adapters over ``RepositoryWorkspace``: they translate query
parameters and nothing else. Validation, limits and path security live
in the workspace, so the MCP adapter gets identical behavior.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from app.api.response_docs import (
    BAD_REQUEST_RESPONSE,
    CONFLICT_RESPONSE,
    FILE_TOO_LARGE_RESPONSE,
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    NOT_TEXT_RESPONSE,
    SERVER_ERROR_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
from app.dependencies.providers import (
    get_index_freshness,
    get_workspace_opener,
)
from app.indexing.freshness import IndexFreshness
from app.indexing.models import FreshnessResult
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
    WorkspaceOpener,
)

router = APIRouter(
    prefix="/workspace",
    tags=["Workspace"],
)

_COMMON_RESPONSES = {
    **BAD_REQUEST_RESPONSE,
    **FORBIDDEN_RESPONSE,
    **NOT_FOUND_RESPONSE,
    **VALIDATION_ERROR_RESPONSE,
}


def _open_workspace(
    root_directory: str = Query(
        ...,
        description="Absolute path of a registered RIP project root.",
        examples=[
            "/home/user/projects/my-project",
        ],
    ),
    open_workspace: WorkspaceOpener = Depends(
        get_workspace_opener,
    ),
) -> RepositoryWorkspace:
    """Open the workspace named by the request."""

    return open_workspace(
        root_directory,
    )


@router.get(
    "/file",
    response_model=FileContent,
    operation_id="readWorkspaceFile",
    summary="Read file lines",
    description=(
        "Return a line range of a UTF-8 text file, up to 2,000 lines per "
        "call. Secret-like files (.env, private keys) are refused."
    ),
    response_description="The requested lines.",
    responses={
        **_COMMON_RESPONSES,
        **FILE_TOO_LARGE_RESPONSE,
        **NOT_TEXT_RESPONSE,
    },
)
def read_file(
    path: str = Query(
        ...,
        description="Repository-relative file path.",
        examples=[
            "backend/app/main.py",
        ],
    ),
    start_line: int = Query(
        default=1,
        description="First line to return (1-based).",
    ),
    end_line: int | None = Query(
        default=None,
        description="Last line to return (inclusive). Defaults to the end.",
    ),
    workspace: RepositoryWorkspace = Depends(
        _open_workspace,
    ),
) -> FileContent:
    """Return a line range of a file."""

    return workspace.read_file(
        path=path,
        start_line=start_line,
        end_line=end_line,
    )


@router.get(
    "/tree",
    response_model=TreeListing,
    operation_id="listWorkspaceTree",
    summary="List directory tree",
    description=(
        "List files and directories below a directory, skipping ignored "
        "and protected directories. Paginated with offset and limit."
    ),
    response_description="A page of tree entries.",
    responses=_COMMON_RESPONSES,
)
def list_tree(
    path: str = Query(
        default="",
        description="Repository-relative directory; empty for the root.",
    ),
    max_depth: int = Query(
        default=2,
        description="How many directory levels to include (1-20).",
    ),
    offset: int = Query(
        default=0,
        description="Number of entries to skip.",
    ),
    limit: int = Query(
        default=500,
        description="Maximum entries to return (1-2000).",
    ),
    workspace: RepositoryWorkspace = Depends(
        _open_workspace,
    ),
) -> TreeListing:
    """Return a page of the directory tree."""

    return workspace.list_tree(
        path=path,
        max_depth=max_depth,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/search/text",
    response_model=TextSearchResult,
    operation_id="searchWorkspaceText",
    summary="Search text",
    description=(
        "Find lines matching a literal string (default) or a regular "
        "expression across the repository's text files."
    ),
    response_description="Matching lines.",
    responses=_COMMON_RESPONSES,
)
def search_text(
    query: str = Query(
        ...,
        description="Literal text, or a regular expression when regex=true.",
    ),
    regex: bool = Query(
        default=False,
        description="Treat the query as a Python regular expression.",
    ),
    case_sensitive: bool = Query(
        default=False,
        description="Match case exactly.",
    ),
    path_glob: str | None = Query(
        default=None,
        description="fnmatch pattern for relative paths; '*' also matches '/'.",
        examples=[
            "*.py",
        ],
    ),
    limit: int = Query(
        default=100,
        description="Maximum matches to return (1-500).",
    ),
    workspace: RepositoryWorkspace = Depends(
        _open_workspace,
    ),
) -> TextSearchResult:
    """Return matching lines."""

    return workspace.search_text(
        query=query,
        regex=regex,
        case_sensitive=case_sensitive,
        path_glob=path_glob,
        limit=limit,
    )


@router.get(
    "/symbols",
    response_model=SymbolSearchResult,
    operation_id="findWorkspaceSymbols",
    summary="Find symbol definitions",
    description=(
        "Find class, function and method definitions. Python only for "
        "now; the response lists the languages searched."
    ),
    response_description="Matching definitions.",
    responses=_COMMON_RESPONSES,
)
def find_symbols(
    query: str = Query(
        ...,
        description="Symbol name, or a dotted name such as Class.method.",
        examples=[
            "EditingService.apply",
        ],
    ),
    kind: SymbolKind | None = Query(
        default=None,
        description="Only return this kind of symbol.",
    ),
    match: SymbolMatch = Query(
        default=SymbolMatch.EXACT,
        description="exact (case-sensitive), prefix or contains.",
    ),
    limit: int = Query(
        default=50,
        description="Maximum definitions to return (1-500).",
    ),
    workspace: RepositoryWorkspace = Depends(
        _open_workspace,
    ),
) -> SymbolSearchResult:
    """Return matching symbol definitions."""

    return workspace.find_symbols(
        query=query,
        kind=kind,
        match=match,
        limit=limit,
    )


@router.get(
    "/search/semantic",
    response_model=SemanticSearchResult,
    operation_id="searchWorkspaceSemantic",
    summary="Semantic search",
    description=(
        "Return indexed chunks ranked by semantic similarity to the "
        "query. Files changed since the last index are updated first, up "
        "to RIP_INDEXING_REFRESH_SECONDS; the `index` field reports what "
        "was updated and what is still pending."
    ),
    response_description="Ranked chunks.",
    responses={
        **_COMMON_RESPONSES,
        **CONFLICT_RESPONSE,
        **SERVER_ERROR_RESPONSE,
    },
)
def search_semantic(
    query: str = Query(
        ...,
        description="Natural-language description of the code to find.",
        examples=[
            "where are edits applied to files",
        ],
    ),
    limit: int = Query(
        default=10,
        description="Maximum chunks to return (1-50).",
    ),
    workspace: RepositoryWorkspace = Depends(
        _open_workspace,
    ),
    index_freshness: IndexFreshness = Depends(
        get_index_freshness,
    ),
) -> SemanticSearchResult:
    """Return semantically similar chunks."""

    # Update changed files first; the workspace itself never indexes.
    index = index_freshness.refresh(
        workspace.root,
    )

    result = workspace.search_semantic(
        query=query,
        limit=limit,
    )

    return result.model_copy(
        update={
            "index": index,
        },
    )


@router.get(
    "/index-status",
    response_model=FreshnessResult,
    operation_id="getIndexStatus",
    summary="Index freshness",
    description=(
        "Report whether the project's files have changed since they were "
        "indexed. Reads only; it never updates the index."
    ),
    response_description="Freshness of the semantic index.",
    responses={
        **_COMMON_RESPONSES,
        **SERVER_ERROR_RESPONSE,
    },
)
def get_index_status(
    workspace: RepositoryWorkspace = Depends(
        _open_workspace,
    ),
    index_freshness: IndexFreshness = Depends(
        get_index_freshness,
    ),
) -> FreshnessResult:
    """Report index freshness without updating."""

    return index_freshness.status(
        workspace.root,
    )
