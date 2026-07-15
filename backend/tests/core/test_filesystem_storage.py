"""Tests for filesystem-backed storage reliability."""

from pathlib import Path

import pytest

from app.core.storage.exceptions import (
    StorageReadError,
)
from app.core.storage.filesystem import (
    FileSystemStorage,
)


def test_read_json_rejects_malformed_json(
    tmp_path: Path,
) -> None:
    """Malformed JSON should be translated to a storage read error."""

    storage = FileSystemStorage(
        root_directory=tmp_path,
    )

    storage.initialize()

    (
        tmp_path
        / "broken.json"
    ).write_text(
        "{not-json",
        encoding="utf-8",
    )

    with pytest.raises(
        StorageReadError,
    ):
        storage.read_json(
            Path(
                "broken.json",
            ),
        )
