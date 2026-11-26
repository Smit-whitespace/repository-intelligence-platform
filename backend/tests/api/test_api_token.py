"""The API token every REST request except /health must carry (ADR-0020)."""

import os
import stat
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient

from app.core.security.api_token import (
    SIGN_IN_CODE_TTL_SECONDS,
    redeem_sign_in_code,
    sign_in_url,
)
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


def _code_from(
    url: str,
) -> str:
    return parse_qs(
        urlsplit(
            url,
        ).query,
    )["code"][0]


def test_sign_in_link_carries_a_code_never_the_token() -> None:
    """Graphify P1: a token in the link sat in every kept log file."""

    url = sign_in_url()

    assert url.startswith("http://localhost:5173/?code=")

    assert TEST_API_TOKEN not in url


def test_the_configured_frontend_may_call_the_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Graphify: a custom LOC_SERVER_FRONTEND_URL got a sign-in link to an
    app whose browser requests the API then refused (CORS)."""

    from app import main

    monkeypatch.setattr(
        main.settings.server,
        "frontend_url",
        "http://localhost:3000/rip",
    )

    assert main.allowed_browser_origins() == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    response = TestClient(
        main.create_application(),
    ).options(
        "/api/v1/system/version",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


@pytest.mark.parametrize(
    "frontend_url",
    [
        "localhost:3000",
        "//localhost:3000",
        "ftp://localhost:3000",
        "http://",
        "http://localhost:abc",
        "http://localhost:99999",
    ],
)
def test_a_frontend_url_without_http_is_refused_at_startup(
    frontend_url: str,
) -> None:
    """It was silently left out of the allowed origins (Graphify on #6)."""

    from pydantic import ValidationError

    from app.core.config.models import ServerSettings

    with pytest.raises(
        ValidationError,
        match="must start with http:// or https://",
    ):
        ServerSettings(
            frontend_url=frontend_url,
        )


@pytest.mark.parametrize(
    ("frontend_url", "expected_origin"),
    [
        ("HTTP://LocalHost:80/rip", "http://localhost"),
        ("https://RIP.example.test:443", "https://rip.example.test"),
        ("http://user:secret@localhost:3000/", "http://localhost:3000"),
        ("http://[::1]:3000", "http://[::1]:3000"),
    ],
)
def test_the_configured_origin_is_written_the_way_browsers_send_it(
    monkeypatch: pytest.MonkeyPatch,
    frontend_url: str,
    expected_origin: str,
) -> None:
    """Browsers send a lowercase host, no default port and no userinfo,
    so the allow-list entry must too (Graphify on #6)."""

    from app import main

    monkeypatch.setattr(
        main.settings.server,
        "frontend_url",
        frontend_url,
    )

    assert main.allowed_browser_origins()[-1] == expected_origin


def test_a_sign_in_code_works_once() -> None:
    client = _client_without_token()

    code = _code_from(
        sign_in_url(),
    )

    first = client.post(
        "/api/v1/auth/sign-in",
        json={
            "code": code,
        },
    )

    second = client.post(
        "/api/v1/auth/sign-in",
        json={
            "code": code,
        },
    )

    assert first.status_code == 200

    assert first.json() == {
        "token": TEST_API_TOKEN,
    }

    assert second.status_code == 401

    assert "already used" in second.json()["detail"]


def test_a_new_link_replaces_the_previous_one() -> None:
    old = _code_from(
        sign_in_url(),
    )

    sign_in_url()

    assert redeem_sign_in_code(old) is None


def test_an_expired_or_wrong_code_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    code = _code_from(
        sign_in_url(),
    )

    assert redeem_sign_in_code("not-the-code") is None

    now = time.monotonic()

    monkeypatch.setattr(
        time,
        "monotonic",
        lambda: now + SIGN_IN_CODE_TTL_SECONDS + 1,
    )

    assert redeem_sign_in_code(code) is None


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
