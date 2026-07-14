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
from app.editing.snapshot_models import (
    Snapshot,
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

        self._validate_relative_paths(
            repository_root=repository_root,
            relative_paths=[
                edit.relative_path
                for edit in change_set.edits
            ],
            empty_path_message="ChangeSet contains an empty relative path.",
            escape_message="ChangeSet contains a path outside the repository.",
            duplicate_message="ChangeSet contains duplicate target paths.",
        )

        for edit in change_set.edits:
            target_path = (
                repository_root
                / edit.relative_path
            ).resolve()

            self._write_file_atomic(
                target_path=target_path,
                content=edit.updated_content,
            )

    def restore(
        self,
        repository_root: Path,
        snapshot: Snapshot,
    ) -> None:
        """Restore files captured by a snapshot."""

        repository_root = (
            repository_root.resolve()
        )

        self._validate_relative_paths(
            repository_root=repository_root,
            relative_paths=[
                file.relative_path
                for file in snapshot.files
            ],
            empty_path_message="Snapshot contains an empty relative path.",
            escape_message="Snapshot contains a path outside the repository.",
            duplicate_message="Snapshot contains duplicate target paths.",
        )

        for file in snapshot.files:
            target_path = (
                repository_root
                / file.relative_path
            ).resolve()

            if file.existed:
                self._write_file_atomic(
                    target_path=target_path,
                    content=file.content,
                )

            elif target_path.exists():
                target_path.unlink()

    def _validate_relative_paths(
        self,
        repository_root: Path,
        relative_paths: list[Path],
        empty_path_message: str,
        escape_message: str,
        duplicate_message: str,
    ) -> None:
        """Validate repository-relative filesystem paths."""

        seen_paths: set[Path] = set()

        for relative_path in relative_paths:
            if (
                str(relative_path)
                == "."
            ):
                raise EditingError(
                    empty_path_message,
                )

            target_path = (
                repository_root
                / relative_path
            ).resolve()

            try:
                repository_relative_path = (
                    target_path.relative_to(
                        repository_root,
                    )
                )

            except ValueError as error:
                raise EditingError(
                    escape_message,
                ) from error

            if (
                repository_relative_path
                in seen_paths
            ):
                raise EditingError(
                    duplicate_message,
                )

            seen_paths.add(
                repository_relative_path,
            )

    def _write_file_atomic(
        self,
        target_path: Path,
        content: str,
    ) -> None:
        """Write file content using an atomic replacement."""

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
                    content,
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
