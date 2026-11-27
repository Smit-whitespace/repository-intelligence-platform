"""Tests for edit proposals: building, storing, the workflow, validation."""

import json
import os
import stat
from datetime import timedelta
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.chat.models import ChatResponse
from app.core.storage.locations import project_metadata_path
from app.dependencies.providers import get_snapshot_store_factory
from app.editing.change_applier import ChangeApplier
from app.editing.default_provider import DefaultEditingProvider
from app.editing.exceptions import (
    EditConflictError,
    EditingError,
    ProposalNotFoundError,
    ProposalStateError,
)
from app.editing.models import ChangeSet, FileEdit
from app.editing.planner import EditPlanner, parse_edit_blocks
from app.editing.proposal_service import ProposalService
from app.editing.proposals import (
    MAX_OPERATIONS,
    EditOperation,
    EditProposalError,
    FileChange,
    ProposalSource,
    ProposalStatus,
    ProposalStore,
    build_proposal,
)
from app.editing.service import EditingService
from app.editing.snapshot_models import Snapshot, SnapshotFile
from app.editing.validation import (
    ValidationCommand,
    ValidationConfig,
    ValidationRunner,
)
from app.workspace.service import RepositoryWorkspace
from app.workspace.symbols import PythonSymbolExtractor


def _register(
    root: Path,
) -> Path:
    path = project_metadata_path(
        root,
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_bytes(
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
        b"def greet(name):\n    return 'hi ' + name\n\n\ndef helper():\n    return 1\n",
    )

    return root


def _op(
    path: str,
    search: str,
    replace: str,
) -> EditOperation:
    return EditOperation(
        path=path,
        search=search,
        replace=replace,
    )


def _build(
    root: Path,
    *operations: EditOperation,
):
    return build_proposal(
        repository_root=root,
        operations=list(
            operations,
        ),
        description="test",
        source=ProposalSource.CLIENT,
        change_applier=ChangeApplier(),
    )


def _service(
    planner: EditPlanner | None = None,
    runner: ValidationRunner | None = None,
) -> ProposalService:
    def open_workspace(
        root: Path,
    ) -> RepositoryWorkspace:
        return RepositoryWorkspace.open(
            root,
            MagicMock(),
            PythonSymbolExtractor(),
        )

    return ProposalService(
        editing_service=EditingService(
            editing_provider=DefaultEditingProvider(),
            change_applier=ChangeApplier(),
            snapshot_store_factory=get_snapshot_store_factory(),
        ),
        change_applier=ChangeApplier(),
        validation_runner=runner or ValidationRunner(),
        planner=planner or EditPlanner(chat_provider_factory=MagicMock()),
        workspace_opener=open_workspace,
        edit_model_label=lambda: "ollama/qwen3:8b",
    )


# --- Building proposals --------------------------------------------------


def test_single_replacement_produces_a_diff(
    project: Path,
) -> None:
    proposal = _build(
        project,
        _op("app.py", "return 'hi ' + name", "return f'hello {name}'"),
    )

    assert proposal.status is ProposalStatus.PENDING

    [file] = proposal.files

    assert (file.path, file.change, file.added_lines, file.removed_lines) == (
        "app.py",
        FileChange.MODIFY,
        1,
        1,
    )

    assert "-    return 'hi ' + name" in proposal.diff

    assert "+    return f'hello {name}'" in proposal.diff

    assert proposal.diff.startswith("--- a/app.py\n+++ b/app.py\n")

    # Nothing is written while proposing.
    assert b"'hi '" in (project / "app.py").read_bytes()


def test_operations_on_one_file_apply_in_order(
    project: Path,
) -> None:
    proposal = _build(
        project,
        _op("app.py", "def helper():", "def helper_renamed():"),
        _op("app.py", "def helper_renamed():\n    return 1", "def helper_renamed():\n    return 2"),
    )

    [edit] = proposal.change_set.edits

    assert "def helper_renamed():\n    return 2" in edit.updated_content


def test_new_file_creation(
    project: Path,
) -> None:
    proposal = _build(
        project,
        _op("pkg/new.py", "", "VALUE = 1\n"),
    )

    [file] = proposal.files

    assert file.change is FileChange.CREATE

    assert proposal.diff.startswith("--- /dev/null\n+++ b/pkg/new.py\n")


def test_every_bad_operation_is_reported_at_once(
    project: Path,
) -> None:
    (project / "dup.py").write_bytes(
        b"x = 1\nx = 1\n",
    )

    with pytest.raises(
        EditProposalError,
    ) as error:
        _build(
            project,
            _op("app.py", "not in the file", "y"),
            _op("dup.py", "x = 1", "x = 2"),
            _op("missing.py", "something", "y"),
            _op("app.py.bak", "", "copy"),
        )

    lines = str(error.value).splitlines()

    assert any("app.py (operation 1): 'search' text was not found" in line for line in lines)

    assert any("dup.py" in line and "occurs 2 times" in line for line in lines)

    assert any("missing.py" in line and "does not exist" in line for line in lines)

    assert len(lines) == 3


def test_empty_search_on_an_existing_file_is_rejected(
    project: Path,
) -> None:
    with pytest.raises(
        EditProposalError,
        match="already exists",
    ):
        _build(
            project,
            _op("app.py", "", "overwrite everything"),
        )


def test_lf_search_matches_a_crlf_file_and_keeps_crlf(
    project: Path,
) -> None:
    (project / "win.py").write_bytes(
        b"a = 1\r\nb = 2\r\n",
    )

    proposal = _build(
        project,
        _op("win.py", "a = 1\nb = 2\n", "a = 10\nb = 20\n"),
    )

    assert proposal.change_set.edits[0].updated_content == "a = 10\r\nb = 20\r\n"


def test_crlf_search_matches_an_lf_file_and_keeps_lf(
    project: Path,
) -> None:
    """An agent may copy CRLF text from another file or a Windows read."""

    (project / "unix.py").write_bytes(
        b"a = 1\nb = 2\n",
    )

    proposal = _build(
        project,
        _op("unix.py", "a = 1\r\nb = 2\r\n", "a = 10\r\nb = 20\r\n"),
    )

    assert proposal.change_set.edits[0].updated_content == "a = 10\nb = 20\n"


def test_mixed_line_endings_in_search_still_match(
    project: Path,
) -> None:
    (project / "win.py").write_bytes(
        b"a = 1\r\nb = 2\r\nc = 3\r\n",
    )

    proposal = _build(
        project,
        _op("win.py", "a = 1\r\nb = 2\n", "a = 1\nb = 20\r\n"),
    )

    assert (
        proposal.change_set.edits[0].updated_content
        == "a = 1\r\nb = 20\r\nc = 3\r\n"
    )


def test_single_line_replace_in_an_lf_file_never_adds_crlf(
    project: Path,
) -> None:
    (project / "unix.py").write_bytes(
        b"value = 1\n",
    )

    proposal = _build(
        project,
        _op("unix.py", "value = 1", "value = 1\r\nother = 2"),
    )

    assert proposal.change_set.edits[0].updated_content == "value = 1\nother = 2\n"


@pytest.mark.parametrize(
    "path",
    [
        "../outside.py",
        ".git/hooks/pre-commit",
        ".rip/validation.json",
    ],
)
def test_unsafe_paths_are_rejected_before_reading(
    project: Path,
    path: str,
) -> None:
    """An agent can never write validation commands or hooks this way."""

    with pytest.raises(
        EditingError,
    ):
        _build(
            project,
            _op(path, "", "payload"),
        )


def test_operations_that_change_nothing_are_rejected(
    project: Path,
) -> None:
    with pytest.raises(
        EditProposalError,
        match="do not change any file",
    ):
        _build(
            project,
            _op("app.py", "def helper():", "def helper():"),
        )


def test_operation_limit(
    project: Path,
) -> None:
    with pytest.raises(
        EditProposalError,
        match="At most",
    ):
        _build(
            project,
            *[
                _op(f"f{index}.py", "", "x")
                for index in range(MAX_OPERATIONS + 1)
            ],
        )


# --- Store ---------------------------------------------------------------


def test_store_round_trip_and_newest_first(
    project: Path,
) -> None:
    store = ProposalStore(
        project,
    )

    first = _build(
        project,
        _op("a.py", "", "a\n"),
    )

    # Explicit times: two proposals built in the same clock tick tie.
    second = _build(
        project,
        _op("b.py", "", "b\n"),
    ).model_copy(
        update={
            "created_at": first.created_at + timedelta(seconds=1),
        },
    )

    store.save(first)

    store.save(second)

    assert store.load(first.proposal_id) == first

    assert [proposal.proposal_id for proposal in store.list()] == [
        second.proposal_id,
        first.proposal_id,
    ]


@pytest.mark.parametrize(
    "proposal_id",
    [
        "missing",
        "../../project",
        "0" * 32,
    ],
)
def test_unknown_or_malformed_ids_are_not_found(
    project: Path,
    proposal_id: str,
) -> None:
    with pytest.raises(
        ProposalNotFoundError,
    ):
        ProposalStore(project).load(proposal_id)


def test_views_never_carry_full_file_contents(
    project: Path,
) -> None:
    view = _build(
        project,
        _op("app.py", "def helper():", "def helper2():"),
    ).view()

    assert "change_set" not in view.model_dump()


# --- Workflow ------------------------------------------------------------


def test_propose_apply_rollback_round_trip(
    project: Path,
) -> None:
    service = _service()

    original = (project / "app.py").read_bytes()

    proposal = service.propose(
        project,
        [
            _op("app.py", "return 1", "return 42"),
        ],
        "make helper return 42",
    )

    applied = service.apply(
        project,
        proposal.proposal_id,
        validate=False,
    )

    assert applied.status is ProposalStatus.APPLIED

    assert applied.snapshot_id

    assert b"return 42" in (project / "app.py").read_bytes()

    rolled_back = service.rollback(
        project,
        proposal.proposal_id,
    )

    assert rolled_back.status is ProposalStatus.ROLLED_BACK

    assert (project / "app.py").read_bytes() == original


def test_state_rules_are_enforced(
    project: Path,
) -> None:
    service = _service()

    proposal = service.propose(
        project,
        [
            _op("app.py", "return 1", "return 2"),
        ],
        "",
    )

    with pytest.raises(
        ProposalStateError,
        match="only applied proposals can be rolled back",
    ):
        service.rollback(project, proposal.proposal_id)

    service.reject(project, proposal.proposal_id)

    with pytest.raises(
        ProposalStateError,
        match="rejected",
    ):
        service.apply(project, proposal.proposal_id)

    assert (project / "app.py").read_bytes().count(b"return 1") == 1


def test_proposal_goes_stale_if_the_file_changes(
    project: Path,
) -> None:
    service = _service()

    proposal = service.propose(
        project,
        [
            _op("app.py", "return 1", "return 2"),
        ],
        "",
    )

    (project / "app.py").write_bytes(
        b"edited by a person\n",
    )

    with pytest.raises(
        EditConflictError,
    ):
        service.apply(project, proposal.proposal_id)

    assert service.get(project, proposal.proposal_id).status is ProposalStatus.PENDING


def test_unregistered_root_is_refused(
    tmp_path: Path,
) -> None:
    from app.editing.exceptions import UnregisteredRepositoryError

    with pytest.raises(
        UnregisteredRepositoryError,
    ):
        _service().propose(
            tmp_path,
            [
                _op("a.py", "", "x"),
            ],
            "",
        )


# --- Validation ----------------------------------------------------------


def _python(
    code: str,
    name: str = "check",
    timeout_seconds: float = 60,
) -> ValidationCommand:
    return ValidationCommand(
        name=name,
        argv=[
            sys.executable,
            "-c",
            code,
        ],
        timeout_seconds=timeout_seconds,
    )


def test_validation_runs_after_apply_and_reports_each_command(
    project: Path,
) -> None:
    service = _service()

    service.set_validation_config(
        project,
        ValidationConfig(
            commands=[
                _python("import app; print('ok', app.helper())", name="import"),
                _python("import sys; print('boom'); sys.exit(3)", name="fails"),
            ],
        ),
    )

    proposal = service.propose(
        project,
        [
            _op("app.py", "return 1", "return 7"),
        ],
        "",
    )

    applied = service.apply(
        project,
        proposal.proposal_id,
    )

    report = applied.validation

    assert report is not None and report.ran

    assert not report.passed

    first, second = report.results

    assert first.passed and "ok 7" in first.output

    assert (second.passed, second.exit_code) == (False, 3)

    assert "boom" in second.output


def test_validation_without_commands_does_not_run() -> None:
    report = ValidationRunner().run(
        Path("."),
        ValidationConfig(),
    )

    assert (report.ran, report.passed) == (False, True)


def test_validation_timeout_and_missing_program(
    project: Path,
) -> None:
    report = ValidationRunner().run(
        project,
        ValidationConfig(
            commands=[
                _python("import time; time.sleep(30)", name="slow", timeout_seconds=0.5),
                ValidationCommand(
                    name="missing",
                    argv=[
                        "definitely-not-a-real-program-rip",
                    ],
                ),
            ],
        ),
    )

    slow, missing = report.results

    assert slow.timed_out and not slow.passed

    assert not missing.passed

    assert "Could not start" in missing.output


def test_validation_commands_are_not_run_through_a_shell(
    project: Path,
) -> None:
    """Shell syntax is passed as plain arguments, never interpreted."""

    report = ValidationRunner().run(
        project,
        ValidationConfig(
            commands=[
                _python(
                    "import sys; print(sys.argv[1:])",
                ).model_copy(
                    update={
                        "argv": [
                            sys.executable,
                            "-c",
                            "import sys; print(sys.argv[1:])",
                            "; echo injected",
                        ],
                    },
                ),
            ],
        ),
    )

    assert "['; echo injected']" in report.results[0].output


def test_invalid_validation_file_is_a_clear_error(
    project: Path,
) -> None:
    from app.editing.validation import validation_config_path

    validation_config_path(project).write_text(
        json.dumps({"commands": [{"name": "x", "argv": []}]}),
        encoding="utf-8",
    )

    with pytest.raises(
        EditingError,
        match="validation configuration is invalid",
    ):
        _service().validation_config(project)


# --- Planner -------------------------------------------------------------


MODEL_REPLY = """I'll make helper return 2 and add a constants module.

<<<<<<< SEARCH app.py
def helper():
    return 1
=======
def helper():
    return 2
>>>>>>> REPLACE

<<<<<<< SEARCH `pkg/constants.py`
=======
ANSWER = 42
>>>>>>> REPLACE
"""


def test_parse_edit_blocks_extracts_operations_and_notes() -> None:
    operations, notes = parse_edit_blocks(
        MODEL_REPLY,
    )

    assert [(op.path, op.search, op.replace) for op in operations] == [
        ("app.py", "def helper():\n    return 1\n", "def helper():\n    return 2\n"),
        ("pkg/constants.py", "", "ANSWER = 42\n"),
    ]

    assert notes == "I'll make helper return 2 and add a constants module."


def test_plan_builds_a_planner_proposal_from_the_model_reply(
    project: Path,
) -> None:
    chat_provider = MagicMock()

    chat_provider.generate.return_value = ChatResponse(
        content=MODEL_REPLY,
    )

    service = _service(
        planner=EditPlanner(
            chat_provider_factory=lambda: chat_provider,
        ),
    )

    proposal = service.plan(
        project,
        "make helper return 2 and add a constants module",
        files=[
            "app.py",
        ],
    )

    assert proposal.source is ProposalSource.PLANNER

    assert proposal.model == "ollama/qwen3:8b"

    assert {file.path for file in proposal.files} == {
        "app.py",
        "pkg/constants.py",
    }

    prompt = chat_provider.generate.call_args.args[0]

    user_message = prompt.messages[-1].content

    # The named file is sent in full, exactly as on disk.
    assert "### app.py (whole file)" in user_message

    assert "def greet(name):" in user_message


def test_plan_without_edit_blocks_is_a_clear_error(
    project: Path,
) -> None:
    chat_provider = MagicMock()

    chat_provider.generate.return_value = ChatResponse(
        content="I am not sure what to change.",
    )

    with pytest.raises(
        EditingError,
        match="did not produce any edit blocks",
    ):
        _service(
            planner=EditPlanner(
                chat_provider_factory=lambda: chat_provider,
            ),
        ).plan(
            project,
            "do something",
            files=[
                "app.py",
            ],
        )


def test_plan_needs_context(
    project: Path,
) -> None:
    """With no named files and no index, there is nothing to edit from."""

    with pytest.raises(
        EditingError,
        match="No repository context",
    ):
        _service().plan(
            project,
            "refactor everything",
            files=[],
        )


# --- ChangeApplier fixes -------------------------------------------------


@pytest.mark.skipif(
    os.name == "nt",
    reason="Windows has no executable permission bit.",
)
def test_apply_keeps_the_executable_bit(
    project: Path,
) -> None:
    script = project / "run.sh"

    script.write_bytes(
        b"#!/bin/sh\necho old\n",
    )

    script.chmod(
        0o755,
    )

    ChangeApplier().apply(
        repository_root=project,
        change_set=ChangeSet(
            edits=[
                FileEdit(
                    relative_path=Path("run.sh"),
                    original_content="#!/bin/sh\necho old\n",
                    updated_content="#!/bin/sh\necho new\n",
                ),
            ],
        ),
    )

    assert stat.S_IMODE(script.stat().st_mode) == 0o755


def test_failed_restore_puts_every_file_back(
    project: Path,
) -> None:
    (project / "a.py").write_bytes(
        b"current a\n",
    )

    (project / "b.py").write_bytes(
        b"current b\n",
    )

    class FailSecondWrite(ChangeApplier):
        writes = 0

        def _write_file_atomic(
            self,
            target_path: Path,
            content: str,
        ) -> None:
            type(self).writes += 1

            if type(self).writes == 2:
                raise OSError(
                    "disk full",
                )

            super()._write_file_atomic(
                target_path=target_path,
                content=content,
            )

    with pytest.raises(
        EditingError,
        match="roll back",
    ):
        FailSecondWrite().restore(
            repository_root=project,
            snapshot=Snapshot(
                files=[
                    SnapshotFile(
                        relative_path=Path("a.py"),
                        existed=True,
                        content="old a\n",
                    ),
                    SnapshotFile(
                        relative_path=Path("b.py"),
                        existed=True,
                        content="old b\n",
                    ),
                ],
            ),
        )

    assert (project / "a.py").read_bytes() == b"current a\n"

    assert (project / "b.py").read_bytes() == b"current b\n"
