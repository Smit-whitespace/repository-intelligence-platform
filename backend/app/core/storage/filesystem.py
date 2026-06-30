"""Filesystem-backed storage implementation."""

import json
import shutil
from pathlib import Path
from typing import Any

from app.core.storage.abstractions import StorageProvider
from app.core.storage.exceptions import (
    StorageError,
    StorageInitializationError,
    StorageReadError,
    StorageResourceNotFoundError,
    StorageWriteError,
)


class FileSystemStorage(StorageProvider):
    """Filesystem-backed storage provider."""

    def __init__(
        self,
        root_directory: Path,
    ) -> None:
        """Initialize the filesystem storage provider."""

        self._root_directory = root_directory.resolve()

    def _resolve_path(
        self,
        path: Path,
    ) -> Path:
        """Resolve a storage path within the configured storage root."""

        resolved_path = (
            self._root_directory / path
        ).resolve()

        try:
            resolved_path.relative_to(
                self._root_directory,
            )
        except ValueError as error:
            raise StorageError(
                f"Path escapes storage root: {path}"
            ) from error

        return resolved_path

    def _ensure_parent_directory(
        self,
        path: Path,
    ) -> None:
        """Ensure the parent directory exists."""

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def initialize(
        self,
    ) -> None:
        """Initialize the storage root directory."""

        try:
            self._root_directory.mkdir(
                parents=True,
                exist_ok=True,
            )
        except OSError as error:
            raise StorageInitializationError(
                f"Failed to initialize storage root: "
                f"{self._root_directory}"
            ) from error

    def exists(
        self,
        path: Path,
    ) -> bool:
        """Return whether a storage resource exists."""

        return self._resolve_path(path).exists()

    def create_directory(
        self,
        path: Path,
    ) -> None:
        """Create a storage directory."""

        self._resolve_path(path).mkdir(
            parents=True,
            exist_ok=True,
        )

    def read_text(
        self,
        path: Path,
    ) -> str:
        """Read UTF-8 text from storage."""

        resolved_path = self._resolve_path(path)

        if not resolved_path.exists():
            raise StorageResourceNotFoundError(
                f"Storage resource not found: {path}"
            )

        try:
            return resolved_path.read_text(
                encoding="utf-8",
            )
        except OSError as error:
            raise StorageReadError(
                f"Failed to read storage resource: {path}"
            ) from error

    def write_text(
        self,
        path: Path,
        content: str,
    ) -> None:
        """Write UTF-8 text to storage using an atomic write."""

        resolved_path = self._resolve_path(path)

        self._ensure_parent_directory(
            resolved_path,
        )

        temporary_path = resolved_path.with_suffix(
            resolved_path.suffix + ".tmp",
        )

        try:
            temporary_path.write_text(
                content,
                encoding="utf-8",
            )

            temporary_path.replace(
                resolved_path,
            )

        except OSError as error:
            raise StorageWriteError(
                f"Failed to write storage resource: {path}"
            ) from error

    def read_json(
        self,
        path: Path,
    ) -> dict[str, Any]:
        """Read JSON data from storage."""

        try:
            return json.loads(
                self.read_text(path),
            )
        except json.JSONDecodeError as error:
            raise StorageReadError(
                f"Invalid JSON in storage resource: {path}"
            ) from error

    def write_json(
        self,
        path: Path,
        data: dict[str, Any],
    ) -> None:
        """Write JSON data to storage."""

        self.write_text(
            path=path,
            content=json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ),
        )

    def delete(
        self,
        path: Path,
    ) -> None:
        """Delete a storage resource."""

        resolved_path = self._resolve_path(path)

        if not resolved_path.exists():
            raise StorageResourceNotFoundError(
                f"Storage resource not found: {path}"
            )

        try:
            if resolved_path.is_dir():
                shutil.rmtree(
                    resolved_path,
                )
            else:
                resolved_path.unlink()

        except OSError as error:
            raise StorageWriteError(
                f"Failed to delete storage resource: {path}"
            ) from error