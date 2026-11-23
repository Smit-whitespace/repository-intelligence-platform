"""HTTP tests for the model configuration endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(
    app,
)

HOSTED_CONFIGURATION = {
    "providers": {
        "ollama": {"type": "ollama"},
        "claude": {
            "type": "anthropic",
            "api_key_env": "RIP_TEST_ANTHROPIC_API_KEY",
        },
    },
    "primary": {"provider": "ollama", "model": "qwen3:8b"},
    "capabilities": {
        "chat": {"provider": "claude", "model": "claude-opus-5-5"},
    },
    "embedding": {"provider": "ollama", "model": "nomic-embed-text"},
}


def test_defaults_are_reported_as_unsaved(
    model_config_path: Path,
) -> None:
    response = client.get(
        "/api/v1/models/configuration",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["saved"] is False

    assert body["path"] == str(model_config_path)

    assert body["configuration"]["primary"] == {
        "provider": "ollama",
        "model": "qwen3:8b",
    }

    assert body["api_keys_present"] == {}


def test_saved_configuration_takes_effect_on_the_next_request(
    model_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "RIP_TEST_ANTHROPIC_API_KEY",
        raising=False,
    )

    saved = client.put(
        "/api/v1/models/configuration",
        json=HOSTED_CONFIGURATION,
    )

    assert saved.status_code == 200

    assert saved.json()["saved"] is True

    assert saved.json()["api_keys_present"] == {
        "claude": False,
    }

    assert model_config_path.is_file()

    effective = {
        model["operation"]: model
        for model in client.get("/api/v1/models/effective").json()["models"]
    }

    assert effective["chat.answer"]["provider"] == "claude"

    assert effective["chat.answer"]["source"] == "capability"

    assert effective["edit"]["source"] == "primary"

    assert effective["embedding"]["model"] == "nomic-embed-text"

    assert client.get("/api/v1/settings/model").json() == {
        "active_provider": "claude",
        "active_model": "claude-opus-5-5",
    }


def test_api_key_values_are_never_returned(
    model_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "RIP_TEST_ANTHROPIC_API_KEY",
        "sk-ant-very-secret",
    )

    response = client.put(
        "/api/v1/models/configuration",
        json=HOSTED_CONFIGURATION,
    )

    assert response.json()["api_keys_present"] == {
        "claude": True,
    }

    assert "sk-ant-very-secret" not in response.text

    assert "sk-ant-very-secret" not in model_config_path.read_text(
        encoding="utf-8",
    )


def test_chat_with_a_missing_key_is_a_clear_error(
    model_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "RIP_TEST_ANTHROPIC_API_KEY",
        raising=False,
    )

    client.put(
        "/api/v1/models/configuration",
        json=HOSTED_CONFIGURATION,
    )

    response = client.post(
        "/api/v1/chat",
        json={
            "query": "Where are edits applied?",
        },
    )

    assert response.status_code == 400

    assert "RIP_TEST_ANTHROPIC_API_KEY" in response.json()["detail"]


def test_invalid_configuration_is_rejected_and_not_saved(
    model_config_path: Path,
) -> None:
    response = client.put(
        "/api/v1/models/configuration",
        json={
            **HOSTED_CONFIGURATION,
            "primary": {"provider": "nowhere", "model": "x"},
        },
    )

    assert response.status_code == 422

    assert not model_config_path.exists()


def test_workspace_tools_keep_working_without_an_embedding_key(
    model_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Reading files never needs the embedding provider."""

    from app.core.storage.locations import project_metadata_path

    monkeypatch.delenv(
        "RIP_TEST_OPENAI_API_KEY",
        raising=False,
    )

    client.put(
        "/api/v1/models/configuration",
        json={
            "providers": {
                "ollama": {"type": "ollama"},
                "openai": {
                    "type": "openai_compatible",
                    "base_url": "https://api.openai.com/v1",
                    "api_key_env": "RIP_TEST_OPENAI_API_KEY",
                },
            },
            "primary": {"provider": "ollama", "model": "qwen3:8b"},
            "embedding": {"provider": "openai", "model": "text-embedding-3-small"},
        },
    )

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

    (root / "main.py").write_bytes(
        b"print('hi')\n",
    )

    response = client.get(
        "/api/v1/workspace/file",
        params={
            "root_directory": str(root),
            "path": "main.py",
        },
    )

    assert response.status_code == 200


def test_config_changes_made_outside_the_app_apply_to_the_next_request(
    model_config_path: Path,
) -> None:
    """Another process (an MCP server) or a person may edit the file."""

    import json

    assert client.get("/api/v1/settings/model").json()["active_model"] == (
        "qwen3:8b"
    )

    model_config_path.write_text(
        json.dumps(
            {
                "providers": {"ollama": {"type": "ollama"}},
                "primary": {"provider": "ollama", "model": "llama3.2"},
                "embedding": {"provider": "ollama", "model": "nomic-embed-text"},
            },
        ),
        encoding="utf-8",
    )

    assert client.get("/api/v1/settings/model").json()["active_model"] == (
        "llama3.2"
    )
