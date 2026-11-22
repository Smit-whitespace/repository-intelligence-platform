"""HTTP tests for the Workspace endpoints, using the real wiring."""

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
    metadata_path = project_metadata_path(
        tmp_path,
    )

    metadata_path.parent.mkdir(
        parents=True,
    )

    metadata_path.write_bytes(
        b"{}",
    )

    (tmp_path / "main.py").write_bytes(
        b"class App:\n    def run(self):\n        return 'ok'\n",
    )

    (tmp_path / "blob.bin").write_bytes(
        b"\x00\x01\x02",
    )

    return tmp_path


def _get(
    endpoint: str,
    root: Path,
    **params: object,
):
    return client.get(
        f"/api/v1/workspace/{endpoint}",
        params={
            "root_directory": str(
                root,
            ),
            **params,
        },
    )


def test_read_file(
    project: Path,
) -> None:
    response = _get(
        "file",
        project,
        path="main.py",
        start_line=2,
        end_line=2,
    )

    assert response.status_code == 200

    assert response.json()["content"] == "    def run(self):\n"


def test_tree_text_symbols_and_semantic(
    project: Path,
) -> None:
    tree = _get("tree", project)

    assert tree.status_code == 200

    assert "main.py" in [entry["path"] for entry in tree.json()["entries"]]

    text = _get("search/text", project, query="return")

    assert text.json()["matches"][0]["line"] == 3

    symbols = _get("symbols", project, query="App.run")

    assert symbols.json()["symbols"][0]["kind"] == "method"

    semantic = _get("search/semantic", project, query="run the app")

    assert semantic.status_code == 200

    assert semantic.json() == {
        "indexed": False,
        "hits": [],
    }


@pytest.mark.parametrize(
    ("params", "status_code"),
    [
        ({"path": "../escape.txt"}, 400),
        ({"path": ".git/config"}, 400),
        ({"path": "missing.py"}, 404),
        ({"path": "blob.bin"}, 415),
        ({"path": "main.py", "start_line": 0}, 400),
    ],
)
def test_read_file_error_statuses(
    project: Path,
    params: dict,
    status_code: int,
) -> None:
    response = _get(
        "file",
        project,
        **params,
    )

    assert response.status_code == status_code

    assert "detail" in response.json()


def test_unregistered_root_is_forbidden(
    tmp_path: Path,
) -> None:
    response = _get(
        "tree",
        tmp_path,
    )

    assert response.status_code == 403


def test_invalid_symbol_match_mode_is_a_validation_error(
    project: Path,
) -> None:
    response = _get(
        "symbols",
        project,
        query="App",
        match="fuzzy",
    )

    assert response.status_code == 422
