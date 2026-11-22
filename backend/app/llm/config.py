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

from enum import StrEnum

from pydantic import BaseModel
from pydantic import Field
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


TASK_CAPABILITY: dict[Task, Capability] = {
    Task.CHAT_ANSWER: Capability.CHAT,
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

        embedding_type = self.providers[self.embedding.provider].type

        if embedding_type not in EMBEDDING_PROVIDER_TYPES:
            raise ValueError(
                f"Provider type '{embedding_type.value}' has no embeddings "
                "API; choose an ollama or openai_compatible provider for "
                "embedding.",
            )

        return self
