"""Repository scanning exceptions."""


class RepositoryError(Exception):
    """Base repository exception."""


class RepositoryScanError(RepositoryError):
    """Raised when repository scanning fails."""