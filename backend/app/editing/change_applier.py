"""Repository ChangeSet application."""

import os
import tempfile
from pathlib import Path

from app.editing.exceptions import (
    EditingError,
)
from app.editing.models import (
    ChangeSet,
)


class ChangeApplier:
    """Apply repository modifications."""

    def apply(
        self,
        repository_root: Path,
        change_set: ChangeSet,
    ) -> None:
        """Apply every file modification."""

        repository_root = (
            repository_root.resolve()
        )

        self._validate_change_set(
            repository_root,
            change_set,
        )

        for edit in change_set.edits:
            target_path = (
                repository_root
                / edit.relative_path
            ).resolve()

            target_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            temporary_path: Path | None = None

            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=target_path.parent,
                    delete=False,
                ) as temporary_file:
                    temporary_file.write(
                        edit.updated_content,
                    )
                    temporary_file.flush()
                    os.fsync(
                        temporary_file.fileno(),
                    )

                    temporary_path = Path(
                        temporary_file.name,
                    )

                temporary_path.replace(
                    target_path,
                )

            finally:
                if (
                    temporary_path is not None
                    and temporary_path.exists()
                ):
                    temporary_path.unlink()

    def _validate_change_set(
        self,
        repository_root: Path,
        change_set: ChangeSet,
    ) -> None:
        """Validate a ChangeSet before execution."""

        seen_paths: set[Path] = set()

        for edit in change_set.edits:
            if (
                str(edit.relative_path)
                == "."
            ):
                raise EditingError(
                    "ChangeSet contains an empty relative path.",
                )

            target_path = (
                repository_root
                / edit.relative_path
            ).resolve()

            try:
                repository_relative_path = (
                    target_path.relative_to(
                        repository_root,
                    )
                )

            except ValueError as error:
                raise EditingError(
                    "ChangeSet contains a path outside the repository.",
                ) from error

            if (
                repository_relative_path
                in seen_paths
            ):
                raise EditingError(
                    "ChangeSet contains duplicate target paths.",
                )

            seen_paths.add(
                repository_relative_path,
            )