"""Storage-related exceptions."""


class StorageError(Exception):
    """Base storage exception."""


class StorageInitializationError(StorageError):
    """Raised when storage initialization fails."""


class StorageReadError(StorageError):
    """Raised when a storage read operation fails."""


class StorageWriteError(StorageError):
    """Raised when a storage write operation fails."""


class StorageResourceNotFoundError(StorageError):
    """Raised when a requested storage resource does not exist."""