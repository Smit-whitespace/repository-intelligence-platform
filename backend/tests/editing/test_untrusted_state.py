"""Regression tests for repository-supplied RIP state (security review).

A cloned repository can contain a ``.rip`` directory. These
tests replay the attacks the security review confirmed and check that
RIP only uses state files it signed itself.
"""

import json
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.storage.locations import project_storage_directory
from app.editing.exceptions import UntrustedStateError
from app.editing.proposals import ProposalStore
from app.editing.validation import (
    UNTRUSTED_VALIDATION_MESSAGE,
    load_validation_config,
)
from app.main import app

client = TestClient(
    app,
)


def _clone_of_malicious_repo(
    root: Path,
    marker: Path,
) -> Path:
    """A repository that ships project metadata and validation commands."""

    storage = project_storage_directory(
        root,
    )

    storage.mkdir(
        parents=True,
    )

    (storage / "project.json").write_text(
        "{}",
        encoding="utf-8",
    )

    (storage / "validation.json").write_text(
        json.dumps(
            {
                "commands": [
                    {
                        "name": "tests",
                        "argv": [
                            sys.executable,
                            "-c",
                            f"open({str(marker)!r}, 'w').write('owned')",
                        ],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )

    (root / "app.py").write_bytes(
        b"print(1)\n",
    )

    return root


def test_shipped_validation_commands_never_run(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "attacker-code-ran"

    root = _clone_of_malicious_repo(
        tmp_path / "repo",
        marker,
    )

    shown = client.get(
        "/api/v1/editing/validation",
        params={"root_directory": str(root)},
    ).json()

    # The commands are visible for review, but marked as not approved.
    assert shown["trusted"] is False

    assert shown["commands"][0]["name"] == "tests"

    proposal = client.post(
        "/api/v1/editing/proposals",
        json={
            "repository_root": str(root),
            "edits": [
                {"path": "app.py", "search": "print(1)", "replace": "print(2)"},
            ],
        },
    ).json()

    applied = client.post(
        f"/api/v1/editing/proposals/{proposal['proposal_id']}/apply",
        json={"repository_root": str(root)},
    ).json()

    assert applied["status"] == "applied"

    assert applied["validation"]["ran"] is False

    assert applied["validation"]["results"][0]["output"] == (
        UNTRUSTED_VALIDATION_MESSAGE
    )

    run_now = client.post(
        "/api/v1/editing/validation/run",
        json={"repository_root": str(root)},
    ).json()

    assert run_now["ran"] is False

    assert not marker.exists()


def test_saving_commands_approves_them(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "approved-command-ran"

    root = _clone_of_malicious_repo(
        tmp_path / "repo",
        marker,
    )

    shown = load_validation_config(
        root,
    )

    # The person reviews the commands and saves them: now they may run.
    client.put(
        "/api/v1/editing/validation",
        json={
            "repository_root": str(root),
            "config": {"commands": [c.model_dump() for c in shown.commands]},
        },
    )

    assert load_validation_config(root).trusted

    report = client.post(
        "/api/v1/editing/validation/run",
        json={"repository_root": str(root)},
    ).json()

    assert report["ran"] is True

    assert marker.read_text() == "owned"


def _proposal_file(
    root: Path,
    proposal_id: str,
) -> Path:
    return (
        project_storage_directory(root)
        / "proposals"
        / f"{proposal_id}.json"
    )


def _propose(
    root: Path,
) -> str:
    return client.post(
        "/api/v1/editing/proposals",
        json={
            "repository_root": str(root),
            "edits": [
                {"path": "app.py", "search": "print(1)", "replace": "print(2)"},
            ],
        },
    ).json()["proposal_id"]


def test_tampered_proposal_contents_are_refused(
    tmp_path: Path,
) -> None:
    """The diff shown and the contents written can never diverge."""

    root = _clone_of_malicious_repo(
        tmp_path / "repo",
        tmp_path / "marker",
    )

    proposal_id = _propose(
        root,
    )

    path = _proposal_file(
        root,
        proposal_id,
    )

    stored = json.loads(
        path.read_text(encoding="utf-8"),
    )

    stored["change_set"]["edits"][0]["updated_content"] = (
        "import os\nos.system('echo owned')\n"
    )

    path.write_text(
        json.dumps(stored),
        encoding="utf-8",
    )

    applied = client.post(
        f"/api/v1/editing/proposals/{proposal_id}/apply",
        json={"repository_root": str(root)},
    )

    assert applied.status_code == 403

    assert (root / "app.py").read_bytes() == b"print(1)\n"

    # Untrusted proposals are left out of listings entirely.
    listed = client.get(
        "/api/v1/editing/proposals",
        params={"root_directory": str(root)},
    ).json()["proposals"]

    assert listed == []


def test_shipped_unsigned_proposal_is_refused(
    tmp_path: Path,
) -> None:
    root = _clone_of_malicious_repo(
        tmp_path / "repo",
        tmp_path / "marker",
    )

    proposal_id = _propose(
        root,
    )

    path = _proposal_file(
        root,
        proposal_id,
    )

    stored = json.loads(
        path.read_text(encoding="utf-8"),
    )

    del stored["signature"]

    path.write_text(
        json.dumps(stored),
        encoding="utf-8",
    )

    with pytest.raises(
        UntrustedStateError,
    ):
        ProposalStore(root).load(proposal_id)


def test_a_signed_proposal_cannot_be_moved_to_another_project(
    tmp_path: Path,
) -> None:
    first = _clone_of_malicious_repo(
        tmp_path / "first",
        tmp_path / "marker",
    )

    second = _clone_of_malicious_repo(
        tmp_path / "second",
        tmp_path / "marker",
    )

    proposal_id = _propose(
        first,
    )

    target = _proposal_file(
        second,
        proposal_id,
    )

    target.parent.mkdir(
        parents=True,
    )

    target.write_bytes(
        _proposal_file(first, proposal_id).read_bytes(),
    )

    with pytest.raises(
        UntrustedStateError,
    ):
        ProposalStore(second).load(proposal_id)


def test_tampered_snapshot_is_never_restored(
    tmp_path: Path,
) -> None:
    root = _clone_of_malicious_repo(
        tmp_path / "repo",
        tmp_path / "marker",
    )

    proposal_id = _propose(
        root,
    )

    applied = client.post(
        f"/api/v1/editing/proposals/{proposal_id}/apply",
        json={"repository_root": str(root), "validate_after": False},
    ).json()

    snapshot = (
        project_storage_directory(root)
        / "snapshots"
        / f"{applied['snapshot_id']}.json"
    )

    stored = json.loads(
        snapshot.read_text(encoding="utf-8"),
    )

    stored["files"][0]["content"] = "import os\nos.system('echo owned')\n"

    snapshot.write_text(
        json.dumps(stored),
        encoding="utf-8",
    )

    response = client.post(
        f"/api/v1/editing/proposals/{proposal_id}/rollback",
        json={"repository_root": str(root)},
    )

    assert response.status_code == 403

    assert (root / "app.py").read_bytes() == b"print(2)\n"


def test_linked_validation_file_is_refused(
    tmp_path: Path,
) -> None:
    root = _clone_of_malicious_repo(
        tmp_path / "repo",
        tmp_path / "marker",
    )

    outside = tmp_path / "outside.json"

    outside.write_text(
        "precious",
        encoding="utf-8",
    )

    link = project_storage_directory(root) / "validation.json"

    link.unlink()

    try:
        os.symlink(
            outside,
            link,
        )

    except (OSError, NotImplementedError):
        pytest.skip(
            "Creating symlinks is not permitted on this system.",
        )

    response = client.put(
        "/api/v1/editing/validation",
        json={
            "repository_root": str(root),
            "config": {"commands": []},
        },
    )

    assert response.status_code == 400

    assert outside.read_text(encoding="utf-8") == "precious"
