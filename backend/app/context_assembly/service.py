"""Default Context Assembly implementation."""

from app.chat.models import (
    ChatMessage,
    ChatPrompt,
    ChatRole,
)
from app.context_assembly.models import (
    ContextAssemblyRequest,
    ContextAssemblyResponse,
)
from app.context_assembly.providers import (
    ContextAssembly,
)


class DefaultContextAssembly(
    ContextAssembly,
):
    """Default implementation of Context Assembly."""

    def assemble(
        self,
        request: ContextAssemblyRequest,
    ) -> ContextAssemblyResponse:
        """Assemble repository context into a chat prompt."""

        repository_context = "\n\n".join(
            (
                f"File: {result.metadata.relative_path}\n\n"
                f"{result.content}"
            )
            for result in request.results
        )

        prompt = ChatPrompt(
            messages=[
                ChatMessage(
                    role=ChatRole.SYSTEM,
                    content=(
                        "You are a repository-aware coding assistant. "
                        "Use the provided repository context when answering."
                    ),
                ),
                ChatMessage(
                    role=ChatRole.SYSTEM,
                    content=repository_context,
                ),
                ChatMessage(
                    role=ChatRole.USER,
                    content=request.query,
                ),
            ],
        )

        return ContextAssemblyResponse(
            prompt=prompt,
        )