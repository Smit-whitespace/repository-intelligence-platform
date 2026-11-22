"""Repository ChangeSet application."""

import os
import stat
import tempfile
from pathlib import Path

from app.core.storage.locations import (
    is_protected_path,
    is_valid_path_text,
)
from app.editing.exceptions import (
    EditConflictError,
    EditingError,
    IncompleteRevertError,
)
from app.editing.models import (
    ChangeSet,
)
from app.editing.snapshot_models import (
    Snapshot,
)


def read_text_exact(
    path: Path,
) -> str:
    """Read a UTF-8 text file without translating line endings.

    ``Path.read_text`` uses universal newlines and turns ``\\r\\n`` into
    ``\\n``, which would make CRLF files compare and snapshot wrongly.
    """

    with path.open(
        encoding="utf-8",
        newline="",
    ) as file:
        return file.read()


def read_text_for_edit(
    path: Path,
    relative_path: Path,
) -> str | None:
    """Read an edit target exactly, or ``None`` if it does not exist.

    Binary, non-UTF-8 and unreadable files become a clear ``EditingError``
    (HTTP 400) instead of an unhandled ``UnicodeDecodeError`` (HTTP 500).
    """

    if not path.exists():
        return None

    try:
        return read_text_exact(
            path,
        )

    except UnicodeDecodeError as error:
        raise EditingError(
            f"File is not UTF-8 text and cannot be edited: {relative_path.as_posix()}",
        ) from error

    except OSError as error:
        raise EditingError(
            f"Failed to read repository file: {relative_path.as_posix()}",
        ) from error


