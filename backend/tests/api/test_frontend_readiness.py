"""Frontend readiness API tests."""

import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.routes import models as model_routes
from app.api.routes import system as system_routes
from app.main import app


class FakeOllamaClient:
    """Fake Ollama client."""

    def list(
        self,
    ) -> SimpleNamespace:
        """Return mixed model shapes."""

        return SimpleNamespace(
            models=[
                SimpleNamespace(
                    model="qwen3.6",
                ),
                {
                    "name": "llama3.2",
                },
            ],
        )


def test_list_models_normalizes_provider_models(
    monkeypatch,
) -> None:
    """Model listing should hide provider-specific response details."""

    monkeypatch.setattr(
        model_routes,
        "_ollama_client",
        lambda: FakeOllamaClient(),
    )

    client = TestClient(
        app,
    )

    response = client.get(
        "/api/v1/models",
    )

    assert (
        response.status_code
        == 200
    )

    assert response.json() == {
        "models": [
            {
                "provider": "ollama",
                "name": "llama3.2",
            },
            {
                "provider": "ollama",
                "name": "qwen3.6",
            },
        ],
    }


def test_get_active_model_returns_the_resolved_chat_model(
    model_config_path: Path,
) -> None:
    """Active model is what chat resolves to, from the configuration."""

    client = TestClient(
        app,
    )

    response = client.get(
        "/api/v1/settings/model",
    )

    assert (
        response.status_code
        == 200
    )

    assert response.json() == {
        "active_provider": "ollama",
        "active_model": "qwen3:8b",
    }


def test_update_active_model_saves_the_primary_model(
    monkeypatch,
    model_config_path: Path,
) -> None:
    """Choosing an installed model saves it as the primary model."""

    monkeypatch.setattr(
        model_routes,
        "_ollama_client",
        lambda: FakeOllamaClient(),
    )

    client = TestClient(
        app,
    )

    response = client.put(
        "/api/v1/settings/model",
        json={
            "model": "llama3.2",
        },
    )

    assert (
        response.status_code
        == 200
    )

    assert response.json() == {
        "active_provider": "ollama",
        "active_model": "llama3.2",
    }

    saved = json.loads(
        model_config_path.read_text(
            encoding="utf-8",
        ),
    )

    assert saved["primary"] == {
        "provider": "ollama",
        "model": "llama3.2",
    }

    # The next request sees the new model without a restart.
    assert client.get("/api/v1/settings/model").json()["active_model"] == (
        "llama3.2"
    )


def test_update_active_model_rejects_unknown_model(
    monkeypatch,
) -> None:
    """Unknown models should be rejected."""

    monkeypatch.setattr(
        model_routes,
        "_ollama_client",
        lambda: FakeOllamaClient(),
    )

    client = TestClient(
        app,
    )

    response = client.put(
        "/api/v1/settings/model",
        json={
            "model": "missing",
        },
    )

    assert (
        response.status_code
        == 400
    )


def test_system_status_returns_frontend_startup_information(
    monkeypatch,
    model_config_path: Path,
) -> None:
    """System status should expose frontend startup fields."""

    monkeypatch.setattr(
        system_routes,
        "_installed_models",
        lambda: [],
    )
    client = TestClient(
        app,
    )

    response = client.get(
        "/api/v1/system/status",
    )

    assert (
        response.status_code
        == 200
    )

    assert response.json() == {
        "backend_health": "healthy",
        "provider_connectivity": "available",
        "active_provider": "ollama",
        "active_model": "qwen3:8b",
        "project_status": "not_loaded",
        "repository_status": "not_loaded",
        "indexing_state": "available",
    }


def test_system_capabilities_returns_feature_flags() -> None:
    """System capabilities should expose frontend feature flags."""

    client = TestClient(
        app,
    )

    response = client.get(
        "/api/v1/system/capabilities",
    )

    assert (
        response.status_code
        == 200
    )

    assert response.json() == {
        "streaming": True,
        "retrieval": True,
        "editing": True,
        "snapshots": True,
        "rollback": True,
        "providers": [
            "ollama",
        ],
    }


def test_system_version_returns_rip_branding() -> None:
    """System version should expose RIP branding."""

    client = TestClient(
        app,
    )

    response = client.get(
        "/api/v1/system/version",
    )

    assert (
        response.status_code
        == 200
    )

    assert response.json() == {
        "application_name": "Repository Intelligence Platform (RIP)",
        "application_version": "0.1.0",
        "api_version": "v1",
        "backend_version": "0.1.0",
    }
