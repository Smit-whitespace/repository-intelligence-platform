"""Chat orchestration service."""

from collections.abc import Iterator

from app.chat.models import (
    ChatChunk,
    ChatRequest,
    ChatResponse,
)
from app.chat.providers import ChatProvider
from app.context_assembly.models import (
    ContextAssemblyRequest,
)
from app.context_assembly.providers import (
    ContextAssembly,
)
from app.indexing.retrieval_models import (
    SearchQuery,
)
from app.indexing.retrieval_service import (
    RetrievalService,
)


class ChatService:
    """Repository-aware chat orchestration."""

    def __init__(
        self,
        retrieval_service: RetrievalService,
        context_assembly: ContextAssembly,
        chat_provider: ChatProvider,
    ) -> None:
        """Initialize the chat service."""

        self._retrieval_service = (
            retrieval_service
        )

        self._context_assembly = (
            context_assembly
        )

        self._chat_provider = (
            chat_provider
        )

    def chat(
        self,
        request: ChatRequest,
    ) -> ChatResponse:
        """Generate a repository-aware chat response."""

        search_response = (
            self._retrieval_service.search(
                SearchQuery(
                    query=request.query,
                    root_directory=request.root_directory,
                ),
            )
        )

        context = (
            self._context_assembly.assemble(
                ContextAssemblyRequest(
                    query=request.query,
                    results=search_response.results,
                ),
            )
        )

        return self._chat_provider.generate(
            context.prompt,
        )

    def stream(
        self,
        request: ChatRequest,
    ) -> Iterator[ChatChunk]:
        """Stream a repository-aware chat response."""

        search_response = (
            self._retrieval_service.search(
                SearchQuery(
                    query=request.query,
                    root_directory=request.root_directory,
                ),
            )
        )

        context = (
            self._context_assembly.assemble(
                ContextAssemblyRequest(
                    query=request.query,
                    results=search_response.results,
                ),
            )
        )

        return self._chat_provider.stream(
            context.prompt,
        )