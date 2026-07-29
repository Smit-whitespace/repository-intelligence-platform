"""Tests for chat orchestration service."""

from collections.abc import Iterator
from collections.abc import Sequence
from pathlib import Path

from app.chat.models import (
    ChatChunk,
    ChatMessage,
    ChatPrompt,
    ChatRequest,
    ChatResponse,
    ChatRole,
)
from app.chat.providers import ChatProvider
from app.chat.service import ChatService
from app.context_assembly.models import (
    ContextAssemblyRequest,
    ContextAssemblyResponse,
)
from app.context_assembly.providers import (
    ContextAssembly,
)
from app.indexing.models import (
    EmbeddingVector,
    IndexedChunk,
)
from app.indexing.providers import EmbeddingProvider
from app.indexing.retrieval_models import (
    SearchHit,
)
from app.indexing.retrieval_service import (
    RetrievalService,
)
from app.indexing.stores import VectorStore
from app.repository.models import (
    ChunkBoundary,
    RepositoryChunkMetadata,
)


class FakeEmbeddingProvider(
    EmbeddingProvider,
):
    """Fake embedding provider."""

    def embed(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        """Return deterministic embeddings."""

        return [
            EmbeddingVector(
                values=[1.0],
            )
            for _ in texts
        ]


class FakeVectorStore(
    VectorStore,
):
    """Fake vector store."""

    def add(
        self,
        chunks: Sequence[IndexedChunk],
    ) -> None:
        """Store indexed chunks."""

    def search(
        self,
        query_embedding: EmbeddingVector,
        limit: int = 10,
        where: dict | None = None,
    ) -> list[SearchHit]:
        """Return deterministic search hits."""

        metadata = RepositoryChunkMetadata(
            relative_path=Path(
                "main.py",
            ),
            language="Python",
            mime_type="text/x-python",
            sha256="abc",
        )

        boundary = ChunkBoundary(
            start_line=1,
            end_line=1,
        )

        return [
            SearchHit(
                chunk_id="chunk-1",
                content="print('hello')",
                metadata=metadata,
                boundary=boundary,
                vector_score=0.9,
            ),
        ]

    def delete(
        self,
        chunk_ids: Sequence[str],
    ) -> None:
        """Delete indexed chunks."""

    def clear(
        self,
    ) -> None:
        """Clear indexed chunks."""


class FakeContextAssembly(
    ContextAssembly,
):
    """Fake Context Assembly."""

    def __init__(
        self,
    ) -> None:
        """Initialize fake Context Assembly."""

        self.called = False

        self.request: (
            ContextAssemblyRequest
            | None
        ) = None

    def assemble(
        self,
        request: ContextAssemblyRequest,
    ) -> ContextAssemblyResponse:
        """Return deterministic prompt."""

        self.called = True

        self.request = request

        return ContextAssemblyResponse(
            prompt=ChatPrompt(
                messages=[
                    ChatMessage(
                        role=ChatRole.USER,
                        content=request.query,
                    ),
                ],
            ),
        )


class FakeChatProvider(
    ChatProvider,
):
    """Fake chat provider."""

    def __init__(
        self,
    ) -> None:
        """Initialize fake chat provider."""

        self.generate_called = False

        self.stream_called = False

        self.prompt: ChatPrompt | None = (
            None
        )

    def generate(
        self,
        prompt: ChatPrompt,
    ) -> ChatResponse:
        """Return deterministic response."""

        self.generate_called = True

        self.prompt = prompt

        return ChatResponse(
            content="Hello!",
        )

    def stream(
        self,
        prompt: ChatPrompt,
    ) -> Iterator[ChatChunk]:
        """Return deterministic stream."""

        self.stream_called = True

        self.prompt = prompt

        yield ChatChunk(
            content="Hello",
            is_final=False,
        )

        yield ChatChunk(
            content="!",
            is_final=True,
        )


def create_chat_service() -> tuple[
    ChatService,
    FakeContextAssembly,
    FakeChatProvider,
]:
    """Create a chat service with fake dependencies."""

    retrieval_service = RetrievalService(
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=FakeVectorStore(),
    )

    context_assembly = (
        FakeContextAssembly()
    )

    chat_provider = FakeChatProvider()

    service = ChatService(
        retrieval_service=retrieval_service,
        context_assembly=context_assembly,
        chat_provider=chat_provider,
    )

    return (
        service,
        context_assembly,
        chat_provider,
    )


def test_chat() -> None:
    """Chat should orchestrate all collaborators."""

    (
        service,
        context_assembly,
        chat_provider,
    ) = create_chat_service()

    response = service.chat(
        ChatRequest(
            query="What does main.py do?",
        ),
    )

    assert (
        response.content
        == "Hello!"
    )

    assert (
        context_assembly.called
    )

    assert (
        context_assembly.request
        is not None
    )

    assert (
        context_assembly.request.query
        == "What does main.py do?"
    )

    assert (
        chat_provider.generate_called
    )

    assert (
        chat_provider.prompt
        is not None
    )

    assert (
        chat_provider.prompt.messages[
            0
        ].content
        == "What does main.py do?"
    )


def test_stream() -> None:
    """Streaming chat should orchestrate all collaborators."""

    (
        service,
        context_assembly,
        chat_provider,
    ) = create_chat_service()

    chunks = list(
        service.stream(
            ChatRequest(
                query="Explain the repository.",
            ),
        )
    )

    assert len(
        chunks,
    ) == 2

    assert (
        chunks[0].content
        == "Hello"
    )

    assert (
        chunks[1].is_final
    )

    assert (
        context_assembly.called
    )

    assert (
        context_assembly.request
        is not None
    )

    assert (
        context_assembly.request.query
        == "Explain the repository."
    )

    assert (
        chat_provider.stream_called
    )

    assert (
        chat_provider.prompt
        is not None
    )

    assert (
        chat_provider.prompt.messages[
            0
        ].content
        == "Explain the repository."
    )