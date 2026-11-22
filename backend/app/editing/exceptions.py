"""Repository Editing exceptions."""


class EditingError(Exception):
    """Base exception for the Editing subsystem."""


class InvalidRepositoryError(EditingError):
    """Repository root is invalid."""


class UnregisteredRepositoryError(EditingError):
    """Repository root is not a registered RIP project.

    Editing operations only act on roots that contain project metadata
    (``<root>/.local_openclaw/project.json``). Without this check, any
    caller could choose an arbitrary directory as the "repository" and
    write anywhere on disk.
    """


class EditConflictError(EditingError):
    """A file changed between planning and apply, or after apply.

    Raised instead of silently overwriting changes that the edit plan or
    snapshot did not account for.
    """


class IncompleteRevertError(EditingError):
    """A failed apply could not restore every file it had written."""


class SnapshotNotFoundError(EditingError):
    """Snapshot could not be found."""


class SnapshotPersistenceError(EditingError):
    """Snapshot persistence failed."""
