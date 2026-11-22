"""Tests for the Repository Workspace tools."""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.core.storage.locations import (
    project_chroma_directory,
    project_metadata_path,
)
from app.indexing.retrieval_models import (
    SearchResponse,
    SearchResult,
)
from app.indexing.retrieval_service import RetrievalService
from app.repository.models import (
    ChunkBoundary,
    ChunkType,
    RepositoryChunkMetadata,
)
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
    SymbolKind,
)
from app.workspace.service import (
    RepositoryWorkspace,
    SymbolMatch,
)
from app.workspace.symbols import PythonSymbolExtractor

PYTHON_SOURCE = b'''"""Module."""

import functools


class Greeter:
    """Greets."""

    @staticmethod
    @functools.cache
    def greet(name):
        return f"hi {name}"

    async def wave(self):
        return None

    class Inner:
        def deep(self):
            def hidden():
                return 1
            return hidden()


def helper():
    return Greeter.greet("x")
'''


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


def _write(
    root: Path,
    relative_path: str,
    content: bytes,
) -> Path:
    path = root / relative_path

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_bytes(
        content,
    )

    return path


@pytest.fixture
def project(
    tmp_path: Path,
) -> Path:
    root = _register(
        tmp_path / "repo",
    )

    _write(root, "app/greeter.py", PYTHON_SOURCE)
    _write(root, "app/__init__.py", b"")
    _write(root, "README.md", b"# Demo\nTODO: write docs\n")
    _write(root, "node_modules/lib/index.js", b"TODO in a dependency\n")
    _write(root, ".git/config", b"TODO in git\n")
    _write(root, ".env", b"SECRET=TODO\n")
    _write(root, ".env.example", b"SECRET=changeme\n")
    _write(root, "image.png", b"\x89PNG\r\n\x00\x00TODO")

    return root


@pytest.fixture
def retrieval() -> MagicMock:
    return MagicMock(
        spec=RetrievalService,
    )


@pytest.fixture
def workspace(
    project: Path,
    retrieval: MagicMock,
) -> RepositoryWorkspace:
    return RepositoryWorkspace.open(
        root_directory=project,
        retrieval_service=retrieval,
        symbol_extractor=PythonSymbolExtractor(),
    )


# --- Opening -------------------------------------------------------------


def test_open_rejects_unregistered_root(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        UnregisteredWorkspaceError,
    ):
        RepositoryWorkspace.open(
            root_directory=tmp_path,
            retrieval_service=MagicMock(),
            symbol_extractor=PythonSymbolExtractor(),
        )


def test_open_rejects_missing_root(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        WorkspaceFileNotFoundError,
    ):
        RepositoryWorkspace.open(
            root_directory=tmp_path / "missing",
            retrieval_service=MagicMock(),
            symbol_extractor=PythonSymbolExtractor(),
        )


# --- Path safety ---------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/etc/passwd",
        "C:/Windows/win.ini",
        "C:relative",
        "\\\\server\\share\\file",
        "../outside.txt",
        "app/../../outside.txt",
        "..\\outside.txt",
    ],
)
def test_paths_outside_the_root_are_rejected(
    workspace: RepositoryWorkspace,
    project: Path,
    path: str,
) -> None:
    _write(project.parent, "outside.txt", b"secret")

    with pytest.raises(
        WorkspacePathError,
    ):
        workspace.read_file(
            path,
        )


@pytest.mark.parametrize(
    "path",
    [
        ".git/config",
        ".GIT/config",
        ".local_openclaw/project.json",
    ],
)
def test_protected_directories_are_not_readable(
    workspace: RepositoryWorkspace,
    path: str,
) -> None:
    with pytest.raises(
        WorkspacePathError,
        match="protected",
    ):
        workspace.read_file(
            path,
        )


def test_symlink_escaping_the_root_is_rejected(
    workspace: RepositoryWorkspace,
    project: Path,
) -> None:
    outside = _write(
        project.parent,
        "outside.txt",
        b"secret",
    )

    try:
        os.symlink(
            outside,
            project / "link.txt",
        )

    except (OSError, NotImplementedError):
        pytest.skip(
            "Creating symlinks is not permitted on this system.",
        )

    with pytest.raises(
        WorkspacePathError,
    ):
        workspace.read_file(
            "link.txt",
        )

    listed = [
        entry.path
        for entry in workspace.list_tree().entries
    ]

    assert "link.txt" not in listed


