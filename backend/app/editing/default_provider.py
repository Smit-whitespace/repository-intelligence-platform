"""Default Repository Editing provider."""

from pathlib import Path

from app.editing.exceptions import (
    InvalidRepositoryError,
)
from app.editing.models import (
    ChangeSet,
    EditRequest,
    EditResponse,
    FileEdit,
)
from app.editing.providers import (
    EditingProvider,
)


class DefaultEditingProvider(
    EditingProvider,
):
    """Default implementation of the Editing provider."""

    def edit(
        self,
        request: EditRequest,
    ) -> EditResponse:
        """Generate repository modifications."""

        repository_root = (
            request.repository_root.resolve()
        )

        if not repository_root.exists():
            raise InvalidRepositoryError(
                "Repository root does not exist.",
            )

        if not repository_root.is_dir():
            raise InvalidRepositoryError(
                "Repository root is not a directory.",
            )

        change_set = ChangeSet(
            edits=[],
        )

        instruction = (
            request.instruction.strip()
        )

        prefix = "create file "

        if instruction.lower().startswith(
            prefix,
        ):
            relative_path = Path(
                instruction[
                    len(prefix):
                ].strip(),
            )

            candidate_path = (
                repository_root
                / relative_path
            ).resolve()

            try:
                repository_relative_path = (
                    candidate_path.relative_to(
                        repository_root,
                    )
                )

            except ValueError as error:
                raise InvalidRepositoryError(
                    "Planned file path escapes the repository root.",
                ) from error

            original_content = ""

            if candidate_path.exists():
                if not candidate_path.is_file():
                    raise InvalidRepositoryError(
                        "Planned path is not a file.",
                    )

                original_content = (
                    candidate_path.read_text(
                        encoding="utf-8",
                    )
                )

            change_set.edits.append(
                FileEdit(
                    relative_path=repository_relative_path,
                    original_content=original_content,
                    updated_content="",
                ),
            )

        return EditResponse(
            change_set=change_set,
        )