class ChangeApplier:
    """Apply repository modifications."""

    def apply(
        self,
        repository_root: Path,
        change_set: ChangeSet,
    ) -> None:
        """Apply every file modification, or none of them.

        Each edit's ``original_content`` must still match the file on
        disk (an empty string for a file that does not exist yet). If a
        write fails part-way, files already written are restored to
        their original content before the error is raised.
        """

        repository_root = (
            repository_root.resolve()
        )

        self.validate_change_set(
            repository_root=repository_root,
            change_set=change_set,
        )

        targets: list[tuple[Path, str, str | None]] = []

        for edit in change_set.edits:
            target_path = (
                repository_root
                / edit.relative_path
            ).resolve()

            current_content = read_text_for_edit(
                target_path,
                edit.relative_path,
            )

            if (current_content or "") != edit.original_content:
                raise EditConflictError(
                    "File changed since the edit was planned: "
                    f"{edit.relative_path.as_posix()}",
                )

            targets.append(
                (
                    target_path,
                    edit.updated_content,
                    current_content,
                ),
            )

        written: list[tuple[Path, str | None]] = []

        try:
            for target_path, updated_content, original_content in targets:
                self._write_file_atomic(
                    target_path=target_path,
                    content=updated_content,
                )

                written.append(
                    (
                        target_path,
                        original_content,
                    ),
                )

        except Exception as error:
            self._revert(
                repository_root,
                written,
                error,
            )

            raise EditingError(
                "Failed to apply ChangeSet; every written file was reverted.",
            ) from error

    def validate_change_set(
        self,
        repository_root: Path,
        change_set: ChangeSet,
    ) -> None:
        """Validate every target path without touching any file.

        Callers must run this before reading any target (for example to
        snapshot it), so a path outside the root is never read at all.
        """

        repository_root = (
            repository_root.resolve()
        )

        self._validate_repository_root(
            repository_root,
        )

        self._validate_relative_paths(
            repository_root=repository_root,
            relative_paths=[
                edit.relative_path
                for edit in change_set.edits
            ],
            empty_path_message="ChangeSet contains an empty relative path.",
            absolute_path_message="ChangeSet contains an absolute path.",
            escape_message="ChangeSet contains a path outside the repository.",
            protected_message="ChangeSet targets a protected path.",
            invalid_message="ChangeSet contains an invalid path.",
            duplicate_message="ChangeSet contains duplicate target paths.",
            conflict_message="ChangeSet contains conflicting target paths.",
            parent_message="ChangeSet target parent is not a directory.",
            target_directory_message="ChangeSet target path is a directory.",
        )

    def validate_snapshot(
        self,
        repository_root: Path,
        snapshot: Snapshot,
    ) -> None:
        """Validate every snapshot path without touching any file."""

        repository_root = (
            repository_root.resolve()
        )

        self._validate_repository_root(
            repository_root,
        )

        self._validate_relative_paths(
            repository_root=repository_root,
            relative_paths=[
                file.relative_path
                for file in snapshot.files
            ],
            empty_path_message="Snapshot contains an empty relative path.",
            absolute_path_message="Snapshot contains an absolute path.",
            escape_message="Snapshot contains a path outside the repository.",
            protected_message="Snapshot targets a protected path.",
            invalid_message="Snapshot contains an invalid path.",
            duplicate_message="Snapshot contains duplicate target paths.",
            conflict_message="Snapshot contains conflicting target paths.",
            parent_message="Snapshot target parent is not a directory.",
            target_directory_message="Snapshot target path is a directory.",
        )

    def restore(
        self,
        repository_root: Path,
        snapshot: Snapshot,
    ) -> None:
        """Restore files captured by a snapshot, all or nothing.

        If a write fails part-way, files already restored are put back to
        the state they were in before the rollback started.
        """

        repository_root = (
            repository_root.resolve()
        )

        self.validate_snapshot(
            repository_root=repository_root,
            snapshot=snapshot,
        )

        targets = [
            (
                (repository_root / file.relative_path).resolve(),
                file,
            )
            for file in snapshot.files
        ]

        current_states = [
            read_text_for_edit(
                target_path,
                file.relative_path,
            )
            for target_path, file in targets
        ]

        changed: list[tuple[Path, str | None]] = []

        try:
            for (target_path, file), current in zip(
                targets,
                current_states,
            ):
                if file.existed:
                    self._write_file_atomic(
                        target_path=target_path,
                        content=file.content,
                    )

                elif target_path.exists():
                    target_path.unlink()

                else:
                    continue

                changed.append(
                    (
                        target_path,
                        current,
                    ),
                )

        except Exception as error:
            self._revert(
                repository_root,
                changed,
                error,
            )

            raise EditingError(
                "Failed to roll back; every restored file was put back.",
            ) from error

    def _revert(
        self,
        repository_root: Path,
        written: list[tuple[Path, str | None]],
        cause: Exception,
    ) -> None:
        """Restore files written by a failed apply, newest first.

        Reports repository-relative paths only, so error responses never
        reveal where the repository lives on the server.
        """

        unrestored: list[str] = []

        for target_path, original_content in reversed(written):
            try:
                if original_content is None:
                    target_path.unlink(
                        missing_ok=True,
                    )

                else:
                    self._write_file_atomic(
                        target_path=target_path,
                        content=original_content,
                    )

            except Exception:
                unrestored.append(
                    target_path.relative_to(
                        repository_root,
                    ).as_posix(),
                )

        if unrestored:
            raise IncompleteRevertError(
                "Failed to apply ChangeSet, and these files could not be "
                f"reverted: {', '.join(unrestored)}.",
            ) from cause

    def _validate_repository_root(
        self,
        repository_root: Path,
    ) -> None:
        """Validate the repository root before mutation."""

        if not repository_root.exists():
            raise EditingError(
                "Repository root does not exist.",
            )

        if not repository_root.is_dir():
            raise EditingError(
                "Repository root is not a directory.",
            )

    def _validate_relative_paths(
        self,
        repository_root: Path,
        relative_paths: list[Path],
        empty_path_message: str,
        absolute_path_message: str,
        escape_message: str,
        protected_message: str,
        invalid_message: str,
        duplicate_message: str,
        conflict_message: str,
        parent_message: str,
        target_directory_message: str,
    ) -> None:
        """Validate repository-relative filesystem paths."""

        seen_paths: set[Path] = set()
        repository_relative_paths: list[Path] = []

        for relative_path in relative_paths:
            if (
                str(relative_path)
                == "."
            ):
                raise EditingError(
                    empty_path_message,
                )

            if relative_path.is_absolute():
                raise EditingError(
                    absolute_path_message,
                )

            if not is_valid_path_text(
                str(relative_path),
            ):
                raise EditingError(
                    invalid_message,
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

            # Checked on the resolved path, so a symlink that points into
            # a protected directory is rejected too.
            if is_protected_path(
                repository_relative_path,
            ):
                raise EditingError(
                    protected_message,
                )

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
            repository_relative_paths.append(
                repository_relative_path,
            )

            if target_path.exists() and target_path.is_dir():
                raise EditingError(
                    target_directory_message,
                )

            parent_path = target_path.parent

            while parent_path != repository_root:
                if parent_path.exists() and not parent_path.is_dir():
                    raise EditingError(
                        parent_message,
                    )

                parent_path = parent_path.parent

        for repository_relative_path in repository_relative_paths:
            for other_relative_path in repository_relative_paths:
                if (
                    repository_relative_path
                    == other_relative_path
                ):
                    continue

                try:
                    other_relative_path.relative_to(
                        repository_relative_path,
                    )

                except ValueError:
                    continue

                raise EditingError(
                    conflict_message,
                )

    def _write_file_atomic(
        self,
        target_path: Path,
        content: str,
    ) -> None:
        """Write file content using an atomic replacement.

        ``newline=""`` writes the content byte-for-byte; the default
        would turn every ``\\n`` into ``\\r\\n`` on Windows.
        """

        target_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=target_path.parent,
                delete=False,
            ) as temporary_file:
                temporary_path = Path(
                    temporary_file.name,
                )

                temporary_file.write(
                    content,
                )
                temporary_file.flush()
                os.fsync(
                    temporary_file.fileno(),
                )

            # Keep the target's permission bits (e.g. an executable
            # script); a fresh temporary file would otherwise reset them.
            if target_path.exists():
                os.chmod(
                    temporary_path,
                    stat.S_IMODE(
                        target_path.stat().st_mode,
                    ),
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