# --- read_file -----------------------------------------------------------


def test_read_whole_file(
    workspace: RepositoryWorkspace,
) -> None:
    result = workspace.read_file(
        "README.md",
    )

    assert result.content == "# Demo\nTODO: write docs\n"

    assert (result.start_line, result.end_line, result.total_lines) == (1, 2, 2)

    assert not result.truncated


def test_read_line_range_keeps_crlf(
    workspace: RepositoryWorkspace,
    project: Path,
) -> None:
    _write(project, "win.txt", b"one\r\ntwo\r\nthree\r\n")

    result = workspace.read_file(
        "win.txt",
        start_line=2,
        end_line=3,
    )

    assert result.content == "two\r\nthree\r\n"


def test_line_numbers_ignore_form_feeds_and_unicode_separators(
    workspace: RepositoryWorkspace,
    project: Path,
) -> None:
    _write(
        project,
        "odd.js",
        "a\x0cb\nc\u2028d\nlast\n".encode(),
    )

    result = workspace.read_file(
        "odd.js",
        start_line=3,
        end_line=3,
    )

    assert result.total_lines == 3

    assert result.content == "last\n"


def test_long_ranges_are_truncated_with_a_resume_point(
    workspace: RepositoryWorkspace,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        RepositoryWorkspace,
        "MAX_READ_LINES",
        3,
    )

    _write(
        project,
        "long.txt",
        b"".join(f"line {i}\n".encode() for i in range(1, 11)),
    )

    result = workspace.read_file(
        "long.txt",
        start_line=2,
    )

    assert result.content == "line 2\nline 3\nline 4\n"

    assert result.truncated

    assert result.next_start_line == 5


def test_range_past_the_end_is_empty(
    workspace: RepositoryWorkspace,
) -> None:
    result = workspace.read_file(
        "README.md",
        start_line=50,
    )

    assert result.content == ""

    assert result.end_line < result.start_line


@pytest.mark.parametrize(
    ("start_line", "end_line"),
    [
        (0, None),
        (5, 4),
    ],
)
def test_invalid_ranges_are_rejected(
    workspace: RepositoryWorkspace,
    start_line: int,
    end_line: int | None,
) -> None:
    with pytest.raises(
        WorkspaceError,
    ):
        workspace.read_file(
            "README.md",
            start_line=start_line,
            end_line=end_line,
        )


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        ".env.local",
        "certs/server.pem",
        "id_rsa",
    ],
)
def test_secret_like_files_are_refused(
    workspace: RepositoryWorkspace,
    project: Path,
    path: str,
) -> None:
    _write(project, path, b"secret")

    with pytest.raises(
        WorkspacePathError,
        match="secrets",
    ):
        workspace.read_file(
            path,
        )


def test_env_templates_are_readable(
    workspace: RepositoryWorkspace,
) -> None:
    assert workspace.read_file(".env.example").content == "SECRET=changeme\n"


def test_binary_and_non_utf8_files_are_refused(
    workspace: RepositoryWorkspace,
    project: Path,
) -> None:
    _write(project, "latin1.txt", "café".encode("latin-1"))

    for path in (
        "image.png",
        "latin1.txt",
    ):
        with pytest.raises(
            NotATextFileError,
        ):
            workspace.read_file(
                path,
            )


def test_oversized_files_are_refused(
    workspace: RepositoryWorkspace,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        RepositoryWorkspace,
        "MAX_FILE_BYTES",
        10,
    )

    with pytest.raises(
        FileTooLargeError,
    ):
        workspace.read_file(
            "README.md",
        )


def test_directories_and_missing_files_are_not_found(
    workspace: RepositoryWorkspace,
) -> None:
    for path in (
        "app",
        "missing.py",
    ):
        with pytest.raises(
            WorkspaceFileNotFoundError,
        ):
            workspace.read_file(
                path,
            )


# --- list_tree -----------------------------------------------------------


def test_tree_skips_ignored_and_protected_directories(
    workspace: RepositoryWorkspace,
) -> None:
    listing = workspace.list_tree()

    paths = {
        entry.path
        for entry in listing.entries
    }

    assert {
        "app",
        "app/greeter.py",
        "README.md",
        ".env.example",
    } <= paths

    assert not any(
        path.startswith(
            (
                "node_modules",
                ".git",
                ".local_openclaw",
            ),
        )
        for path in paths
    )


