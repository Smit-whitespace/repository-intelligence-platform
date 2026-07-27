"""End-to-end backend workflow certification tests."""

from collections.abc import Iterator
from collections.abc import Sequence
from pathlib import Path
import shutil

from fastapi.testclient import TestClient

from app.chat.models import (
    ChatChunk,
    ChatPrompt,
    ChatResponse,
)
from app.chat.providers import ChatProvider
from app.chat.service import ChatService
from app.context_assembly.service import (
    DefaultContextAssembly,
)
from app.dependencies.providers import (
    get_chat_service,
)
from app.indexing.exceptions import EmbeddingError
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
from app.main import app
from app.repository.models import (
    ChunkBoundary,
    RepositoryChunkMetadata,
)


class FakeEmbeddingProvider(EmbeddingProvider):
    """Deterministic embedding provider."""

    def embed(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        """Return one simple vector per input."""

        return [
            EmbeddingVector(
                values=[1.0],
            )
            for _ in texts
        ]


class FailingEmbeddingProvider(EmbeddingProvider):
    """Embedding provider that fails deterministically."""

    def embed(
        self,
        texts: Sequence[str],
    ) -> list[EmbeddingVector]:
        """Raise the retrieval failure used by chat."""

        raise EmbeddingError(
            "Embedding provider unavailable.",
        )


class FakeVectorStore(VectorStore):
    """Deterministic vector store."""

    def __init__(
        self,
    ) -> None:
        """Initialize fake vector store."""

        self.query_embedding: EmbeddingVector | None = None

    def add(
        self,
        chunks: Sequence[IndexedChunk],
    ) -> None:
        """Store chunks."""

    def search(
        self,
        query_embedding: EmbeddingVector,
        limit: int = 10,
    ) -> list[SearchHit]:
        """Return one repository search hit."""

        self.query_embedding = query_embedding

        return [
            SearchHit(
                chunk_id="chunk-1",
                content="def main():\n    return 'hello'",
                metadata=RepositoryChunkMetadata(
                    relative_path=Path(
                        "main.py",
                    ),
                    language="Python",
                    mime_type="text/x-python",
                    sha256="abc123",
                ),
                boundary=ChunkBoundary(
                    start_line=1,
                    end_line=2,
                ),
                vector_score=0.9,
            ),
        ]

    def delete(
        self,
        chunk_ids: Sequence[str],
    ) -> None:
        """Delete chunks."""

    def clear(
        self,
    ) -> None:
        """Clear chunks."""


class RecordingChatProvider(ChatProvider):
    """Chat provider that records prompts."""

    def __init__(
        self,
    ) -> None:
        """Initialize recording provider."""

        self.prompt: ChatPrompt | None = None

    def generate(
        self,
        prompt: ChatPrompt,
    ) -> ChatResponse:
        """Return a deterministic response."""

        self.prompt = prompt

        return ChatResponse(
            content="Repository answer.",
        )

    def stream(
        self,
        prompt: ChatPrompt,
    ) -> Iterator[ChatChunk]:
        """Return deterministic stream chunks."""

        self.prompt = prompt

        yield ChatChunk(
            content="Repository",
            is_final=False,
        )

        yield ChatChunk(
            content=" answer.",
            is_final=True,
        )


def create_chat_service(
    embedding_provider: EmbeddingProvider,
    chat_provider: RecordingChatProvider,
) -> ChatService:
    """Create a chat service with deterministic dependencies."""

    return ChatService(
        retrieval_service=RetrievalService(
            embedding_provider=embedding_provider,
            vector_store=FakeVectorStore(),
        ),
        context_assembly=DefaultContextAssembly(),
        chat_provider=chat_provider,
    )


def test_project_management_workflow(
    tmp_path: Path,
) -> None:
    """Project open should persist metadata retrievable through the API."""

    client = TestClient(
        app,
    )

    open_response = client.post(
        "/api/v1/projects/open",
        json={
            "root_directory": str(
                tmp_path,
            ),
        },
    )

    assert open_response.status_code == 200

    assert (tmp_path / ".local_openclaw" / "project.json").exists()

    info_response = client.get(
        "/api/v1/projects/info",
        params={
            "root_directory": str(
                tmp_path,
            ),
        },
    )

    assert info_response.status_code == 200

    assert info_response.json()["name"] == tmp_path.name


def test_project_open_rejects_invalid_project(
    tmp_path: Path,
) -> None:
    """Invalid project roots should return a documented error."""

    client = TestClient(
        app,
    )

    response = client.post(
        "/api/v1/projects/open",
        json={
            "root_directory": str(
                tmp_path / "missing",
            ),
        },
    )

    assert response.status_code == 400

    assert "detail" in response.json()


def test_project_info_handles_deleted_project(
    tmp_path: Path,
) -> None:
    """Project info should fail predictably after repository deletion."""

    client = TestClient(
        app,
    )

    open_response = client.post(
        "/api/v1/projects/open",
        json={
            "root_directory": str(
                tmp_path,
            ),
        },
    )

    assert open_response.status_code == 200

    shutil.rmtree(
        tmp_path,
    )

    info_response = client.get(
        "/api/v1/projects/info",
        params={
            "root_directory": str(
                tmp_path,
            ),
        },
    )

    assert info_response.status_code == 404

    assert "detail" in info_response.json()


def test_repository_intelligence_workflow(
    tmp_path: Path,
) -> None:
    """Repository index should honor ignores and return metadata."""

    (tmp_path / "main.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    internal_directory = tmp_path / ".local_openclaw"

    internal_directory.mkdir()

    (internal_directory / "project.json").write_text(
        "{}",
        encoding="utf-8",
    )

    client = TestClient(
        app,
    )

    index_response = client.get(
        "/api/v1/repository/index",
        params={
            "root_directory": str(
                tmp_path,
            ),
        },
    )

    assert index_response.status_code == 200

    data = index_response.json()

    assert data["summary"] == {
        "files": 1,
        "directories": 0,
        "total_size_bytes": 14,
    }

    assert (
        len(
            data["entries"],
        )
        == 1
    )

    entry = data["entries"][0]

    assert entry["relative_path"] == "main.py"

    assert entry["language"] == "Python"

    assert entry["is_text_file"] is True

    assert entry["mime_type"] == "text/x-python"


def test_repository_index_rejects_invalid_repository(
    tmp_path: Path,
) -> None:
    """Invalid repository roots should return a documented error."""

    client = TestClient(
        app,
    )

    response = client.get(
        "/api/v1/repository/index",
        params={
            "root_directory": str(
                tmp_path / "missing",
            ),
        },
    )

    assert response.status_code == 400

    assert "detail" in response.json()


def test_repository_index_rejects_file_path(
    tmp_path: Path,
) -> None:
    """Repository index should reject files as repository roots."""

    repository_file = tmp_path / "README.md"

    repository_file.write_text(
        "hello",
        encoding="utf-8",
    )

    client = TestClient(
        app,
    )

    response = client.get(
        "/api/v1/repository/index",
        params={
            "root_directory": str(
                repository_file,
            ),
        },
    )

    assert response.status_code == 400

    assert "detail" in response.json()


def test_repository_aware_chat_workflow() -> None:
    """Chat API should retrieve context before generating a response."""

    chat_provider = RecordingChatProvider()

    app.dependency_overrides[get_chat_service] = lambda: create_chat_service(
        embedding_provider=FakeEmbeddingProvider(),
        chat_provider=chat_provider,
    )

    client = TestClient(
        app,
    )

    response = client.post(
        "/api/v1/chat",
        json={
            "query": "What does main.py do?",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    assert response.json() == {
        "content": "Repository answer.",
    }

    assert chat_provider.prompt is not None

    assert "File: main.py" in chat_provider.prompt.messages[2].content


def test_chat_streaming_workflow() -> None:
    """Streaming chat should return server-sent events."""

    chat_provider = RecordingChatProvider()

    app.dependency_overrides[get_chat_service] = lambda: create_chat_service(
        embedding_provider=FakeEmbeddingProvider(),
        chat_provider=chat_provider,
    )

    client = TestClient(
        app,
    )

    with client.stream(
        "GET",
        "/api/v1/chat/stream",
        params={
            "query": "Explain main.py",
        },
    ) as response:
        assert response.status_code == 200

        stream = "".join(
            response.iter_text(),
        )

    app.dependency_overrides.clear()

    assert stream == ("data: Repository\n\ndata:  answer.\n\n")

    assert chat_provider.prompt is not None


def test_chat_rejects_invalid_request() -> None:
    """Invalid chat requests should return validation errors."""

    client = TestClient(
        app,
    )

    response = client.post(
        "/api/v1/chat",
        json={},
    )

    assert response.status_code == 422


def test_chat_propagates_retrieval_errors() -> None:
    """Retrieval failures should return the documented server error shape."""

    app.dependency_overrides[get_chat_service] = lambda: create_chat_service(
        embedding_provider=FailingEmbeddingProvider(),
        chat_provider=RecordingChatProvider(),
    )

    client = TestClient(
        app,
    )

    response = client.post(
        "/api/v1/chat",
        json={
            "query": "Explain main.py",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 500

    assert response.json() == {
        "detail": "Embedding provider unavailable.",
    }


def test_complete_editing_apply_rollback_workflow(
    tmp_path: Path,
) -> None:
    """Editing should plan, apply, snapshot, and rollback through the API."""

    readme_path = tmp_path / "README.md"

    readme_path.write_text(
        "Original contents",
        encoding="utf-8",
    )

    client = TestClient(
        app,
    )

    plan_response = client.post(
        "/api/v1/editing/edit",
        json={
            "repository_root": str(
                tmp_path,
            ),
            "instruction": "create file README.md",
        },
    )

    assert plan_response.status_code == 200

    assert (
        readme_path.read_text(
            encoding="utf-8",
        )
        == "Original contents"
    )

    change_set = plan_response.json()["change_set"]

    apply_response = client.post(
        "/api/v1/editing/apply",
        json={
            "repository_root": str(
                tmp_path,
            ),
            "change_set": change_set,
        },
    )

    assert apply_response.status_code == 200

    snapshot_id = apply_response.json()["snapshot_id"]

    assert snapshot_id

    assert (
        readme_path.read_text(
            encoding="utf-8",
        )
        == ""
    )

    rollback_response = client.post(
        "/api/v1/editing/rollback",
        json={
            "repository_root": str(
                tmp_path,
            ),
            "snapshot_id": snapshot_id,
        },
    )

    assert rollback_response.status_code == 204

    assert (
        readme_path.read_text(
            encoding="utf-8",
        )
        == "Original contents"
    )


def test_editing_rejects_repository_boundary_escape(
    tmp_path: Path,
) -> None:
    """Planning should reject file paths outside the repository root."""

    client = TestClient(
        app,
    )

    response = client.post(
        "/api/v1/editing/edit",
        json={
            "repository_root": str(
                tmp_path,
            ),
            "instruction": "create file ../outside.txt",
        },
    )

    assert response.status_code == 400

    assert not (tmp_path.parent / "outside.txt").exists()


def test_editing_apply_rejects_invalid_repository(
    tmp_path: Path,
) -> None:
    """Apply should reject missing repository roots."""

    missing_root = tmp_path / "missing"

    client = TestClient(
        app,
    )

    response = client.post(
        "/api/v1/editing/apply",
        json={
            "repository_root": str(
                missing_root,
            ),
            "change_set": {
                "edits": [
                    {
                        "relative_path": "README.md",
                        "original_content": "",
                        "updated_content": "content",
                    },
                ],
            },
        },
    )

    assert response.status_code == 400

    assert not missing_root.exists()


def test_editing_rejects_invalid_snapshot_id(
    tmp_path: Path,
) -> None:
    """Rollback should reject unknown snapshot identifiers."""

    client = TestClient(
        app,
    )

    response = client.post(
        "/api/v1/editing/rollback",
        json={
            "repository_root": str(
                tmp_path,
            ),
            "snapshot_id": "missing-snapshot",
        },
    )

    assert response.status_code == 404


def test_editing_rollback_rejects_invalid_repository(
    tmp_path: Path,
) -> None:
    """Rollback should reject missing repository roots."""

    repository_file = tmp_path / "README.md"

    repository_file.write_text(
        "Original contents",
        encoding="utf-8",
    )

    client = TestClient(
        app,
    )

    apply_response = client.post(
        "/api/v1/editing/apply",
        json={
            "repository_root": str(
                tmp_path,
            ),
            "change_set": {
                "edits": [
                    {
                        "relative_path": "README.md",
                        "original_content": "Original contents",
                        "updated_content": "Updated contents",
                    },
                ],
            },
        },
    )

    assert apply_response.status_code == 200

    response = client.post(
        "/api/v1/editing/rollback",
        json={
            "repository_root": str(
                tmp_path / "missing",
            ),
            "snapshot_id": apply_response.json()["snapshot_id"],
        },
    )

    assert response.status_code == 400

    assert not (tmp_path / "missing").exists()


def test_editing_rejects_invalid_rollback_request() -> None:
    """Rollback should reject malformed requests."""

    client = TestClient(
        app,
    )

    response = client.post(
        "/api/v1/editing/rollback",
        json={
            "repository_root": ".",
        },
    )

    assert response.status_code == 422
