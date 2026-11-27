"""Test-wide configuration.

Runs before any test module imports the application, so settings are
built with these values.
"""

import os
import tempfile
from pathlib import Path

# FastAPI's TestClient sends "Host: testserver"; allow it in tests only.
os.environ["RIP_SERVER_ALLOWED_HOSTS"] = "localhost,127.0.0.1,testserver"

# Never read or write the developer's real ~/.rip/models.json.
# The file does not exist, so the RIP_OLLAMA_* defaults apply.
_TEST_HOME = Path(tempfile.mkdtemp(prefix="rip-tests-"))

os.environ["RIP_MODEL_CONFIG_PATH"] = str(
    _TEST_HOME / "models.json",
)

# The key that signs proposals, snapshots and validation commands.
os.environ["RIP_INTEGRITY_KEY_PATH"] = str(
    _TEST_HOME / "integrity.key",
)

# The API token (ADR-0020): a known value, so tests can send it.
TEST_API_TOKEN = "rip-test-api-token"

(_TEST_HOME / "api.token").write_text(
    TEST_API_TOKEN,
    encoding="ascii",
)

os.environ["RIP_API_TOKEN_PATH"] = str(
    _TEST_HOME / "api.token",
)


import pytest  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

_original_test_client_init = TestClient.__init__


def _test_client_with_token(
    self: TestClient,
    *args: object,
    headers: dict[str, str] | None = None,
    **kwargs: object,
) -> None:
    """Every test client sends the API token unless a test overrides it.

    Tests of the token itself pass their own Authorization header or
    remove it from ``client.headers``.
    """

    _original_test_client_init(
        self,
        *args,
        headers={
            "Authorization": f"Bearer {TEST_API_TOKEN}",
            **(headers or {}),
        },
        **kwargs,
    )


TestClient.__init__ = _test_client_with_token  # type: ignore[method-assign]


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
            providers.get_proposal_service,
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
