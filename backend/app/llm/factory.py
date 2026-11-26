"""Build provider adapters from the model configuration.

API keys are read from the environment variable a provider names, when
the adapter is built. They are never written to the configuration file
or returned by the API.
"""

import os
from collections.abc import Callable, Sequence

from app.chat.ollama_provider import OllamaChatProvider
from app.chat.providers import ChatProvider
from app.core.config.models import OllamaSettings
from app.indexing.models import EmbeddingVector
from app.indexing.ollama_provider import OllamaEmbeddingProvider
from app.indexing.providers import EmbeddingProvider
from app.llm.config import (
    ModelConfiguration,
    ProviderConfig,
    ProviderType,
)
from app.llm.exceptions import ModelConfigurationError
from app.llm.providers.openai_compatible import (
    OpenAICompatibleChatProvider,
    OpenAICompatibleEmbeddingProvider,
)
from app.llm.resolver import EffectiveModel


def api_key_for(
    provider_name: str,
    provider: ProviderConfig,
) -> str | None:
    """Return the provider's API key, or None if it uses none.

    Raises ``ModelConfigurationError`` when the provider names a variable
    that is not set, saying exactly which one.
    """

    if not provider.api_key_env:
        return None

    value = os.environ.get(
        provider.api_key_env,
        "",
    ).strip()

    if not value:
        raise ModelConfigurationError(
            f"Provider '{provider_name}' needs an API key in the "
            f"environment variable {provider.api_key_env}, which is not set. "
            "Set it and restart RIP.",
        )

    return value


def build_chat_provider(
    configuration: ModelConfiguration,
    effective: EffectiveModel,
    ollama_settings: OllamaSettings,
) -> ChatProvider:
    """Create the chat adapter for a resolved model."""

    provider = configuration.providers[effective.provider]

    api_key = api_key_for(
        effective.provider,
        provider,
    )

    if provider.type is ProviderType.OLLAMA:
        return OllamaChatProvider(
            ollama_settings,
            model=effective.model,
            base_url=provider.base_url,
            think=effective.think,
            timeout_seconds=provider.timeout_seconds,
        )

    if provider.type is ProviderType.OPENAI_COMPATIBLE:
        assert provider.base_url is not None

        return OpenAICompatibleChatProvider(
            base_url=provider.base_url,
            model=effective.model,
            api_key=api_key,
            timeout_seconds=provider.timeout_seconds,
        )

    assert api_key is not None

    # Imported here, not at module level: the anthropic SDK takes about
    # three seconds to import, which every backend and MCP server start
    # would otherwise pay even when no Anthropic model is configured.
    from app.llm.providers.anthropic_provider import AnthropicChatProvider

    return AnthropicChatProvider(
        model=effective.model,
        api_key=api_key,
        base_url=provider.base_url,
        timeout_seconds=provider.timeout_seconds,
    )


def build_embedding_provider(
    configuration: ModelConfiguration,
    effective: EffectiveModel,
    ollama_settings: OllamaSettings,
) -> EmbeddingProvider:
    """Create the embedding adapter for the configured embedding model."""

    provider = configuration.providers[effective.provider]

    api_key = api_key_for(
        effective.provider,
        provider,
    )

    if provider.type is ProviderType.OLLAMA:
        return OllamaEmbeddingProvider(
            ollama_settings,
            model=effective.model,
            base_url=provider.base_url,
        )

    if provider.type is ProviderType.OPENAI_COMPATIBLE:
        assert provider.base_url is not None

        return OpenAICompatibleEmbeddingProvider(
            base_url=provider.base_url,
            model=effective.model,
            api_key=api_key,
            timeout_seconds=provider.timeout_seconds,
        )

    # The configuration validator rejects embedding providers without an
    # embeddings API, so this is unreachable with a validated config.
    raise ModelConfigurationError(
        f"Provider type '{provider.type.value}' has no embeddings API.",
    )


class LazyEmbeddingProvider(
    EmbeddingProvider,
):
    """Build the real embedding provider on first use.

    Services that merely hold a reference to an embedding provider (the
    workspace, through retrieval) must keep working when, say, a hosted
    embedding API key is missing. Only operations that actually embed
    report the configuration error.
    """

    def __init__(
        self,
        build: Callable[[], EmbeddingProvider],
        version: Callable[[], object] | None = None,
    ) -> None:
        """``version`` identifies the configuration; when it changes, the
        provider is rebuilt on next use."""

        self._build = build

        self._version = version

        self._provider: EmbeddingProvider | None = None

        self._built_for: object = None

    def _resolved(
        self,
    ) -> EmbeddingProvider:
        current = self._version() if self._version is not None else None

        if self._provider is None or current != self._built_for:
            self._provider = self._build()

            self._built_for = current

        return self._provider

    @property
    def identity(
        self,
    ) -> str:
        return self._resolved().identity

    def embed(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        return self._resolved().embed(
            texts,
        )
