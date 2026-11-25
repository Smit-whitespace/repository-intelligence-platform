"""Model resolution.

For a generation task, the first configured level wins:

1. the task override,
2. the override for the task's capability,
3. the primary model.

The result says which level it came from, so the UI can show the
effective model and why. If the chosen model cannot perform the
operation, resolution raises ``ModelCompatibilityError``. It never moves
on to another level or provider: a misconfiguration is reported, not
papered over.
"""

from enum import StrEnum

from pydantic import BaseModel, Field

from app.llm.config import (
    GENERATION_PROVIDER_TYPES,
    TASK_CAPABILITY,
    Capability,
    ModelConfiguration,
    ModelRef,
    ProviderType,
    Task,
)
from app.llm.exceptions import ModelCompatibilityError


class ModelSource(StrEnum):
    """Which configuration level an effective model came from."""

    TASK = "task"

    CAPABILITY = "capability"

    PRIMARY = "primary"

    EMBEDDING = "embedding"


class EffectiveModel(BaseModel):
    """The model an operation will actually use, and why."""

    operation: str

    provider: str

    provider_type: ProviderType

    model: str

    source: ModelSource

    think: bool | None = Field(
        default=None,
        description="Whether the model thinks before answering (null: the model's default).",
    )


class ModelResolver:
    """Resolve which model each operation uses."""

    def __init__(
        self,
        configuration: ModelConfiguration,
    ) -> None:
        self._configuration = configuration

    @property
    def configuration(
        self,
    ) -> ModelConfiguration:
        return self._configuration

    def for_task(
        self,
        task: Task,
    ) -> EffectiveModel:
        """Resolve the model for a generation task."""

        task_override = self._configuration.tasks.get(
            task,
        )

        if task_override is not None:
            return self._generation(
                task.value,
                task_override,
                ModelSource.TASK,
            )

        return self._resolve_capability(
            TASK_CAPABILITY[task],
            operation=task.value,
        )

    def for_capability(
        self,
        capability: Capability,
    ) -> EffectiveModel:
        """Resolve the model for a capability as a whole."""

        return self._resolve_capability(
            capability,
            operation=capability.value,
        )

    def for_embedding(
        self,
    ) -> EffectiveModel:
        """Resolve the embedding model (its own configuration only)."""

        ref = self._configuration.embedding

        return EffectiveModel(
            operation="embedding",
            provider=ref.provider,
            provider_type=self._provider_type(
                ref,
            ),
            model=ref.model,
            source=ModelSource.EMBEDDING,
        )

    def effective_models(
        self,
    ) -> list[EffectiveModel]:
        """Every capability, every task and embedding, for display."""

        return [
            *(
                self.for_capability(
                    capability,
                )
                for capability in Capability
            ),
            *(
                self.for_task(
                    task,
                )
                for task in Task
            ),
            self.for_embedding(),
        ]

    def _resolve_capability(
        self,
        capability: Capability,
        operation: str,
    ) -> EffectiveModel:
        capability_override = self._configuration.capabilities.get(
            capability,
        )

        if capability_override is not None:
            return self._generation(
                operation,
                capability_override,
                ModelSource.CAPABILITY,
            )

        return self._generation(
            operation,
            self._configuration.primary,
            ModelSource.PRIMARY,
        )

    def _generation(
        self,
        operation: str,
        ref: ModelRef,
        source: ModelSource,
    ) -> EffectiveModel:
        provider_type = self._provider_type(
            ref,
        )

        if provider_type not in GENERATION_PROVIDER_TYPES:
            raise ModelCompatibilityError(
                f"'{operation}' resolves to {ref.provider}/{ref.model} "
                f"({source.value} setting), but provider type "
                f"'{provider_type.value}' cannot generate text. Configure a "
                "generation model for it.",
            )

        return EffectiveModel(
            operation=operation,
            provider=ref.provider,
            provider_type=provider_type,
            model=ref.model,
            source=source,
            think=ref.think,
        )

    def _provider_type(
        self,
        ref: ModelRef,
    ) -> ProviderType:
        return self._configuration.providers[ref.provider].type