def test_tree_reports_kinds_and_sizes(
    workspace: RepositoryWorkspace,
) -> None:
    entries = {
        entry.path: entry
        for entry in workspace.list_tree().entries
    }

    assert entries["app"].kind is EntryKind.DIRECTORY

    assert entries["app"].size_bytes is None

    assert entries["README.md"].kind is EntryKind.FILE

    assert entries["README.md"].size_bytes == len(b"# Demo\nTODO: write docs\n")


def test_tree_depth_and_subdirectory(
    workspace: RepositoryWorkspace,
    project: Path,
) -> None:
    _write(project, "a/b/c/deep.txt", b"x")

    shallow = {
        entry.path
        for entry in workspace.list_tree(max_depth=1).entries
    }

    assert "a" in shallow

    assert "a/b" not in shallow

    subtree = workspace.list_tree(
        path="a/b",
        max_depth=5,
    )

    assert subtree.path == "a/b"

    assert [entry.path for entry in subtree.entries] == [
        "a/b/c",
        "a/b/c/deep.txt",
    ]


def test_tree_pagination(
    workspace: RepositoryWorkspace,
) -> None:
    everything = workspace.list_tree()

    first = workspace.list_tree(
        limit=2,
    )

    second = workspace.list_tree(
        offset=2,
        limit=2,
    )

    assert first.truncated

    assert first.total_entries == everything.total_entries

    assert [entry.path for entry in first.entries + second.entries] == [
        entry.path
        for entry in everything.entries[:4]
    ]


@pytest.mark.parametrize(
    "arguments",
    [
        {"max_depth": 0},
        {"max_depth": 21},
        {"limit": 0},
        {"limit": 5000},
        {"offset": -1},
    ],
)
def test_tree_rejects_out_of_range_arguments(
    workspace: RepositoryWorkspace,
    arguments: dict,
) -> None:
    with pytest.raises(
        WorkspaceError,
    ):
        workspace.list_tree(
            **arguments,
        )


# --- search_text ---------------------------------------------------------


def test_text_search_skips_ignored_secret_and_binary_files(
    workspace: RepositoryWorkspace,
) -> None:
    result = workspace.search_text(
        "TODO",
    )

    assert [(match.path, match.line) for match in result.matches] == [
        ("README.md", 2),
    ]

    assert not result.truncated


def test_text_search_is_literal_by_default(
    workspace: RepositoryWorkspace,
) -> None:
    result = workspace.search_text(
        'f"hi {name}"',
    )

    assert [match.path for match in result.matches] == [
        "app/greeter.py",
    ]


def test_text_search_case_and_regex(
    workspace: RepositoryWorkspace,
) -> None:
    assert workspace.search_text("todo").matches

    assert not workspace.search_text("todo", case_sensitive=True).matches

    regex_result = workspace.search_text(
        r"def \w+\(self\)",
        regex=True,
    )

    assert {match.line for match in regex_result.matches} == {
        14,
        18,
    }


def test_invalid_regex_is_a_clear_error(
    workspace: RepositoryWorkspace,
) -> None:
    with pytest.raises(
        WorkspaceError,
        match="Invalid regular expression",
    ):
        workspace.search_text(
            "(unclosed",
            regex=True,
        )


def test_text_search_path_glob(
    workspace: RepositoryWorkspace,
) -> None:
    result = workspace.search_text(
        "return",
        path_glob="*.py",
    )

    assert result.matches

    assert all(match.path.endswith(".py") for match in result.matches)

    assert not workspace.search_text("return", path_glob="*.md").matches


def test_text_search_limit_truncates(
    workspace: RepositoryWorkspace,
) -> None:
    result = workspace.search_text(
        "return",
        limit=2,
    )

    assert len(result.matches) == 2

    assert result.truncated

    assert result.truncation_reason is not None


def test_long_lines_are_shortened_around_the_match(
    workspace: RepositoryWorkspace,
    project: Path,
) -> None:
    _write(
        project,
        "minified.js",
        b"x" * 5000 + b"NEEDLE" + b"y" * 5000,
    )

    match = workspace.search_text(
        "NEEDLE",
    ).matches[0]

    assert match.column == 5001

    assert "NEEDLE" in match.text

    assert len(match.text) <= RepositoryWorkspace.MAX_MATCH_TEXT_LENGTH + 2


