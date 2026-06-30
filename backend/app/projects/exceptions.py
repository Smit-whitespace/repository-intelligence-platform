"""Project management exceptions."""


class ProjectError(Exception):
    """Base project exception."""


class ProjectNotFoundError(ProjectError):
    """Raised when a project cannot be found."""


class InvalidProjectError(ProjectError):
    """Raised when a directory is not a valid project."""