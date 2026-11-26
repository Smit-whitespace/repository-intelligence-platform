"""The API token every REST request except /health must carry (ADR-0020)."""

import os
import stat
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.security.api_token import sign_in_url
from app.core.storage.secret_file import read_or_create_secret
from app.main import create_application
from tests.conftest import TEST_API_TOKEN

PROTECTED = [
    ("get", "/api/v1/system/version"),
    ("get", "/api/v1/models/effective"),
    ("post", "/api/v1/projects/open"),
    ("get", "/api/v1/workspace/file?root_directory=x&path=y"),
    ("post", "/api/v1/editing/proposals/0123456789abcdef0123456789abcdef/apply"),
    ("get", "/api/v1/chat/stream?query=hi"),
]


def _client_without_token() -> TestClient:
    client = TestClient(
        create_application(),
    )

    client.headers.pop(
        "Authorization",
    )

    return client


@pytest.mark.parametrize(
    ("method", "path"),
    PROTECTED,
)
def test_requests_without_the_token_are_refused(
    method: str,
    path: str,
) -> None:
    """Refused before any handler runs, so nothing is read or written."""

    response = getattr(
        _client_without_token(),
        method,
    )(
        path,
    )

    assert response.status_code == 401

    assert response.headers["WWW-Authenticate"] == "Bearer"

    assert "sign-in link" in response.json()["detail"]


@pytest.mark.parametrize(
    "authorization",
    [
        "Bearer wrong-token",
        f"Bearer {TEST_API_TOKEN}x",
        f"Basic {TEST_API_TOKEN}",
        TEST_API_TOKEN,
    ],
)
def test_a_wrong_token_or_scheme_is_refused(
    authorization: str,
) -> None:
    response = TestClient(
        create_application(),
        headers={
            "Authorization": authorization,
        },
    ).get(
        "/api/v1/system/version",
    )

    assert response.status_code == 401


def test_the_right_token_is_accepted() -> None:
    response = TestClient(
        create_application(),
    ).get(
        "/api/v1/system/version",
    )

    assert response.status_code == 200


def test_health_stays_open() -> None:
    """The app must tell "backend down" apart from "not signed in"."""

    response = _client_without_token().get(
        "/api/v1/health",
    )

    assert response.status_code == 200


def test_openapi_documents_the_bearer_scheme() -> None:
    schema = TestClient(
        create_application(),
    ).get(
        "/openapi.json",
    ).json()

    assert schema["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"


def test_sign_in_url_carries_the_token() -> None:
    assert sign_in_url() == f"http://localhost:5173/?token={TEST_API_TOKEN}"


def test_secret_file_is_created_once_and_reused(
    tmp_path: Path,
) -> None:
    path = tmp_path / "nested" / "api.token"

    first = read_or_create_secret(
        path,
        lambda: "first",
    )

    second = read_or_create_secret(
        path,
        lambda: "second",
    )

    assert (first, second) == ("first", "first")


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="POSIX file modes",
)
def test_secret_file_is_readable_only_by_its_owner(
    tmp_path: Path,
) -> None:
    path = tmp_path / "api.token"

    read_or_create_secret(
        path,
        lambda: "secret",
    )

    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
