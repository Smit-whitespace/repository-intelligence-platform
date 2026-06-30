"""Repository scanner implementation."""

import os
from pathlib import Path

from app.repository.exceptions import RepositoryScanError
from app.repository.ignore import should_ignore
from app.repository.models import RepositoryEntry


class RepositoryScanner:
    """Repository filesystem scanner."""

    def scan(
        self,
        root_directory: Path,
    ) -> list[RepositoryEntry]:
        """Scan a repository."""

        root_directory = root_directory.resolve()

        if not root_directory.exists():
            raise RepositoryScanError(
                f"Repository does not exist: {root_directory}"
            )

        if not root_directory.is_dir():
            raise RepositoryScanError(
                f"Repository is not a directory: {root_directory}"
            )

        entries: list[RepositoryEntry] = []

        for current_root, directories, files in os.walk(
            root_directory,
        ):
            current_path = Path(current_root)

            directories[:] = [
                directory
                for directory in directories
                if not should_ignore(
                    current_path / directory,
                )
            ]

            for directory in directories:
                absolute_path = current_path / directory

                entries.append(
                    RepositoryEntry(
                        name=directory,
                        absolute_path=absolute_path,
                        relative_path=absolute_path.relative_to(
                            root_directory,
                        ),
                        is_directory=True,
                    )
                )

            for file_name in files:
                absolute_path = current_path / file_name

                if should_ignore(
                    absolute_path,
                ):
                    continue

                entries.append(
                    RepositoryEntry(
                        name=file_name,
                        absolute_path=absolute_path,
                        relative_path=absolute_path.relative_to(
                            root_directory,
                        ),
                        is_directory=False,
                    )
                )

        return sorted(
            entries,
            key=lambda entry: entry.relative_path.as_posix(),
        )