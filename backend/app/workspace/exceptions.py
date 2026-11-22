"""Repository Workspace exceptions."""


class WorkspaceError(Exception):
    """Base exception for workspace operations (HTTP 400)."""


class UnregisteredWorkspaceError(WorkspaceError):
    """The root is not a registered RIP project (HTTP 403)."""


class WorkspacePathError(WorkspaceError):
    """A path is absolute, escapes the root, or is protected (HTTP 400)."""


class WorkspaceFileNotFoundError(WorkspaceError):
    """The requested file or directory does not exist (HTTP 404)."""


class FileTooLargeError(WorkspaceError):
    """The file exceeds the size a tool will read (HTTP 413)."""


class NotATextFileError(WorkspaceError):
    """The file is binary or not valid UTF-8 (HTTP 415)."""
