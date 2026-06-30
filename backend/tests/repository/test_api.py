"""Repository API tests."""

from pathlib import Path

import pytest
from httpx import ASGITransport
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_repository_summary_endpoint(
    tmp_path: Path,
) -> None:
    """Repository summary endpoint should succeed."""

    (tmp_path / "README.md").write_text(
        "hello",
        encoding="utf-8",
    )

    transport = ASGITransport(
        app=app,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/api/v1/repository/index",
            params={
                "root_directory": str(tmp_path),
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["summary"]["files"] == 1
    assert data["summary"]["directories"] == 0
    assert data["summary"]["total_size_bytes"] == 5

    assert len(data["entries"]) == 1