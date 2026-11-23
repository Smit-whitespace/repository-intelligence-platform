"""Tests for model configuration, resolution and storage."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config.models import OllamaSettings
from app.llm import resolver as resolver_module
from app.llm.config import (
    Capability,
    ModelConfiguration,
    ModelRef,
    ProviderConfig,
    ProviderType,
    Task,
)
from app.llm.exceptions import (
    ModelCompatibilityError,
    ModelConfigurationError,
)
from app.llm.resolver import (
    ModelResolver,
    ModelSource,
)
from app.llm.store import (
    ModelConfigStore,
    configuration_from_ollama_settings,
)


def _configuration(
    **overrides: object,
) -> ModelConfiguration:
    data: dict = {
        "providers": {
            "local": {"type": "ollama"},
            "openai": {
                "type": "openai_compatible",
                "base_url": "https://api.openai.com/v1",
                "api_key_env": "OPENAI_API_KEY",
            },
            "claude": {
                "type": "anthropic",
                "api_key_env": "ANTHROPIC_API_KEY",
            },
        },
        "primary": {"provider": "local", "model": "qwen3:8b"},
        "embedding": {"provider": "local", "model": "nomic-embed-text"},
    }

    data.update(
        overrides,
    )

    return ModelConfiguration.model_validate(
        data,
    )


# --- Schema validation ---------------------------------------------------


def test_minimal_configuration_needs_only_primary_and_embedding() -> None:
    configuration = _configuration()

    assert configuration.capabilities == {}

    assert configuration.tasks == {}


def test_unknown_provider_reference_is_rejected_with_its_location() -> None:
    with pytest.raises(
        ValidationError,
        match="capabilities.edit uses provider 'missing'",
    ):
        _configuration(
            capabilities={
                "edit": {"provider": "missing", "model": "x"},
            },
        )


def test_embedding_must_use_a_provider_with_an_embeddings_api() -> None:
    with pytest.raises(
        ValidationError,
        match="has no embeddings API",
    ):
        _configuration(
            embedding={"provider": "claude", "model": "claude-opus-5-5"},
        )


@pytest.mark.parametrize(
    ("provider", "message"),
    [
        ({"type": "openai_compatible"}, "need a base_url"),
        ({"type": "anthropic"}, "need api_key_env"),
    ],
)
def test_provider_required_fields(
    provider: dict,
    message: str,
) -> None:
    with pytest.raises(
        ValidationError,
        match=message,
    ):
        ProviderConfig.model_validate(
            provider,
        )


def test_unknown_task_and_capability_names_are_rejected() -> None:
    with pytest.raises(
        ValidationError,
    ):
        _configuration(
            tasks={
                "planning": {"provider": "local", "model": "x"},
            },
        )


# --- Resolution hierarchy ------------------------------------------------


def test_everything_inherits_the_primary_model_by_default() -> None:
    resolver = ModelResolver(
        _configuration(),
    )

    chat = resolver.for_task(
        Task.CHAT_ANSWER,
    )

    assert (chat.provider, chat.model, chat.source) == (
        "local",
        "qwen3:8b",
        ModelSource.PRIMARY,
    )

    edit = resolver.for_capability(
        Capability.EDIT,
    )

    assert edit.source is ModelSource.PRIMARY


def test_capability_override_beats_primary() -> None:
    resolver = ModelResolver(
        _configuration(
            capabilities={
                "chat": {"provider": "claude", "model": "claude-opus-5-5"},
            },
        ),
    )

    chat = resolver.for_task(
        Task.CHAT_ANSWER,
    )

    assert (chat.provider, chat.model, chat.source) == (
        "claude",
        "claude-opus-5-5",
        ModelSource.CAPABILITY,
    )

    # Other capabilities still inherit the primary model.
    assert resolver.for_capability(Capability.EDIT).source is ModelSource.PRIMARY


def test_task_override_beats_capability_override() -> None:
    resolver = ModelResolver(
        _configuration(
            capabilities={
                "chat": {"provider": "claude", "model": "claude-opus-5-5"},
            },
            tasks={
                "chat.answer": {"provider": "openai", "model": "gpt-5"},
            },
        ),
    )

    chat = resolver.for_task(
        Task.CHAT_ANSWER,
    )

    assert (chat.provider, chat.source) == (
        "openai",
        ModelSource.TASK,
    )

    # The capability as a whole still reports its own override.
    assert resolver.for_capability(Capability.CHAT).provider == "claude"


def test_embedding_never_follows_the_primary_model() -> None:
    resolver = ModelResolver(
        _configuration(
            primary={"provider": "claude", "model": "claude-opus-5-5"},
        ),
    )

    embedding = resolver.for_embedding()

    assert (embedding.provider, embedding.model, embedding.source) == (
        "local",
        "nomic-embed-text",
        ModelSource.EMBEDDING,
    )


def test_incompatible_model_is_an_error_not_a_silent_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the chosen model cannot generate, resolution must not move on."""

    monkeypatch.setattr(
        resolver_module,
        "GENERATION_PROVIDER_TYPES",
        frozenset({ProviderType.ANTHROPIC}),
    )

    resolver = ModelResolver(
        _configuration(
            capabilities={
                "chat": {"provider": "local", "model": "qwen3:8b"},
            },
        ),
    )

    with pytest.raises(
        ModelCompatibilityError,
        match="cannot generate text",
    ):
        resolver.for_task(
            Task.CHAT_ANSWER,
        )


