"""Model configuration schema.

Three levels for generation, plus embeddings:

1. ``primary`` (required): the default for every generation operation.
2. ``capabilities`` (optional): e.g. a different model for ``edit``.
3. ``tasks`` (optional, advanced): e.g. a model for one specific step.

``embedding`` is configured separately: embedding models produce vectors,
not text, and changing one invalidates the index (see indexing's
compatibility check), so it never follows the primary model.

Providers are named entries; models refer to them by name. API keys are
never stored here, only the *name* of the environment variable that
holds one.
"""

import re
from enum import StrEnum
from typing import Any
from urllib.parse import urlsplit

from pydantic import BaseModel
from pydantic import Field
from pydantic import SerializerFunctionWrapHandler
from pydantic import model_serializer
from pydantic import model_validator


class ProviderType(StrEnum):
    """Wire protocol a provider speaks."""

    OLLAMA = "ollama"
    """Local Ollama server (chat and embeddings)."""

    OPENAI_COMPATIBLE = "openai_compatible"
    """Any ``/v1/chat/completions`` + ``/v1/embeddings`` API: OpenAI,
    OpenRouter, LM Studio, vLLM, Gemini's OpenAI-compatible endpoint."""

    ANTHROPIC = "anthropic"
    """Anthropic's Messages API (chat only; no embeddings endpoint)."""


_API_KEY_ENV_PATTERN = re.compile(
    r"[A-Z][A-Z0-9_]*_API_KEY",
)

_LOOPBACK_HOSTS = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "::1",
    },
)

GENERATION_PROVIDER_TYPES = frozenset(
    ProviderType,
)

EMBEDDING_PROVIDER_TYPES = frozenset(
    {
        ProviderType.OLLAMA,
        ProviderType.OPENAI_COMPATIBLE,
    },
)


class Capability(StrEnum):
    """Major capability a model can be assigned to."""

    CHAT = "chat"

    EDIT = "edit"


class Task(StrEnum):
    """A specific generation step that RIP performs.

    Only steps that exist in code are listed, so the advanced level never
    offers settings that do nothing.
    """

    CHAT_ANSWER = "chat.answer"
    """Answering a repository question in chat."""

    EDIT_PLAN = "edit.plan"
    """Writing search/replace edits from an instruction."""


TASK_CAPABILITY: dict[Task, Capability] = {
    Task.CHAT_ANSWER: Capability.CHAT,
    Task.EDIT_PLAN: Capability.EDIT,
}
"""The capability each task belongs to (its level-2 fallback)."""


class ProviderConfig(BaseModel):
    """How to reach one model provider."""

    type: ProviderType

    base_url: str | None = Field(
        default=None,
        description="API base URL. Required for openai_compatible; "
        "optional for the others (their standard endpoint is used).",
        examples=[
            "https://api.openai.com/v1",
        ],
    )

    api_key_env: str | None = Field(
        default=None,
        description="Name of the environment variable holding the API "
        "key. The key itself is never stored or returned.",
        examples=[
            "OPENAI_API_KEY",
        ],
    )

    timeout_seconds: float = Field(
        default=120.0,
        gt=0,
    )

    @model_validator(
        mode="after",
    )
    def _check_key_handling(
        self,
    ) -> "ProviderConfig":
        """Keep a configuration from turning into a secret-exfiltration tool.

        The API has no authentication beyond accepting only local Host
        headers, so a local process could otherwise point ``api_key_env``
        at any secret (``AWS_SECRET_ACCESS_KEY``) and ``base_url`` at its
        own server. Only API-key variables are accepted, and a key is
        never sent to a non-local server without TLS.
        """

        if self.api_key_env is not None and not _API_KEY_ENV_PATTERN.fullmatch(
            self.api_key_env,
        ):
            raise ValueError(
                "api_key_env must name an API key variable ending in "
                "_API_KEY (for example OPENAI_API_KEY); other environment "
                "variables are never read.",
            )

        if self.api_key_env and self.base_url:
            url = urlsplit(
                self.base_url,
            )

            if url.scheme != "https" and url.hostname not in _LOOPBACK_HOSTS:
                raise ValueError(
                    "base_url must use https:// when an API key is sent to "
                    "a server other than this machine.",
                )

        return self

    @model_validator(
        mode="after",
    )
    def _check_required_fields(
        self,
    ) -> "ProviderConfig":
        if self.type is ProviderType.OPENAI_COMPATIBLE and not self.base_url:
            raise ValueError(
                "openai_compatible providers need a base_url, e.g. "
                "https://api.openai.com/v1",
            )

        if self.type is ProviderType.ANTHROPIC and not self.api_key_env:
            raise ValueError(
                "anthropic providers need api_key_env, e.g. ANTHROPIC_API_KEY",
            )

        return self


class ModelRef(BaseModel):
    """A model on a named provider."""

    provider: str = Field(
        min_length=1,
        examples=[
            "ollama",
        ],
    )

    model: str = Field(
        min_length=1,
        examples=[
            "qwen3:8b",
        ],
    )

    think: bool | None = Field(
        default=None,
        description="Ollama generation models only. false turns off a "
        "reasoning model's thinking: much faster answers (qwen3:8b chat: "
        "19 s instead of 55 s) at some cost in precision. true forces it; "
        "unset uses the model's default.",
    )

    @model_serializer(
        mode="wrap",
    )
    def _omit_unset_think(
        self,
        handler: SerializerFunctionWrapHandler,
    ) -> dict[str, Any]:
        # Keep saved files and API responses as they were for everyone
        # who never sets it.
        data: dict[str, Any] = handler(self)

        if self.think is None:
            data.pop(
                "think",
                None,
            )

        return data


class ModelConfiguration(BaseModel):
    """The complete model configuration."""

    version: int = 1

    providers: dict[str, ProviderConfig]

    primary: ModelRef

    capabilities: dict[Capability, ModelRef] = Field(
        default_factory=dict,
    )

    tasks: dict[Task, ModelRef] = Field(
        default_factory=dict,
    )

    embedding: ModelRef

    @model_validator(
        mode="after",
    )
    def _check_references(
        self,
    ) -> "ModelConfiguration":
        references = [
            ("primary", self.primary),
            ("embedding", self.embedding),
            *(
                (f"capabilities.{capability.value}", ref)
                for capability, ref in self.capabilities.items()
            ),
            *(
                (f"tasks.{task.value}", ref)
                for task, ref in self.tasks.items()
            ),
        ]

        for location, ref in references:
            if ref.provider not in self.providers:
                raise ValueError(
                    f"{location} uses provider '{ref.provider}', which is "
                    "not defined under providers.",
                )

            # Refused, not ignored: a setting that silently does nothing
            # would leave someone wondering why answers are still slow.
            if ref.think is not None and (
                location == "embedding"
                or self.providers[ref.provider].type is not ProviderType.OLLAMA
            ):
                raise ValueError(
                    f"{location} sets 'think', which only applies to Ollama "
                    "generation models. Remove it.",
                )

        embedding_type = self.providers[self.embedding.provider].type

        if embedding_type not in EMBEDDING_PROVIDER_TYPES:
            raise ValueError(
                f"Provider type '{embedding_type.value}' has no embeddings "
                "API; choose an ollama or openai_compatible provider for "
                "embedding.",
            )

        return self
