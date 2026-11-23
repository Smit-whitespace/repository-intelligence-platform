"""HTTP tests for the proposal and validation endpoints (real wiring)."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.storage.locations import project_metadata_path
from app.main import app

client = TestClient(
    app,
)


@pytest.fixture
def project(
    tmp_path: Path,
) -> Path:
    root = tmp_path / "repo"

    metadata_path = project_metadata_path(
        root,
    )

    metadata_path.parent.mkdir(
        parents=True,
    )

    metadata_path.write_bytes(
        b"{}",
    )

    (root / "app.py").write_bytes(
        b"VALUE = 1\n",
    )

    return root


def _propose(
    root: Path,
) -> dict:
    response = client.post(
        "/api/v1/editing/proposals",
        json={
            "repository_root": str(root),
            "description": "bump VALUE",
            "edits": [
                {
                    "path": "app.py",
                    "search": "VALUE = 1",
                    "replace": "VALUE = 2",
                },
            ],
        },
    )

    assert response.status_code == 200, response.text

    return response.json()


def test_propose_review_apply_rollback(
    project: Path,
) -> None:
    proposal = _propose(
        project,
    )

    proposal_id = proposal["proposal_id"]

    assert proposal["status"] == "pending"

    assert "+VALUE = 2" in proposal["diff"]

    assert "change_set" not in proposal

    listed = client.get(
        "/api/v1/editing/proposals",
        params={"root_directory": str(project)},
    ).json()["proposals"]

    assert [item["proposal_id"] for item in listed] == [
        proposal_id,
    ]

    fetched = client.get(
        f"/api/v1/editing/proposals/{proposal_id}",
        params={"root_directory": str(project)},
    )

    assert fetched.json()["description"] == "bump VALUE"

    applied = client.post(
        f"/api/v1/editing/proposals/{proposal_id}/apply",
        json={
            "repository_root": str(project),
            "validate_after": False,
        },
    )

    assert applied.json()["status"] == "applied"

    assert applied.json()["validation"] is None

    assert (project / "app.py").read_bytes() == b"VALUE = 2\n"

    again = client.post(
        f"/api/v1/editing/proposals/{proposal_id}/apply",
        json={"repository_root": str(project)},
    )

    assert again.status_code == 409

    rolled_back = client.post(
        f"/api/v1/editing/proposals/{proposal_id}/rollback",
        json={"repository_root": str(project)},
    )

    assert rolled_back.json()["status"] == "rolled_back"

    assert (project / "app.py").read_bytes() == b"VALUE = 1\n"


def test_error_statuses(
    project: Path,
    tmp_path: Path,
) -> None:
    missing = client.get(
        f"/api/v1/editing/proposals/{'0' * 32}",
        params={"root_directory": str(project)},
    )

    assert missing.status_code == 404

    bad_edit = client.post(
        "/api/v1/editing/proposals",
        json={
            "repository_root": str(project),
            "edits": [
                {"path": "app.py", "search": "nope", "replace": "x"},
            ],
        },
    )

    assert bad_edit.status_code == 400

    assert "was not found" in bad_edit.json()["detail"]

    unregistered = client.get(
        "/api/v1/editing/proposals",
        params={"root_directory": str(tmp_path)},
    )

    assert unregistered.status_code == 403


def test_validation_config_and_run(
    project: Path,
) -> None:
    empty = client.get(
        "/api/v1/editing/validation",
        params={"root_directory": str(project)},
    )

    assert empty.json() == {
        "commands": [],
        "trusted": True,
    }

    saved = client.put(
        "/api/v1/editing/validation",
        json={
            "repository_root": str(project),
            "config": {
                "commands": [
                    {
                        "name": "import",
                        "argv": [
                            sys.executable,
                            "-c",
                            "import app; print(app.VALUE)",
                        ],
                    },
                ],
            },
        },
    )

    assert saved.status_code == 200

    report = client.post(
        "/api/v1/editing/validation/run",
        json={"repository_root": str(project)},
    ).json()

    assert report["ran"] is True

    assert report["passed"] is True

    assert report["results"][0]["output"].strip() == "1"
