"""Tests for the MCP server.

In-process tests drive the real ``MCPServer`` through the SDK's own
``Client``. The stdio tests launch ``python -m app.mcp_server`` as a
subprocess, exactly as Claude Code or another MCP client does, which
also proves nothing but protocol messages reaches stdout.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from mcp import Client, StdioServerParameters

from app.core.storage.locations import (
    is_registered_project,
    project_metadata_path,
)
from app.indexing.exceptions import IndexingBusyError
from app.indexing.models import (
    IndexingResult,
    IndexStatus,
)
from app.indexing.service import IndexingService
from app.mcp_server.server import EditingMode, build_server
from app.workspace.service import RepositoryWorkspace
from app.workspace.symbols import PythonSymbolExtractor

BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]

EXPECTED_TOOLS = {
    "read_file",
    "list_tree",
    "search_text",
    "find_symbols",
    "search_semantic",
    "index_status",
    "reindex",
}


PROPOSE_TOOLS = {
    "propose_edit",
    "get_proposal",
    "list_proposals",
}

APPLY_TOOLS = {
    "apply_proposal",
    "rollback_proposal",
}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _register(
    root: Path,
) -> Path:
    metadata_path = project_metadata_path(
        root,
    )

    metadata_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata_path.write_bytes(
        b"{}",
    )

    return root


@pytest.fixture
def project(
    tmp_path: Path,
) -> Path:
    root = _register(
        tmp_path / "repo",
    )

    (root / "app.py").write_bytes(
        b"class Service:\n    def run(self):\n        return 'TODO'\n",
    )

    (root / ".env").write_bytes(
        b"API_KEY=TODO\n",
    )

    return root


@pytest.fixture
def indexing() -> MagicMock:
    service = MagicMock(
        spec=IndexingService,
    )

    service.status.return_value = IndexStatus(
        indexed=False,
        configured_embedding_model="ollama:nomic-embed-text",
        compatible=False,
    )

    service.index_repository.return_value = IndexingResult(
        scanned_files=1,
        indexed_files=1,
        indexed_chunks=1,
        skipped_files=0,
        failed_files=0,
    )

    return service


@pytest.fixture
def client(
    project: Path,
    indexing: MagicMock,
) -> Client:
    workspace = RepositoryWorkspace.open(
        root_directory=project,
        retrieval_service=MagicMock(),
        symbol_extractor=PythonSymbolExtractor(),
    )

    return Client(
        build_server(
            workspace=workspace,
            indexing_service=indexing,
        ),
    )


# --- In-process ----------------------------------------------------------


@pytest.mark.anyio
async def test_lists_all_tools_with_annotations_and_schemas(
    client: Client,
) -> None:
    async with client:
        tools = {
            tool.name: tool
            for tool in (await client.list_tools()).tools
        }

    assert set(tools) == EXPECTED_TOOLS

    for name, tool in tools.items():
        assert tool.description, name

        assert tool.output_schema is not None, name

        assert tool.annotations is not None

        assert tool.annotations.read_only_hint is (name != "reindex")


@pytest.mark.anyio
async def test_server_sends_usage_instructions(
    client: Client,
) -> None:
    async with client:
        instructions = client.instructions or ""

    assert "relative to the repository root" in instructions


@pytest.mark.anyio
async def test_tools_return_structured_results(
    client: Client,
) -> None:
    async with client:
        read = await client.call_tool(
            "read_file",
            {
                "path": "app.py",
                "start_line": 2,
                "end_line": 2,
            },
        )

        symbols = await client.call_tool(
            "find_symbols",
            {
                "query": "Service.run",
            },
        )

        text = await client.call_tool(
            "search_text",
            {
                "query": "TODO",
            },
        )

        tree = await client.call_tool(
            "list_tree",
            {},
        )

    assert not read.is_error

    assert read.structured_content["content"] == "    def run(self):\n"

    assert symbols.structured_content["symbols"][0]["kind"] == "method"

    # .env is a secret-like file, so only app.py matches.
    assert [
        match["path"]
        for match in text.structured_content["matches"]
    ] == [
        "app.py",
    ]

    assert "app.py" in [
        entry["path"]
        for entry in tree.structured_content["entries"]
    ]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("path", "message"),
    [
        ("../outside.txt", "outside the repository"),
        (".git/config", "protected directory"),
        (".env", "secrets"),
        ("missing.py", "File not found"),
    ],
)
async def test_domain_errors_become_tool_errors_with_the_message(
    client: Client,
    path: str,
    message: str,
) -> None:
    async with client:
        result = await client.call_tool(
            "read_file",
            {
                "path": path,
            },
        )

    assert result.is_error

    assert message in result.content[0].text


@pytest.mark.anyio
async def test_index_tools_use_the_bound_root(
    client: Client,
    project: Path,
    indexing: MagicMock,
) -> None:
    async with client:
        status = await client.call_tool(
            "index_status",
            {},
        )

        reindex = await client.call_tool(
            "reindex",
            {},
        )

    assert status.structured_content["indexed"] is False

    assert reindex.structured_content["indexed_files"] == 1

    indexing.status.assert_called_once_with(
        project,
    )

    indexing.index_repository.assert_called_once_with(
        project,
    )


@pytest.mark.anyio
async def test_reindex_reports_a_busy_index_as_a_tool_error(
    client: Client,
    indexing: MagicMock,
) -> None:
    indexing.index_repository.side_effect = IndexingBusyError(
        "Another process is indexing this project.",
    )

    async with client:
        result = await client.call_tool(
            "reindex",
            {},
        )

    assert result.is_error

    assert "Another process is indexing" in result.content[0].text


# --- Real stdio subprocess -----------------------------------------------


def _server_parameters(
    root: Path,
) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "app.mcp_server",
            "--root",
            str(
                root,
            ),
        ],
        cwd=str(
            BACKEND_DIRECTORY,
        ),
        env={
            "PYTHONPATH": str(
                BACKEND_DIRECTORY,
            ),
            "LOC_LOGGING_LEVEL": "WARNING",
        },
    )


@pytest.mark.anyio
async def test_stdio_server_registers_root_and_serves_tools(
    tmp_path: Path,
) -> None:
    """The path Claude Code uses: launch, initialize, list, call."""

    root = tmp_path / "fresh-repo"

    root.mkdir()

    (root / "main.py").write_bytes(
        b"def entry_point():\n    pass\n",
    )

    assert not is_registered_project(
        root,
    )

    async with Client(
        _server_parameters(
            root,
        ),
        read_timeout_seconds=60,
    ) as stdio_client:
        tools = {
            tool.name
            for tool in (await stdio_client.list_tools()).tools
        }

        symbols = await stdio_client.call_tool(
            "find_symbols",
            {
                "query": "entry_point",
            },
        )

        status = await stdio_client.call_tool(
            "index_status",
            {},
        )

    # Started without --editing, the server is in "propose" mode.
    assert tools == EXPECTED_TOOLS | PROPOSE_TOOLS

    assert symbols.structured_content["symbols"][0]["path"] == "main.py"

    # Starting the server registered the project, without indexing it.
    assert is_registered_project(
        root,
    )

    assert status.structured_content["indexed"] is False


def test_stdio_server_refuses_a_home_directory_root() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.mcp_server",
            "--root",
            str(
                Path.home(),
            ),
        ],
        cwd=BACKEND_DIRECTORY,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 2

    assert "home directory or a drive root" in result.stderr

    # Nothing but protocol may ever appear on stdout.
    assert result.stdout == ""


# --- Editing modes -------------------------------------------------------


def _editing_client(
    project: Path,
    indexing: MagicMock,
    mode: EditingMode,
) -> Client:
    from app.dependencies.providers import get_snapshot_store_factory
    from app.editing.change_applier import ChangeApplier
    from app.editing.default_provider import DefaultEditingProvider
    from app.editing.planner import EditPlanner
    from app.editing.proposal_service import ProposalService
    from app.editing.service import EditingService
    from app.editing.validation import ValidationRunner

    def open_workspace(
        root: Path,
    ) -> RepositoryWorkspace:
        return RepositoryWorkspace.open(
            root,
            MagicMock(),
            PythonSymbolExtractor(),
        )

    proposal_service = ProposalService(
        editing_service=EditingService(
            editing_provider=DefaultEditingProvider(),
            change_applier=ChangeApplier(),
            snapshot_store_factory=get_snapshot_store_factory(),
        ),
        change_applier=ChangeApplier(),
        validation_runner=ValidationRunner(),
        planner=EditPlanner(chat_provider_factory=MagicMock()),
        workspace_opener=open_workspace,
        edit_model_label=lambda: "ollama/qwen3:8b",
    )

    return Client(
        build_server(
            workspace=open_workspace(project),
            indexing_service=indexing,
            proposal_service=proposal_service,
            editing_mode=mode,
        ),
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("off", EXPECTED_TOOLS),
        ("propose", EXPECTED_TOOLS | PROPOSE_TOOLS),
        ("apply", EXPECTED_TOOLS | PROPOSE_TOOLS | APPLY_TOOLS),
    ],
)
async def test_editing_mode_controls_which_tools_exist(
    project: Path,
    indexing: MagicMock,
    mode: str,
    expected: set[str],
) -> None:
    async with _editing_client(
        project,
        indexing,
        EditingMode(mode),
    ) as client:
        tools = {
            tool.name: tool
            for tool in (await client.list_tools()).tools
        }

    assert set(tools) == expected

    if "apply_proposal" in tools:
        annotations = tools["apply_proposal"].annotations

        assert annotations is not None and annotations.destructive_hint


@pytest.mark.anyio
async def test_propose_mode_creates_proposals_without_writing(
    project: Path,
    indexing: MagicMock,
) -> None:
    async with _editing_client(
        project,
        indexing,
        EditingMode.PROPOSE,
    ) as client:
        result = await client.call_tool(
            "propose_edit",
            {
                "edits": [
                    {
                        "path": "app.py",
                        "search": "return 'TODO'",
                        "replace": "return 'done'",
                    },
                ],
                "description": "finish the TODO",
            },
        )

        bad = await client.call_tool(
            "propose_edit",
            {
                "edits": [
                    {
                        "path": "app.py",
                        "search": "not there",
                        "replace": "x",
                    },
                ],
                "description": "broken",
            },
        )

        apply_attempt = await client.call_tool(
            "apply_proposal",
            {
                "proposal_id": result.structured_content["proposal_id"],
            },
        )

    assert not result.is_error

    assert "+        return 'done'" in result.structured_content["diff"]

    assert b"TODO" in (project / "app.py").read_bytes()

    assert bad.is_error

    assert "was not found" in bad.content[0].text

    # The tool does not exist in propose mode.
    assert apply_attempt.is_error


@pytest.mark.anyio
async def test_apply_mode_applies_and_rolls_back(
    project: Path,
    indexing: MagicMock,
) -> None:
    original = (project / "app.py").read_bytes()

    async with _editing_client(
        project,
        indexing,
        EditingMode.APPLY,
    ) as client:
        proposal = await client.call_tool(
            "propose_edit",
            {
                "edits": [
                    {
                        "path": "app.py",
                        "search": "return 'TODO'",
                        "replace": "return 'done'",
                    },
                ],
                "description": "finish the TODO",
            },
        )

        proposal_id = proposal.structured_content["proposal_id"]

        applied = await client.call_tool(
            "apply_proposal",
            {
                "proposal_id": proposal_id,
            },
        )

        assert applied.structured_content["status"] == "applied"

        # No validation commands configured: reported, not silently skipped.
        assert applied.structured_content["validation"]["ran"] is False

        assert b"'done'" in (project / "app.py").read_bytes()

        rolled_back = await client.call_tool(
            "rollback_proposal",
            {
                "proposal_id": proposal_id,
            },
        )

    assert rolled_back.structured_content["status"] == "rolled_back"

    assert (project / "app.py").read_bytes() == original
