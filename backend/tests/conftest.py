"""Test-wide configuration.

Runs before any test module imports the application, so settings are
built with these values.
"""

import os
import tempfile
from pathlib import Path

# FastAPI's TestClient sends "Host: testserver"; allow it in tests only.
os.environ["LOC_SERVER_ALLOWED_HOSTS"] = "localhost,127.0.0.1,testserver"

# Never read or write the developer's real ~/.local_openclaw/models.json.
# The file does not exist, so the LOC_OLLAMA_* defaults apply.
os.environ["LOC_MODEL_CONFIG_PATH"] = str(
    Path(tempfile.mkdtemp(prefix="rip-tests-")) / "models.json",
)


import pytest  # noqa: E402


@pytest.fixture
def model_config_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Give a test its own model configuration file and fresh caches.

    Returns the (not yet existing) path; ``apply_model_configuration``
    writes there, and every cached provider is rebuilt before and after.
    """

    from app.core.config.models import OllamaSettings
    from app.dependencies import providers
    from app.llm.store import (
        ModelConfigStore,
        configuration_from_ollama_settings,
    )

    path = tmp_path / "models.json"

    store = ModelConfigStore(
        path=path,
        defaults=configuration_from_ollama_settings(
            OllamaSettings(
                chat_model="qwen3:8b",
                embedding_model="nomic-embed-text",
            ),
        ),
    )

    def clear_caches() -> None:
        for cached in (
            providers.get_model_resolver,
            providers.get_chat_provider,
            providers.get_chat_service,
            providers.get_embedding_provider,
            providers.get_repository_indexer,
            providers.get_indexing_service,
            providers.get_retrieval_service,
            providers.get_project_initialization_service,
            providers.get_workspace_opener,
        ):
            cached.cache_clear()

    monkeypatch.setattr(
        providers,
        "get_model_config_store",
        lambda: store,
    )

    clear_caches()

    yield path

    clear_caches()
