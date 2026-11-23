"""The API rejects requests whose Host header is not a local name."""

from fastapi.testclient import TestClient

from app.main import app


def test_unknown_host_header_is_rejected() -> None:
    """Blocks DNS rebinding from a web page on another domain."""

    client = TestClient(
        app,
        base_url="http://attacker.example",
    )

    response = client.get(
        "/api/v1/health",
    )

    assert response.status_code == 400


def test_local_host_headers_are_accepted() -> None:
    for base_url in (
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ):
        client = TestClient(
            app,
            base_url=base_url,
        )

        assert client.get("/api/v1/health").status_code == 200
