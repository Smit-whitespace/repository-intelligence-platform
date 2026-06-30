"""Storage provider abstractions."""

from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import Any


class StorageProvider(ABC):
    """Abstract storage provider interface."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize storage resources."""

    @abstractmethod
    def exists(
        self,
        path: Path,
    ) -> bool:
        """Return whether a path exists."""

    @abstractmethod
    def create_directory(
        self,
        path: Path,
    ) -> None:
        """Create a directory."""

    @abstractmethod
    def read_text(
        self,
        path: Path,
    ) -> str:
        """Read text content."""

    @abstractmethod
    def write_text(
        self,
        path: Path,
        content: str,
    ) -> None:
        """Write text content."""

    @abstractmethod
    def read_json(
        self,
        path: Path,
    ) -> dict[str, Any]:
        """Read JSON data."""

    @abstractmethod
    def write_json(
        self,
        path: Path,
        data: dict[str, Any],
    ) -> None:
        """Write JSON data."""

    @abstractmethod
    def delete(
        self,
        path: Path,
    ) -> None:
        """Delete a file or directory."""