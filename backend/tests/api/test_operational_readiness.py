"""Operational readiness certification tests."""

from pathlib import Path

import pytest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import main
from app.chat.exceptions import ChatException
from app.core.config.provider import get_settings
from app.core.storage.exceptions import (
    StorageInitializationError,
)
from app.core.storage.filesystem import (
    FileSystemStorage,
)
from app.dependencies import providers
from app.editing.exceptions import EditingError
from app.indexing.exceptions import IndexingError
from app.projects.exceptions import InvalidProjectError
from app.repository.exceptions import RepositoryScanError


class RecordingLogger:
    """Logger that records lifecycle events."""

    def __init__(
        self,
    ) -> None:
        """Initialize event storage."""

        self.events: list[str] = []

    def info(
        self,
        event: str,
    ) -> None:
        """Record an info event."""

        self.events.append(
            event,
        )


def test_application_factory_configures_logging(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Application creation should configure structured logging."""

    calls: list[tuple[str, bool]] = []

    def fake_configure_logging(
        level: str,
        json_logs: bool,
    ) -> None:
        calls.append(
            (
                level,
                json_logs,
            ),
        )

    monkeypatch.setattr(
        main,
        "configure_logging",
        fake_configure_logging,
        raising=False,
    )

    main.create_application()

    assert calls == [
        (
            main.settings.logging.level,
            main.settings.logging.json_logs,
        ),
    ]


def test_application_lifespan_logs_startup_and_shutdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Application lifespan should emit startup and shutdown events."""

    recording_logger = RecordingLogger()

    monkeypatch.setattr(
        main,
        "logger",
        recording_logger,
    )

    application = main.create_application()

    with TestClient(
        application,
    ) as client:
        response = client.get(
            "/api/v1/health",
        )

        assert (
            response.status_code
            == 200
        )

    assert recording_logger.events == [
        "application_started",
        "application_stopped",
    ]


def test_application_factory_registers_routes_and_openapi() -> None:
    """Application factory should register all public API routes."""

    application = main.create_application()

    schema = application.openapi()

    assert set(
        schema["paths"],
    ) == {
        "/api/v1/health",
        "/api/v1/projects/open",
        "/api/v1/projects/info",
        "/api/v1/repository/index",
        "/api/v1/repository/scan",
        "/api/v1/repository/summary",
        "/api/v1/models",
        "/api/v1/settings/model",
        "/api/v1/system/status",
        "/api/v1/system/capabilities",
        "/api/v1/system/version",
        "/api/v1/chat",
        "/api/v1/chat/stream",
        "/api/v1/editing/edit",
        "/api/v1/editing/apply",
        "/api/v1/editing/rollback",
    }


def test_application_factory_registers_exception_handlers() -> None:
    """Application factory should register domain exception handlers."""

    application = main.create_application()

    for exception_type in (
        InvalidProjectError,
        RepositoryScanError,
        EditingError,
        ChatException,
        IndexingError,
    ):
        assert (
            exception_type
            in application.exception_handlers
        )


def test_health_endpoint_is_ready_after_startup() -> None:
    """Health endpoint should be available after application startup."""

    with TestClient(
        main.create_application(),
    ) as client:
        response = client.get(
            "/api/v1/health",
        )

    assert (
        response.status_code
        == 200
    )

    assert response.json() == {
        "status": "healthy",
        "application": "Repository Intelligence Platform (RIP)",
        "version": "0.1.0",
    }


def test_no_custom_middleware_is_registered() -> None:
    """Middleware stack should remain explicit and unchanged."""

    application = main.create_application()

    middleware_classes = [
        m.cls
        for m in application.user_middleware
    ]

    assert middleware_classes == [
        CORSMiddleware,
    ]


def test_dependency_providers_are_cached_and_wired() -> None:
    """Core dependency providers should return stable singleton services."""

    providers.get_project_service.cache_clear()
    providers.get_repository_service.cache_clear()
    providers.get_editing_service.cache_clear()

    assert (
        providers.get_project_service()
        is providers.get_project_service()
    )

    assert (
        providers.get_repository_service()
        is providers.get_repository_service()
    )

    assert (
        providers.get_editing_service()
        is providers.get_editing_service()
    )


def test_environment_configuration_overrides(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Environment variables should override default settings."""

    get_settings.cache_clear()

    monkeypatch.setenv(
        "LOC_SERVER_PORT",
        "9123",
    )
    monkeypatch.setenv(
        "LOC_STORAGE_ROOT_DIRECTORY",
        str(
            tmp_path
            / "storage",
        ),
    )

    settings = get_settings()

    assert (
        settings.server.port
        == 9123
    )

    assert (
        settings.storage.root_directory
        == tmp_path
        / "storage"
    )

    get_settings.cache_clear()


def test_invalid_environment_configuration_fails_startup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid environment settings should fail during settings creation."""

    get_settings.cache_clear()

    monkeypatch.setenv(
        "LOC_SERVER_PORT",
        "not-an-integer",
    )

    with pytest.raises(
        ValidationError,
    ):
        get_settings()

    get_settings.cache_clear()


def test_storage_initialization_creates_directory(
    tmp_path: Path,
) -> None:
    """Storage initialization should create the configured root directory."""

    storage_root = (
        tmp_path
        / "storage"
    )

    storage = FileSystemStorage(
        root_directory=storage_root,
    )

    storage.initialize()

    assert storage_root.is_dir()


def test_storage_initialization_failure_is_translated(
    tmp_path: Path,
) -> None:
    """Storage initialization failures should use storage exceptions."""

    storage_root = (
        tmp_path
        / "storage"
    )

    storage_root.write_text(
        "",
        encoding="utf-8",
    )

    storage = FileSystemStorage(
        root_directory=storage_root,
    )

    with pytest.raises(
        StorageInitializationError,
    ):
        storage.initialize()