def test_effective_models_lists_every_operation() -> None:
    operations = [
        model.operation
        for model in ModelResolver(_configuration()).effective_models()
    ]

    assert operations == [
        "chat",
        "edit",
        "chat.answer",
        "edit.plan",
        "embedding",
    ]


# --- Storage -------------------------------------------------------------


def _store(
    path: Path,
) -> ModelConfigStore:
    return ModelConfigStore(
        path=path,
        defaults=configuration_from_ollama_settings(
            OllamaSettings(
                base_url="http://localhost:11434",
                chat_model="qwen3:8b",
                embedding_model="nomic-embed-text",
            ),
        ),
    )


def test_defaults_come_from_the_existing_ollama_settings(
    tmp_path: Path,
) -> None:
    store = _store(
        tmp_path / "models.json",
    )

    configuration = store.load()

    assert not store.exists()

    assert configuration.primary == ModelRef(
        provider="ollama",
        model="qwen3:8b",
    )

    assert configuration.embedding.model == "nomic-embed-text"

    assert configuration.providers["ollama"].base_url == "http://localhost:11434"


def test_save_and_load_round_trip(
    tmp_path: Path,
) -> None:
    path = tmp_path / "nested" / "models.json"

    store = _store(
        path,
    )

    configuration = _configuration(
        capabilities={
            "edit": {"provider": "claude", "model": "claude-opus-5-5"},
        },
    )

    store.save(
        configuration,
    )

    assert store.load() == configuration

    saved = json.loads(
        path.read_text(
            encoding="utf-8",
        ),
    )

    # Only the variable name is stored, never a key.
    assert saved["providers"]["claude"]["api_key_env"] == "ANTHROPIC_API_KEY"


def test_corrupt_file_is_a_clear_error(
    tmp_path: Path,
) -> None:
    path = tmp_path / "models.json"

    path.write_text(
        "{not json",
        encoding="utf-8",
    )

    with pytest.raises(
        ModelConfigurationError,
        match="Fix or delete the file",
    ):
        _store(path).load()


# --- Secret exfiltration guards (security review) -------------------------


@pytest.mark.parametrize(
    "variable",
    [
        "AWS_SECRET_ACCESS_KEY",
        "GITHUB_TOKEN",
        "PATH",
        "openai_api_key",
    ],
)
def test_only_api_key_variables_can_be_read(
    variable: str,
) -> None:
    with pytest.raises(
        ValidationError,
        match="must name an API key variable ending in _API_KEY",
    ):
        ProviderConfig(
            type=ProviderType.OPENAI_COMPATIBLE,
            base_url="https://api.example.test/v1",
            api_key_env=variable,
        )


def test_keys_are_never_sent_over_plain_http_to_other_machines() -> None:
    with pytest.raises(
        ValidationError,
        match="must use https://",
    ):
        ProviderConfig(
            type=ProviderType.OPENAI_COMPATIBLE,
            base_url="http://attacker.example/v1",
            api_key_env="OPENAI_API_KEY",
        )


@pytest.mark.parametrize(
    ("base_url", "api_key_env"),
    [
        ("http://localhost:1234/v1", "LMSTUDIO_API_KEY"),
        ("http://127.0.0.1:8000/v1", "LOCAL_API_KEY"),
        ("http://gpu-box.lan:11434/v1", None),
        ("https://api.openai.com/v1", "OPENAI_API_KEY"),
    ],
)
def test_reasonable_setups_are_accepted(
    base_url: str,
    api_key_env: str | None,
) -> None:
    ProviderConfig(
        type=ProviderType.OPENAI_COMPATIBLE,
        base_url=base_url,
        api_key_env=api_key_env,
    )
