"""Repository Editing exceptions."""


class EditingError(Exception):
    """Base exception for the Editing subsystem."""


class InvalidRepositoryError(EditingError):
    """Repository root is invalid."""