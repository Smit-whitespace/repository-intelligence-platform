"""Repository Editing service."""

import hashlib
from collections.abc import Callable
from pathlib import Path

from app.core.storage.locations import is_registered_project
from app.editing.change_applier import (
    ChangeApplier,
    read_text_exact,
    read_text_for_edit,
)
from app.editing.exceptions import (
    EditConflictError,
    EditingError,
    IncompleteRevertError,
    UnregisteredRepositoryError,
)
from app.editing.models import (
    ChangeSet,
    EditRequest,
    EditResponse,
)
from app.editing.providers import (
    EditingProvider,
)
from app.editing.snapshot_models import (
    Snapshot,
    SnapshotFile,
)
from app.editing.snapshot_store import (
    SnapshotStore,
)


class EditingService:
    """Repository Editing orchestration service."""

    def __init__(
        self,
        editing_provider: EditingProvider,
        change_applier: ChangeApplier,
        snapshot_store_factory: Callable[[Path], SnapshotStore],
    ) -> None:
        """Initialize the editing service.

        Snapshots are persisted per project: the snapshot store is
        created from the repository root of each apply/rollback call,
        so snapshots always land in that project's own storage
        directory — never in a store chosen by the process working
        directory.
        """

        self._editing_provider = (
            editing_provider
        )

        self._change_applier = (
            change_applier
        )

        self._snapshot_store_factory = (
            snapshot_store_factory
        )

    def edit(
        self,
        request: EditRequest,
    ) -> EditResponse:
        """Generate repository modifications."""

        self._validate_repository_root(
            request.repository_root,
        )

        return self._editing_provider.edit(
            request,
        )

    def apply(
        self,
        repository_root: Path,
        change_set: ChangeSet,
    ) -> str:
        """Apply a previously generated ChangeSet."""

        self._validate_repository_root(
            repository_root,
        )

        if not change_set.edits:
            raise EditingError(
                "ChangeSet has no edits to apply.",
            )

        # Validate every path before any file is read: the snapshot below
        # reads each target, and must never read outside the repository.
        self._change_applier.validate_change_set(
            repository_root=repository_root,
            change_set=change_set,
        )

        snapshot_store = self._snapshot_store_factory(
            repository_root,
        )

        snapshot = self._create_snapshot(
            repository_root=repository_root,
            change_set=change_set,
        )

        snapshot_store.save(
            snapshot,
        )

        try:
            self._change_applier.apply(
                repository_root=repository_root,
                change_set=change_set,
            )

        except IncompleteRevertError as error:
            # The repository is in a partial state; the snapshot is the
            # way back, so keep it and tell the caller its id.
            raise IncompleteRevertError(
                f"{error} The pre-apply state is saved in snapshot "
                f"{snapshot.snapshot_id}; roll back with it.",
            ) from error

        except Exception:
            # Nothing was changed (or every change was reverted), so the
            # snapshot would only be clutter.
            try:
                snapshot_store.delete(
                    snapshot.snapshot_id,
                )

            except EditingError:
                pass

            raise

        return snapshot.snapshot_id

    def rollback(
        self,
        repository_root: Path,
        snapshot_id: str,
    ) -> None:
        """Restore a previously captured repository snapshot."""

        self._validate_repository_root(
            repository_root,
        )

        snapshot_store = self._snapshot_store_factory(
            repository_root,
        )

        snapshot = snapshot_store.load(
            snapshot_id,
        )

        # Snapshot files live on disk and could have been tampered with,
        # so their paths are validated before any of them is read.
        self._change_applier.validate_snapshot(
            repository_root=repository_root,
            snapshot=snapshot,
        )

        self._ensure_unchanged_since_apply(
            repository_root=repository_root,
            snapshot=snapshot,
        )

        self._change_applier.restore(
            repository_root=repository_root,
            snapshot=snapshot,
        )

    @staticmethod
    def _validate_repository_root(
        repository_root: Path,
    ) -> None:
        require_registered_root(
            repository_root,
        )

    @staticmethod
    def _ensure_unchanged_since_apply(
        repository_root: Path,
        snapshot: Snapshot,
    ) -> None:
        """Refuse a rollback that would overwrite later changes.

        Each file must be in one of the two states this snapshot knows
        about: what the apply wrote, or what was there before the apply
        (for a new file: absent). The second state matters after an
        incomplete revert, where some files are already back to their
        original content and the snapshot is the documented way back.
        Anything else means someone changed the file, so stop.
        """

        root = repository_root.resolve()

        for file in snapshot.files:
            if file.applied_sha256 is None:
                continue

            target_path = (
                root
                / file.relative_path
            ).resolve()

            try:
                current_content = (
                    read_text_exact(
                        target_path,
                    )
                    if target_path.is_file()
                    else None
                )

            except (OSError, UnicodeDecodeError):
                current_content = ""

                current_is_unreadable = True

            else:
                current_is_unreadable = False

            if current_is_unreadable:
                matches_known_state = False

            elif current_content is None:
                matches_known_state = not file.existed

            else:
                matches_known_state = (
                    _sha256(current_content) == file.applied_sha256
                    or (file.existed and current_content == file.content)
                )

            if not matches_known_state:
                raise EditConflictError(
                    "File changed after the edit was applied: "
                    f"{file.relative_path.as_posix()}. Rolling back "
                    "would overwrite those changes.",
                )

    def _create_snapshot(
        self,
        repository_root: Path,
        change_set: ChangeSet,
    ) -> Snapshot:
        """Create a ChangeSet-scoped snapshot."""

        repository_root = (
            repository_root.resolve()
        )

        files: list[SnapshotFile] = []

        for edit in change_set.edits:
            target_path = (
                repository_root
                / edit.relative_path
            ).resolve()

            current_content = read_text_for_edit(
                target_path,
                edit.relative_path,
            )

            existed = current_content is not None

            content = current_content or ""

            files.append(
                SnapshotFile(
                    relative_path=edit.relative_path,
                    existed=existed,
                    content=content,
                    applied_sha256=_sha256(
                        edit.updated_content,
                    ),
                ),
            )

        return Snapshot(
            files=files,
        )


def _sha256(
    content: str,
) -> str:
    """Return the SHA-256 hex digest of UTF-8 text."""

    return hashlib.sha256(
        content.encode(
            "utf-8",
        ),
    ).hexdigest()


def require_registered_root(
    repository_root: Path,
) -> None:
    """Reject roots that are missing or not registered RIP projects.

    Validated before any project-local storage is created, so an invalid
    root can never be materialized as a side effect. The registration
    check is the security boundary for every editing path: the caller
    chooses the root, so without it "stay inside the repository root"
    would not restrict anything.
    """

    root = repository_root.resolve()

    if not root.exists():
        raise EditingError(
            "Repository root does not exist.",
        )

    if not root.is_dir():
        raise EditingError(
            "Repository root is not a directory.",
        )

    if not is_registered_project(
        root,
    ):
        raise UnregisteredRepositoryError(
            "Repository root is not a registered RIP project. "
            "Initialize the project before editing it.",
        )
