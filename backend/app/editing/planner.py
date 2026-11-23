"""Turn an instruction into search/replace edits using RIP's edit model.

The planner gathers context through the workspace (path-safe, secret
files excluded): the files the user names, plus the chunks semantic
search finds for the instruction. It asks the ``edit.plan`` model for
edit blocks in a fixed text format, which models write reliably, and
parses them back into ``EditOperation`` objects. Turning those into a
proposal (and checking that every search text matches exactly once) is
the proposal builder's job, shared with edits that agents send directly.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

from app.chat.models import (
    ChatMessage,
    ChatPrompt,
    ChatRole,
)
from app.chat.providers import ChatProvider
from app.editing.exceptions import EditingError
from app.editing.proposals import EditOperation
from app.indexing.exceptions import IndexingError
from app.workspace.exceptions import WorkspaceError
from app.workspace.service import RepositoryWorkspace

MAX_NAMED_FILES = 10

MAX_CONTEXT_CHARACTERS = 120_000

SEMANTIC_HITS = 8

SYSTEM_PROMPT = """\
You are a careful software engineer editing a repository. Make the \
smallest change that fully does what the user asks.

Reply with a short explanation, then one or more edit blocks in exactly \
this format:

<<<<<<< SEARCH path/relative/to/repository
exact lines copied from the file
=======
the replacement lines
>>>>>>> REPLACE

Rules:
- Copy the SEARCH text exactly from the file content you are given, \
including indentation. It must occur exactly once in that file; include \
a few surrounding lines if needed to make it unique.
- To create a new file, leave the SEARCH section empty and put the whole \
file in the replacement.
- Only edit files whose content you were given, or create new files.
- Do not wrap edit blocks in code fences.
"""

_EDIT_BLOCK = re.compile(
    r"^<<<<<<< SEARCH[ \t]+(?P<path>[^\n]+?)[ \t]*\n"
    r"(?P<search>.*?)"
    r"^=======[ \t]*\n"
    r"(?P<replace>.*?)"
    r"^>>>>>>> REPLACE[ \t]*$",
    re.DOTALL | re.MULTILINE,
)


@dataclass(frozen=True)
class PlannedEdits:
    """What the edit model proposed."""

    operations: list[EditOperation]

    notes: str


class EditPlanner:
    """Generate edit operations from a natural-language instruction."""

    def __init__(
        self,
        chat_provider_factory: Callable[[], ChatProvider],
    ) -> None:
        """``chat_provider_factory`` builds the ``edit.plan`` model's adapter."""

        self._chat_provider_factory = chat_provider_factory

    def plan(
        self,
        workspace: RepositoryWorkspace,
        instruction: str,
        files: list[str],
    ) -> PlannedEdits:
        if not instruction.strip():
            raise EditingError(
                "Describe the change to make.",
            )

        if len(files) > MAX_NAMED_FILES:
            raise EditingError(
                f"Name at most {MAX_NAMED_FILES} files.",
            )

        context = self._context(
            workspace,
            instruction,
            files,
        )

        response = self._chat_provider_factory().generate(
            ChatPrompt(
                messages=[
                    ChatMessage(
                        role=ChatRole.SYSTEM,
                        content=SYSTEM_PROMPT,
                    ),
                    ChatMessage(
                        role=ChatRole.USER,
                        content=(
                            f"Instruction:\n{instruction.strip()}\n\n"
                            f"Repository files:\n\n{context}"
                        ),
                    ),
                ],
            ),
        )

        operations, notes = parse_edit_blocks(
            response.content,
        )

        if not operations:
            raise EditingError(
                "The edit model did not produce any edit blocks. Rephrase "
                "the instruction or name the files to change."
                + (f" Its reply began: {notes[:300]}" if notes else ""),
            )

        return PlannedEdits(
            operations=operations,
            notes=notes,
        )

    @staticmethod
    def _context(
        workspace: RepositoryWorkspace,
        instruction: str,
        files: list[str],
    ) -> str:
        sections: list[str] = []

        budget = MAX_CONTEXT_CHARACTERS

        for path in files:
            content = workspace.read_file(
                path,
            )

            if content.truncated:
                raise EditingError(
                    f"{path} is too long to edit through the edit model "
                    f"({content.total_lines} lines).",
                )

            section = (
                f"### {content.path} (whole file)\n"
                f"```\n{content.content}```\n"
            )

            if len(section) > budget:
                raise EditingError(
                    "The named files are too large to send to the edit "
                    "model together; name fewer files.",
                )

            budget -= len(section)

            sections.append(
                section,
            )

        try:
            hits = workspace.search_semantic(
                instruction,
                limit=SEMANTIC_HITS,
            ).hits

        except (WorkspaceError, IndexingError):
            # Without a usable index, the named files are the context.
            hits = []

        named = set(
            files,
        )

        for hit in hits:
            if hit.path in named:
                continue

            section = (
                f"### {hit.path} (lines {hit.start_line}-{hit.end_line})\n"
                f"```\n{hit.content}\n```\n"
            )

            if len(section) > budget:
                break

            budget -= len(section)

            sections.append(
                section,
            )

        if not sections:
            raise EditingError(
                "No repository context was found for this instruction. Name "
                "the files to change, or index the project first.",
            )

        return "\n".join(
            sections,
        )


def parse_edit_blocks(
    text: str,
) -> tuple[list[EditOperation], str]:
    """Extract edit operations, and the explanation outside the blocks."""

    # Some providers return CRLF; the block markers are matched on "\n".
    text = text.replace(
        "\r\n",
        "\n",
    )

    operations = [
        EditOperation(
            path=match.group(
                "path",
            ).strip().strip("`'\""),
            search=match.group(
                "search",
            ),
            replace=match.group(
                "replace",
            ),
        )
        for match in _EDIT_BLOCK.finditer(
            text,
        )
    ]

    notes = _EDIT_BLOCK.sub(
        "",
        text,
    ).strip()

    return operations, notes[:2000]
