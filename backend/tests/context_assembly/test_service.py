"""Tests for DefaultContextAssembly."""

from pathlib import Path

from app.chat.models import (
    ChatRole,
)
from app.context_assembly.models import (
    ContextAssemblyRequest,
)
from app.context_assembly.service import (
    DefaultContextAssembly,
)
from app.indexing.retrieval_models import (
    SearchResult,
)
from app.repository.models import (
    ChunkBoundary,
    ChunkType,
    RepositoryChunkMetadata,
)


def create_result(
    chunk_id: str = "chunk-1",
    content: str = "def foo():\n    pass",
    relative_path: str = "main.py",
    start_line: int = 1,
    end_line: int = 2,
    similarity: float = 0.8,
) -> SearchResult:
    """Create a sample search result."""

    return SearchResult(
        chunk_id=chunk_id,
        content=content,
        metadata=RepositoryChunkMetadata(
            relative_path=Path(relative_path),
            language="python",
            mime_type="text/x-python",
            sha256="abc123",
        ),
        boundary=ChunkBoundary(
            start_line=start_line,
            end_line=end_line,
            chunk_type=ChunkType.FUNCTION,
        ),
        similarity_score=similarity,
    )


_CONTEXT_MSG_INDEX = 2
_USER_MSG_INDEX = 3


