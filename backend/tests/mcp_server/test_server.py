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
from app.mcp_server.server import build_server
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

    assert tools == EXPECTED_TOOLS

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
