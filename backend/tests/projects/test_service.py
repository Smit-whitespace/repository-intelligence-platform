"""Tests for opening projects."""

import json
from pathlib import Path

from app.core.storage.locations import project_metadata_path
from app.projects.repository import ProjectRepository
from app.projects.service import ProjectService


def test_reopening_a_project_keeps_its_creation_time(
    tmp_path: Path,
) -> None:
    """Opening a project again used to reset "Created" to now."""

    service = ProjectService(
        repository=ProjectRepository(),
    )

    first = service.open_project(
        tmp_path,
    )

    second = service.open_project(
        tmp_path,
    )

    assert second.created_at == first.created_at

    assert service.get_project(tmp_path).created_at == first.created_at


def test_unreadable_metadata_is_replaced_on_open(
    tmp_path: Path,
) -> None:
    """A broken project.json must not stop a project from opening."""

    metadata = project_metadata_path(
        tmp_path,
    )

    metadata.parent.mkdir(
        parents=True,
    )

    metadata.write_text(
        "{not json",
        encoding="utf-8",
    )

    project = ProjectService(
        repository=ProjectRepository(),
    ).open_project(
        tmp_path,
    )

    assert json.loads(metadata.read_text(encoding="utf-8"))["name"] == project.name
