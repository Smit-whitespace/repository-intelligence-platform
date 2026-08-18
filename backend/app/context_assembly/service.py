"""Default Context Assembly implementation."""

from collections import defaultdict

import tiktoken

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

_INSTRUCTION_WITH_CONTEXT = (
    "You are a repository-aware coding assistant.\n\n"
    "Rules:\n"
    "- Answer using ONLY the repository context provided below.\n"
    "- When referencing code, cite the source file path.\n"
    "- If the context does not contain enough evidence to answer the "
    "question, say: \"I couldn't find enough evidence in the indexed "
    'repository to answer this question accurately."\n'
    "- Never fabricate files, functions, classes, or APIs.\n"
    "- Do not reference files or code that are not in the context."
)

_INSTRUCTION_WITHOUT_CONTEXT = (
    "You are a repository-aware coding assistant.\n\n"
    "No repository context is available for this query.\n"
    "Clearly distinguish between:\n"
    "- What you know from general knowledge\n"
    "- What you would expect to find in the repository\n\n"
    "Do not claim specific files, functions, classes, or APIs exist "
    "unless you are certain. Never fabricate code."
)

_DEFAULT_ENCODING = "cl100k_base"


class DefaultContextAssembly(
    ContextAssembly,
):
    """Default implementation of Context Assembly.

    Parameters
    ----------
    max_context_tokens:
        Maximum tokens for repository context content
        (excluding system message and user query). Default 2000.
    min_similarity:
        Minimum heuristic ranking score to include a result.
        Results below this threshold are considered noise. Default 0.3.
        This is not a calibrated similarity — see ``SearchResult.similarity_score``.
    """

    def __init__(
        self,
        max_context_tokens: int = 2000,
        min_similarity: float = 0.3,
    ) -> None:
        self._max_context_tokens = max_context_tokens
        self._min_similarity = min_similarity
        self._encoding = tiktoken.get_encoding(_DEFAULT_ENCODING)

    def _count_tokens(
        self,
        text: str,
    ) -> int:
        """Count tokens in text using the configured encoding."""

        return len(
            self._encoding.encode(
                text,
            ),
        )

    def _build_context_overview(
        self,
        sorted_groups: list[list],
    ) -> str:
        """Build a summary of files and their relevance levels."""

        lines: list[str] = []
        for group in sorted_groups:
            path = group[0].metadata.relative_path
            max_score = max(r.similarity_score for r in group)
            lines.append(f"- {path} (relevance: {max_score:.2f})")
        return "\n".join(lines)

    def assemble(
        self,
        request: ContextAssemblyRequest,
    ) -> ContextAssemblyResponse:
        """Assemble repository context into a chat prompt."""

        results = list(request.results)

        # Filter low-similarity noise
        results = [r for r in results if r.similarity_score >= self._min_similarity]

        # Deduplicate by exact content match
        seen: set[str] = set()
        deduped: list = []
        for r in results:
            if r.content not in seen:
                seen.add(r.content)
                deduped.append(r)
        results = deduped

        if not results:
            return ContextAssemblyResponse(
                prompt=ChatPrompt(
                    messages=[
                        ChatMessage(
                            role=ChatRole.SYSTEM,
                            content=_INSTRUCTION_WITHOUT_CONTEXT,
                        ),
                        ChatMessage(
                            role=ChatRole.USER,
                            content=request.query,
                        ),
                    ],
                ),
            )

        # Group by file path, sort chunks within file by start_line
        groups: dict[str, list] = defaultdict(list)
        for r in results:
            groups[str(r.metadata.relative_path)].append(r)
        for group in groups.values():
            group.sort(key=lambda r: r.boundary.start_line)

        # Sort groups by best relevance score (most relevant file first)
        sorted_groups = sorted(
            groups.values(),
            key=lambda g: max(r.similarity_score for r in g),
            reverse=True,
        )

        # Build context overview
        overview = self._build_context_overview(sorted_groups)

        # Build formatted blocks within the token budget
        blocks: list[str] = []
        total_tokens = 0

        for group in sorted_groups:
            file_path = group[0].metadata.relative_path
            contents: list[str] = []
            group_tokens = 0
            for r in group:
                content_token_count = self._count_tokens(
                    r.content,
                )
                if (
                    total_tokens + group_tokens + content_token_count
                    > self._max_context_tokens
                ):
                    break
                contents.append(r.content)
                group_tokens += content_token_count

            if not contents:
                continue

            block = f"File: {file_path}\n\n" + "\n\n".join(contents)
            block_token_count = self._count_tokens(
                block,
            )

            if total_tokens + block_token_count > self._max_context_tokens:
                break

            blocks.append(block)
            total_tokens += block_token_count

        repository_context = "\n\n".join(blocks)

        prompt = ChatPrompt(
            messages=[
                ChatMessage(
                    role=ChatRole.SYSTEM,
                    content=_INSTRUCTION_WITH_CONTEXT,
                ),
                ChatMessage(
                    role=ChatRole.SYSTEM,
                    content=f"Context overview:\n{overview}",
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
