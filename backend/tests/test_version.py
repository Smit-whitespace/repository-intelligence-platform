"""The version is written in three files; they must agree."""

import json
import tomllib
from pathlib import Path

from app.core.version import APPLICATION_VERSION

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_pyproject_matches_application_version() -> None:
    pyproject = tomllib.loads(
        (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"),
    )

    assert pyproject["project"]["version"] == APPLICATION_VERSION


def test_frontend_package_matches_application_version() -> None:
    frontend = REPOSITORY_ROOT / "frontend"
    package = json.loads(
        (frontend / "package.json").read_text(encoding="utf-8"),
    )
    lock = json.loads(
        (frontend / "package-lock.json").read_text(encoding="utf-8"),
    )

    assert package["version"] == APPLICATION_VERSION
    assert lock["version"] == APPLICATION_VERSION
    assert lock["packages"][""]["version"] == APPLICATION_VERSION