class TestDefaultContextAssembly:
    """Tests for DefaultContextAssembly."""

    def test_empty_results_uses_no_context_instruction(
        self,
    ) -> None:
        """No results should use the no-context instruction and skip context."""

        assembly = DefaultContextAssembly()

        response = assembly.assemble(
            ContextAssemblyRequest(
                query="test",
                results=[],
            ),
        )

        assert len(response.prompt.messages) == 2

        system_msg = response.prompt.messages[0]

        assert system_msg.role == ChatRole.SYSTEM

        assert "No repository context is available" in system_msg.content

        assert response.prompt.messages[1].role == ChatRole.USER

    def test_single_result_included(
        self,
    ) -> None:
        """Single result should be in the context block."""

        assembly = DefaultContextAssembly()

        response = assembly.assemble(
            ContextAssemblyRequest(
                query="test",
                results=[
                    create_result(
                        content="def foo(): pass",
                    ),
                ],
            ),
        )

        context = response.prompt.messages[_CONTEXT_MSG_INDEX].content

        assert "File: main.py" in context

        assert "def foo(): pass" in context

    def test_multiple_files_grouped(
        self,
    ) -> None:
        """Results from the same file should be grouped under one header."""

        assembly = DefaultContextAssembly()

        response = assembly.assemble(
            ContextAssemblyRequest(
                query="test",
                results=[
                    create_result(
                        chunk_id="chunk-1",
                        content="def foo(): pass",
                        start_line=1,
                    ),
                    create_result(
                        chunk_id="chunk-2",
                        content="def bar(): pass",
                        start_line=10,
                    ),
                ],
            ),
        )

        context = response.prompt.messages[_CONTEXT_MSG_INDEX].content

        assert context.count("File: main.py") == 1

        assert "def foo(): pass" in context

        assert "def bar(): pass" in context

        foo_pos = context.index("def foo(): pass")

        bar_pos = context.index("def bar(): pass")

        assert foo_pos < bar_pos

    def test_filters_low_similarity_results(
        self,
    ) -> None:
        """Results below min similarity should be excluded."""

        assembly = DefaultContextAssembly(
            min_similarity=0.5,
        )

        response = assembly.assemble(
            ContextAssemblyRequest(
                query="test",
                results=[
                    create_result(
                        chunk_id="good",
                        content="relevant content",
                        similarity=0.9,
                    ),
                    create_result(
                        chunk_id="noise",
                        content="irrelevant noise",
                        similarity=0.1,
                    ),
                ],
            ),
        )

        context = response.prompt.messages[_CONTEXT_MSG_INDEX].content

        assert "relevant content" in context

        assert "irrelevant noise" not in context

    def test_deduplicates_by_content(
        self,
    ) -> None:
        """Duplicate content should be removed, keeping first occurrence."""

        assembly = DefaultContextAssembly()

        response = assembly.assemble(
            ContextAssemblyRequest(
                query="test",
                results=[
                    create_result(
                        chunk_id="first",
                        content="same content",
                        start_line=1,
                    ),
                    create_result(
                        chunk_id="second",
                        content="same content",
                        start_line=5,
                    ),
                ],
            ),
        )

        context = response.prompt.messages[_CONTEXT_MSG_INDEX].content

        assert context.count("same content") == 1

    def test_respects_token_budget(
        self,
    ) -> None:
        """Results exceeding the token budget should be dropped."""

        assembly = DefaultContextAssembly(
            max_context_tokens=7,
        )

        response = assembly.assemble(
            ContextAssemblyRequest(
                query="test",
                results=[
                    create_result(
                        chunk_id="small",
                        content="short",
                        relative_path="small.py",
                        similarity=0.9,
                    ),
                    create_result(
                        chunk_id="large",
                        content="this content is way too long and will exceed the tiny budget that was set for this test",
                        relative_path="large.py",
                        similarity=0.5,
                    ),
                ],
            ),
        )

        context = response.prompt.messages[_CONTEXT_MSG_INDEX].content

        assert "short" in context

        assert "too long" not in context

    def test_most_relevant_file_first(
        self,
    ) -> None:
        """Files should be ordered by best relevance score."""

        assembly = DefaultContextAssembly()

        response = assembly.assemble(
            ContextAssemblyRequest(
                query="test",
                results=[
                    create_result(
                        chunk_id="alpha-chunk",
                        content="alpha content",
                        relative_path="alpha.py",
                        similarity=0.6,
                    ),
                    create_result(
                        chunk_id="beta-chunk",
                        content="beta content",
                        relative_path="beta.py",
                        similarity=0.9,
                    ),
                ],
            ),
        )

        context = response.prompt.messages[_CONTEXT_MSG_INDEX].content

        beta_pos = context.index("beta.py")

        alpha_pos = context.index("alpha.py")

        assert beta_pos < alpha_pos

    def test_chunks_ordered_by_start_line(
        self,
    ) -> None:
        """Chunks within a file should be ordered by start_line."""

        assembly = DefaultContextAssembly()

        response = assembly.assemble(
            ContextAssemblyRequest(
                query="test",
                results=[
                    create_result(
                        chunk_id="chunk-1",
                        content="second chunk",
                        start_line=20,
                    ),
                    create_result(
                        chunk_id="chunk-2",
                        content="first chunk",
                        start_line=1,
                    ),
                ],
            ),
        )

        context = response.prompt.messages[_CONTEXT_MSG_INDEX].content

        first_pos = context.index("first chunk")

        second_pos = context.index("second chunk")

        assert first_pos < second_pos

    def test_user_query_preserved(
        self,
    ) -> None:
        """User query should be the last message."""

        assembly = DefaultContextAssembly()

        response = assembly.assemble(
            ContextAssemblyRequest(
                query="what does foo do?",
                results=[
                    create_result(),
                ],
            ),
        )

        user_message = response.prompt.messages[_USER_MSG_INDEX]

        assert user_message.role == ChatRole.USER

        assert user_message.content == "what does foo do?"

    def test_all_results_within_budget(
        self,
    ) -> None:
        """All results should be included when budget is sufficient."""

        assembly = DefaultContextAssembly(
            max_context_tokens=10000,
        )

        results = [
            create_result(
                chunk_id=f"chunk-{i}",
                content=f"content {i}",
                similarity=0.9 - i * 0.1,
            )
            for i in range(5)
        ]

        response = assembly.assemble(
            ContextAssemblyRequest(
                query="test",
                results=results,
            ),
        )

        context = response.prompt.messages[_CONTEXT_MSG_INDEX].content

        for i in range(5):
            assert f"content {i}" in context

    def test_grounding_instruction_includes_citation_rule(
        self,
    ) -> None:
        """System instruction should tell the model to cite sources."""

        assembly = DefaultContextAssembly()

        response = assembly.assemble(
            ContextAssemblyRequest(
                query="test",
                results=[create_result()],
            ),
        )

        instruction = response.prompt.messages[0].content

        assert "cite the source file path" in instruction

        assert "ONLY the repository context" in instruction

        assert "couldn't find enough evidence in the indexed repository" in instruction

    def test_grounding_instruction_forbids_fabrication(
        self,
    ) -> None:
        """System instruction should forbid fabricating code."""

        assembly = DefaultContextAssembly()

        response = assembly.assemble(
            ContextAssemblyRequest(
                query="test",
                results=[create_result()],
            ),
        )

        instruction = response.prompt.messages[0].content

        assert "Never fabricate files, functions, classes, or APIs" in instruction

    def test_context_overview_included(
        self,
    ) -> None:
        """Context overview should list files and their relevance."""

        assembly = DefaultContextAssembly()

        response = assembly.assemble(
            ContextAssemblyRequest(
                query="test",
                results=[
                    create_result(
                        relative_path="src/main.py",
                        similarity=0.85,
                    ),
                ],
            ),
        )

        overview = response.prompt.messages[1].content

        assert "Context overview:" in overview

        assert str(Path("src/main.py")) in overview

        assert "0.85" in overview

    def test_no_context_all_results_filtered(
        self,
    ) -> None:
        """When all results are filtered out, use no-context path."""

        assembly = DefaultContextAssembly(
            min_similarity=0.9,
        )

        response = assembly.assemble(
            ContextAssemblyRequest(
                query="test",
                results=[
                    create_result(
                        similarity=0.5,
                    ),
                ],
            ),
        )

        assert len(response.prompt.messages) == 2

        system_msg = response.prompt.messages[0]

        assert "No repository context is available" in system_msg.content

    def test_uses_token_counting_not_char_counting(
        self,
    ) -> None:
        """Budget should be enforced by token count, not char length."""

        assembly = DefaultContextAssembly(
            max_context_tokens=7,
        )

        response = assembly.assemble(
            ContextAssemblyRequest(
                query="test",
                results=[
                    create_result(
                        chunk_id="relevant",
                        content="a",
                        relative_path="small.py",
                        similarity=0.9,
                    ),
                    create_result(
                        chunk_id="irrelevant",
                        content="hello world foo bar baz",
                        relative_path="large.py",
                        similarity=0.5,
                    ),
                ],
            ),
        )

        context = response.prompt.messages[_CONTEXT_MSG_INDEX].content

        assert "a" in context

        assert "hello world foo bar baz" not in context