def test_empty_and_oversized_queries_are_rejected(
    workspace: RepositoryWorkspace,
) -> None:
    for query in (
        "   ",
        "x" * 501,
    ):
        with pytest.raises(
            WorkspaceError,
        ):
            workspace.search_text(
                query,
            )


# --- find_symbols --------------------------------------------------------


def test_find_class_and_function(
    workspace: RepositoryWorkspace,
) -> None:
    classes = workspace.find_symbols(
        "Greeter",
    ).symbols

    assert [(s.kind, s.path, s.start_line, s.end_line) for s in classes] == [
        (SymbolKind.CLASS, "app/greeter.py", 6, 21),
    ]

    functions = workspace.find_symbols(
        "helper",
    ).symbols

    assert functions[0].kind is SymbolKind.FUNCTION


def test_method_lookup_by_qualified_name_includes_decorators(
    workspace: RepositoryWorkspace,
) -> None:
    result = workspace.find_symbols(
        "Greeter.greet",
    )

    assert len(result.symbols) == 1

    method = result.symbols[0]

    assert method.kind is SymbolKind.METHOD

    assert method.start_line == 9

    assert result.languages == [
        "Python",
    ]


def test_async_nested_class_and_hidden_functions(
    workspace: RepositoryWorkspace,
) -> None:
    wave = workspace.find_symbols(
        "wave",
    ).symbols[0]

    assert wave.is_async

    deep = workspace.find_symbols(
        "Greeter.Inner.deep",
    ).symbols

    assert len(deep) == 1

    # Functions defined inside functions are not addressable, so skipped.
    assert not workspace.find_symbols("hidden").symbols


def test_symbol_matching_modes_and_kind_filter(
    workspace: RepositoryWorkspace,
) -> None:
    assert not workspace.find_symbols("greeter").symbols

    prefix = workspace.find_symbols(
        "gree",
        match=SymbolMatch.PREFIX,
    )

    assert {s.name for s in prefix.symbols} == {
        "Greeter",
        "greet",
    }

    methods_only = workspace.find_symbols(
        "e",
        match=SymbolMatch.CONTAINS,
        kind=SymbolKind.METHOD,
    )

    assert {s.name for s in methods_only.symbols} == {
        "greet",
        "wave",
        "deep",
    }


def test_files_with_syntax_errors_are_reported(
    workspace: RepositoryWorkspace,
    project: Path,
) -> None:
    _write(project, "broken.py", b"def oops(:\n")

    result = workspace.find_symbols(
        "helper",
    )

    assert result.symbols

    assert result.files_with_syntax_errors == [
        "broken.py",
    ]


def test_symbols_are_reparsed_after_a_file_changes(
    workspace: RepositoryWorkspace,
    project: Path,
) -> None:
    path = _write(project, "mod.py", b"def before():\n    pass\n")

    assert workspace.find_symbols("before").symbols

    path.write_bytes(
        b"def after_the_edit():\n    pass\n",
    )

    os.utime(
        path,
        ns=(
            path.stat().st_atime_ns,
            path.stat().st_mtime_ns + 1_000_000_000,
        ),
    )

    assert not workspace.find_symbols("before").symbols

    assert workspace.find_symbols("after_the_edit").symbols


# --- search_semantic -----------------------------------------------------


def test_semantic_search_reports_an_unindexed_project(
    workspace: RepositoryWorkspace,
    retrieval: MagicMock,
) -> None:
    result = workspace.search_semantic(
        "greeting",
    )

    assert not result.indexed

    assert result.hits == []

    retrieval.search.assert_not_called()


def _result(
    path: str,
    score: float,
) -> SearchResult:
    return SearchResult(
        chunk_id=path,
        content=f"content of {path}",
        metadata=RepositoryChunkMetadata(
            relative_path=Path(
                path,
            ),
            language="Python",
            mime_type="text/x-python",
            sha256="0" * 64,
        ),
        boundary=ChunkBoundary(
            start_line=1,
            end_line=4,
            chunk_type=ChunkType.CLASS,
        ),
        similarity_score=score,
    )


