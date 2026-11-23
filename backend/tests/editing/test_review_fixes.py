"""Regression tests for the closing correctness review of editing."""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.core.storage.locations import project_metadata_path
from app.dependencies.providers import get_snapshot_store_factory
from app.editing.change_applier import ChangeApplier
from app.editing.default_provider import DefaultEditingProvider
from app.editing.planner import EditPlanner, parse_edit_blocks
from app.editing.proposal_service import ProposalService
from app.editing.proposals import (
    EditOperation,
    EditProposalError,
    ProposalSource,
    ProposalStatus,
    build_proposal,
)
from app.editing.service import EditingService
from app.editing.validation import (
    ValidationCommand,
    ValidationConfig,
    ValidationRunner,
    validation_config_path,
)
from app.workspace.service import RepositoryWorkspace
from app.workspace.symbols import PythonSymbolExtractor


@pytest.fixture
def project(
    tmp_path: Path,
) -> Path:
    root = tmp_path / "repo"

    metadata = project_metadata_path(
        root,
    )

    metadata.parent.mkdir(
        parents=True,
    )

    metadata.write_bytes(
        b"{}",
    )

    (root / "app.py").write_bytes(
        b"def add(a, b):\n    return a + b\n",
    )

    return root


def _build(
    root: Path,
    search: str,
    replace: str,
    path: str = "app.py",
):
    return build_proposal(
        repository_root=root,
        operations=[
            EditOperation(
                path=path,
                search=search,
                replace=replace,
            ),
        ],
        description="",
        source=ProposalSource.CLIENT,
        change_applier=ChangeApplier(),
    )


def _service() -> ProposalService:
    return ProposalService(
        editing_service=EditingService(
            editing_provider=DefaultEditingProvider(),
            change_applier=ChangeApplier(),
            snapshot_store_factory=get_snapshot_store_factory(),
        ),
        change_applier=ChangeApplier(),
        validation_runner=ValidationRunner(),
        planner=EditPlanner(chat_provider_factory=MagicMock()),
        workspace_opener=lambda root: RepositoryWorkspace.open(
            root,
            MagicMock(),
            PythonSymbolExtractor(),
        ),
        edit_model_label=lambda: "ollama/qwen3:8b",
    )


# --- Search matching -----------------------------------------------------


def test_multi_line_search_must_cover_whole_lines(
    project: Path,
) -> None:
    """'  return' (2 spaces) must not match inside '    return' (4 spaces)."""

    # Not a substring at all: plain "not found".
    with pytest.raises(
        EditProposalError,
        match="was not found",
    ):
        _build(
            project,
            "def add(a, b):\n  return a + b\n",
            "x\n",
        )

    # A substring, but not of whole lines: the precise reason is given.
    with pytest.raises(
        EditProposalError,
        match="matches only part of a line",
    ):
        _build(
            project,
            "  return a + b\n",
            "x\n",
        )


def test_single_line_search_may_match_inside_a_line(
    project: Path,
) -> None:
    proposal = _build(
        project,
        "a + b",
        "b + a",
    )

    assert proposal.change_set.edits[0].updated_content.endswith(
        "    return b + a\n",
    )


def test_crlf_file_stays_crlf_after_a_single_line_search(
    project: Path,
) -> None:
    (project / "win.py").write_bytes(
        b"foo()\r\nbar()\r\n",
    )

    proposal = _build(
        project,
        "foo()",
        "setup()\nfoo()",
        path="win.py",
    )

    assert proposal.change_set.edits[0].updated_content == (
        "setup()\r\nfoo()\r\nbar()\r\n"
    )


def test_removed_dash_dash_lines_are_counted(
    project: Path,
) -> None:
    """A removed SQL comment shows as '--- x' in a diff; still a removal."""

    (project / "q.sql").write_bytes(
        b"-- old comment\nSELECT 1;\n",
    )

    proposal = _build(
        project,
        "-- old comment\n",
        "",
        path="q.sql",
    )

    assert (proposal.files[0].added_lines, proposal.files[0].removed_lines) == (
        0,
        1,
    )


def test_planner_accepts_crlf_model_output() -> None:
    reply = (
        "Done.\r\n\r\n<<<<<<< SEARCH app.py\r\nreturn a + b\r\n"
        "=======\r\nreturn b + a\r\n>>>>>>> REPLACE\r\n"
    )

    operations, notes = parse_edit_blocks(
        reply,
    )

    assert [(op.search, op.replace) for op in operations] == [
        ("return a + b\n", "return b + a\n"),
    ]

    assert notes == "Done."


# --- Apply and validation ------------------------------------------------


def test_a_validation_crash_still_records_the_apply(
    project: Path,
) -> None:
    """Files were written: the proposal must say so and keep its snapshot."""

    service = _service()

    proposal = service.propose(
        project,
        [
            EditOperation(path="app.py", search="a + b", replace="b + a"),
        ],
        "",
    )

    validation_config_path(project).write_text(
        "{not json",
        encoding="utf-8",
    )

    applied = service.apply(
        project,
        proposal.proposal_id,
    )

    assert applied.status is ProposalStatus.APPLIED

    assert applied.snapshot_id

    assert applied.validation is not None

    assert not applied.validation.passed

    assert "could not run" in applied.validation.results[0].output

    # And it can still be rolled back.
    service.rollback(project, proposal.proposal_id)

    assert b"a + b" in (project / "app.py").read_bytes()


def test_timeout_kills_grandchildren_that_hold_the_output(
    project: Path,
) -> None:
    """Killing only the direct child used to wait for the grandchild."""

    spawn_and_wait = (
        "import subprocess, sys, time;"
        "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']);"
        "time.sleep(60)"
    )

    started = time.monotonic()

    report = ValidationRunner().run(
        project,
        ValidationConfig(
            commands=[
                ValidationCommand(
                    name="hangs",
                    argv=[
                        sys.executable,
                        "-c",
                        spawn_and_wait,
                    ],
                    timeout_seconds=1,
                ),
            ],
        ),
    )

    assert report.results[0].timed_out

    assert time.monotonic() - started < 20


def test_argv_with_a_nul_byte_is_reported_not_raised(
    project: Path,
) -> None:
    report = ValidationRunner().run(
        project,
        ValidationConfig(
            commands=[
                ValidationCommand(
                    name="bad",
                    argv=[
                        "python\x00",
                    ],
                ),
            ],
        ),
    )

    assert not report.results[0].passed

    assert "Could not start" in report.results[0].output
