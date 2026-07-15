"""API contract certification tests."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.dependencies.providers import (
    get_editing_service,
)
from app.editing.exceptions import SnapshotNotFoundError
from app.main import app


class SnapshotMissingEditingService:
    """Editing service that raises a missing snapshot error."""

    def rollback(
        self,
        repository_root: Path,
        snapshot_id: str,
    ) -> None:
        """Raise the domain error surfaced by a missing snapshot."""

        raise SnapshotNotFoundError(
            "Snapshot not found.",
        )


def test_openapi_contract_metadata() -> None:
    """OpenAPI should expose stable operation metadata and responses."""

    schema = app.openapi()

    operations = {
        (
            method.upper(),
            path,
        ): operation
        for path, methods in schema[
            "paths"
        ].items()
        for method, operation in methods.items()
    }

    expected_operation_ids = {
        (
            "GET",
            "/api/v1/health",
        ): "getHealth",
        (
            "POST",
            "/api/v1/projects/open",
        ): "openProject",
        (
            "GET",
            "/api/v1/projects/info",
        ): "getProjectInfo",
        (
            "GET",
            "/api/v1/repository/index",
        ): "getRepositoryIndex",
        (
            "GET",
            "/api/v1/repository/scan",
        ): "scanRepository",
        (
            "GET",
            "/api/v1/repository/summary",
        ): "getRepositorySummary",
        (
            "POST",
            "/api/v1/chat",
        ): "chat",
        (
            "GET",
            "/api/v1/chat/stream",
        ): "streamChat",
        (
            "GET",
            "/api/v1/models",
        ): "listModels",
        (
            "GET",
            "/api/v1/settings/model",
        ): "getActiveModel",
        (
            "PUT",
            "/api/v1/settings/model",
        ): "updateActiveModel",
        (
            "GET",
            "/api/v1/system/status",
        ): "getSystemStatus",
        (
            "GET",
            "/api/v1/system/capabilities",
        ): "getSystemCapabilities",
        (
            "GET",
            "/api/v1/system/version",
        ): "getSystemVersion",
        (
            "POST",
            "/api/v1/editing/edit",
        ): "planEdit",
        (
            "POST",
            "/api/v1/editing/apply",
        ): "applyChangeSet",
        (
            "POST",
            "/api/v1/editing/rollback",
        ): "rollbackChangeSet",
    }

    for key, operation_id in expected_operation_ids.items():
        assert (
            operations[key]["operationId"]
            == operation_id
        )

        assert operations[key]["summary"]
        assert operations[key]["description"]

    assert (
        "ApplyResponse"
        in schema["components"]["schemas"]
    )

    assert (
        operations[
            (
                "POST",
                "/api/v1/editing/apply",
            )
        ]["responses"]["200"]["description"]
        == "Generated snapshot identifier for rollback."
    )

    assert (
        "text/event-stream"
        in operations[
            (
                "GET",
                "/api/v1/chat/stream",
            )
        ]["responses"]["200"]["content"]
    )


def test_repository_error_response_is_documented_shape() -> None:
    """Repository scan errors should return JSON detail with HTTP 400."""

    client = TestClient(
        app,
    )

    response = client.get(
        "/api/v1/repository/index",
        params={
            "root_directory": "Z:/local-openclaw/does-not-exist",
        },
    )

    assert (
        response.status_code
        == 400
    )

    assert (
        "detail"
        in response.json()
    )


def test_project_not_found_response_is_documented_shape(
    tmp_path: Path,
) -> None:
    """Missing project metadata should return JSON detail with HTTP 404."""

    client = TestClient(
        app,
    )

    response = client.get(
        "/api/v1/projects/info",
        params={
            "root_directory": str(
                tmp_path,
            ),
        },
    )

    assert (
        response.status_code
        == 404
    )

    assert response.json() == {
        "detail": f"Project metadata not found: {tmp_path / '.local_openclaw'}",
    }


def test_snapshot_not_found_response_is_documented_shape() -> None:
    """Missing rollback snapshots should return JSON detail with HTTP 404."""

    app.dependency_overrides[
        get_editing_service
    ] = lambda: SnapshotMissingEditingService()

    client = TestClient(
        app,
    )

    response = client.post(
        "/api/v1/editing/rollback",
        json={
            "repository_root": ".",
            "snapshot_id": "missing-snapshot",
        },
    )

    app.dependency_overrides.clear()

    assert (
        response.status_code
        == 404
    )

    assert response.json() == {
        "detail": "Snapshot not found.",
    }