def test_semantic_search_returns_hits_ranked_by_score(
    workspace: RepositoryWorkspace,
    project: Path,
    retrieval: MagicMock,
) -> None:
    project_chroma_directory(
        project,
    ).mkdir(
        parents=True,
    )

    retrieval.search.return_value = SearchResponse(
        query="greeting",
        results=[
            _result("low.py", 0.2),
            _result("high.py", 0.9),
        ],
    )

    result = workspace.search_semantic(
        "greeting",
        limit=5,
    )

    assert result.indexed

    assert [hit.path for hit in result.hits] == [
        "high.py",
        "low.py",
    ]

    assert result.hits[0].chunk_type == "class"

    query = retrieval.search.call_args.args[0]

    assert query.root_directory == str(project.resolve())

    assert query.limit == 5


# --- Hardening from the security review ----------------------------------


def _make_junction(
    link: Path,
    target: Path,
) -> None:
    """Create a Windows directory junction, or skip the test."""

    if os.name != "nt":
        pytest.skip(
            "Junctions exist only on Windows.",
        )

    import subprocess

    result = subprocess.run(
        [
            "cmd",
            "/c",
            "mklink",
            "/J",
            str(link),
            str(target),
        ],
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        pytest.skip(
            "Could not create a junction on this system.",
        )


def test_traversal_does_not_follow_junctions_out_of_the_root(
    workspace: RepositoryWorkspace,
    project: Path,
) -> None:
    """Junctions are not symlinks to Python, but must be treated as links."""

    outside = project.parent / "outside_dir"

    _write(outside, "credentials.txt", b"AWS_SECRET=topsecret\n")

    _write(outside, "evil.py", b"def outside_function():\n    pass\n")

    _make_junction(
        project / "linkdir",
        outside,
    )

    paths = [
        entry.path
        for entry in workspace.list_tree(max_depth=5).entries
    ]

    assert not any(path.startswith("linkdir") for path in paths)

    assert not workspace.search_text("topsecret").matches

    assert not workspace.find_symbols("outside_function").symbols

    with pytest.raises(
        WorkspacePathError,
    ):
        workspace.read_file(
            "linkdir/credentials.txt",
        )


def test_junction_inside_the_root_is_listed_but_not_walked(
    workspace: RepositoryWorkspace,
    project: Path,
) -> None:
    _make_junction(
        project / "alias",
        project / "app",
    )

    paths = [
        entry.path
        for entry in workspace.list_tree(max_depth=5).entries
    ]

    assert "alias" in paths

    assert not any(path.startswith("alias/") for path in paths)


def test_secret_file_behind_an_innocent_symlink_name_is_not_searched(
    workspace: RepositoryWorkspace,
    project: Path,
) -> None:
    try:
        os.symlink(
            project / ".env",
            project / "notes.txt",
        )

    except (OSError, NotImplementedError):
        pytest.skip(
            "Creating symlinks is not permitted on this system.",
        )

    assert not workspace.search_text("SECRET=TODO").matches

    with pytest.raises(
        WorkspacePathError,
        match="secrets",
    ):
        workspace.read_file(
            "notes.txt",
        )


@pytest.mark.parametrize(
    "path",
    [
        "README.md\x00.txt",
        pytest.param(
            "README.md:hidden",
            marks=pytest.mark.skipif(
                os.name != "nt",
                reason="Alternate data streams exist only on Windows.",
            ),
        ),
    ],
)
def test_paths_with_nul_bytes_or_data_streams_are_rejected(
    workspace: RepositoryWorkspace,
    path: str,
) -> None:
    with pytest.raises(
        WorkspacePathError,
        match="not allowed",
    ):
        workspace.read_file(
            path,
        )


def test_catastrophic_regex_is_stopped_by_the_time_budget(
    workspace: RepositoryWorkspace,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReDoS: a backtracking pattern cannot hang the search."""

    import time

    monkeypatch.setattr(
        RepositoryWorkspace,
        "TEXT_SEARCH_TIME_BUDGET_SECONDS",
        0.5,
    )

    _write(project, "redos.txt", b"a" * 60 + b"b\n")

    started = time.monotonic()

    result = workspace.search_text(
        r"(a|aa)+$",
        regex=True,
    )

    assert time.monotonic() - started < 5

    assert result.truncated

    assert "seconds" in (result.truncation_reason or "")


def test_walk_limit_truncates_every_tool(
    workspace: RepositoryWorkspace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        RepositoryWorkspace,
        "MAX_WALK_ENTRIES",
        2,
    )

    tree = workspace.list_tree()

    assert tree.truncated

    assert tree.total_entries == 2

    text = workspace.search_text(
        "TODO",
    )

    assert text.truncated

    assert "entries" in (text.truncation_reason or "")

    symbols = workspace.find_symbols(
        "helper",
    )

    assert symbols.truncated


@pytest.mark.parametrize(
    "path",
    [
        ".npmrc",
        ".git-credentials",
        ".netrc",
        "id_rsa_work",
        "keys/release.jks",
        ".env.production",
    ],
)
def test_more_credential_files_are_refused(
    workspace: RepositoryWorkspace,
    project: Path,
    path: str,
) -> None:
    _write(project, path, b"token")

    with pytest.raises(
        WorkspacePathError,
        match="secrets",
    ):
        workspace.read_file(
            path,
        )


def test_public_keys_and_templates_stay_readable(
    workspace: RepositoryWorkspace,
    project: Path,
) -> None:
    _write(project, "id_rsa.pub", b"ssh-rsa AAAA\n")

    _write(project, ".npmrc.example", b"registry=https://example.test\n")

    assert workspace.read_file("id_rsa.pub").content == "ssh-rsa AAAA\n"

    assert workspace.read_file(".npmrc.example").total_lines == 1


def test_symbols_inside_conditional_blocks_are_found(
    workspace: RepositoryWorkspace,
    project: Path,
) -> None:
    _write(
        project,
        "compat.py",
        b"from typing import TYPE_CHECKING\n"
        b"\n"
        b"if TYPE_CHECKING:\n"
        b"    class OnlyForTypes:\n"
        b"        pass\n"
        b"\n"
        b"try:\n"
        b"    from fast import parse\n"
        b"except ImportError:\n"
        b"    def parse(text):\n"
        b"        return text\n"
        b"\n"
        b"class Config:\n"
        b"    if True:\n"
        b"        def conditional_method(self):\n"
        b"            pass\n",
    )

    assert workspace.find_symbols("OnlyForTypes").symbols

    fallback = workspace.find_symbols("parse").symbols

    assert [symbol.start_line for symbol in fallback] == [
        10,
    ]

    method = workspace.find_symbols("Config.conditional_method").symbols

    assert method[0].kind is SymbolKind.METHOD


# --- .gitignore ----------------------------------------------------------


def test_gitignored_paths_are_hidden_from_tree_and_search(
    workspace: RepositoryWorkspace,
    project: Path,
) -> None:
    _write(project, ".gitignore", b"dist/\n*.log\n!keep.log\n")
    _write(project, "dist/bundle.js", b"TODO bundled\n")
    _write(project, "debug.log", b"TODO in a log\n")
    _write(project, "keep.log", b"TODO kept\n")

    paths = {
        entry.path
        for entry in workspace.list_tree(max_depth=5).entries
    }

    assert "dist" not in paths

    assert "debug.log" not in paths

    assert {"keep.log", ".gitignore"} <= paths

    matched = {
        match.path
        for match in workspace.search_text("TODO").matches
    }

    assert matched == {
        "README.md",
        "keep.log",
    }


def test_gitignored_file_can_still_be_read_directly(
    workspace: RepositoryWorkspace,
    project: Path,
) -> None:
    """Ignore rules decide what is listed, not what is accessible."""

    _write(project, ".gitignore", b"generated/\n")
    _write(project, "generated/schema.py", b"SCHEMA = 1\n")

    assert workspace.read_file("generated/schema.py").content == "SCHEMA = 1\n"


def test_nested_gitignore_and_info_exclude_are_honored(
    workspace: RepositoryWorkspace,
    project: Path,
) -> None:
    _write(project, "pkg/.gitignore", b"out/\n")
    _write(project, "pkg/out/x.py", b"def hidden_by_nested():\n    pass\n")
    _write(project, "out/y.py", b"def visible_at_root():\n    pass\n")
    _write(project, ".git/info/exclude", b"scratch/\n")
    _write(project, "scratch/z.py", b"def excluded_locally():\n    pass\n")

    assert not workspace.find_symbols("hidden_by_nested").symbols

    assert workspace.find_symbols("visible_at_root").symbols

    assert not workspace.find_symbols("excluded_locally").symbols
