"""Every semantic entry point updates the index before it answers."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.api.routes.chat import router as chat_router
from app.api.routes.workspace import router as workspace_router
from app.chat.models import ChatChunk, ChatRequest, ChatResponse
from app.core.storage.locations import project_metadata_path
from app.dependencies.providers import (
    get_chat_service,
    get_index_freshness,
)
from app.indexing.freshness import ChangeSet
from app.indexing.models import FreshnessResult, FreshnessState
from app.main import app
from app.workspace.models import SemanticSearchResult

ENTRY_POINTS = {
    ("POST", "/api/v1/chat"),
    ("GET", "/api/v1/chat/stream"),
    ("GET", "/api/v1/workspace/search/semantic"),
}


def _semantic_routes() -> set[tuple[str, str]]:
    """Routes that reach semantic search: they use ChatService or end in /semantic."""

    routes = set()

    for router in (chat_router, workspace_router):
        for route in router.routes:
            if not isinstance(route, APIRoute):
                continue

            calls = {dependency.call for dependency in route.dependant.dependencies}

            if get_chat_service in calls or route.path.endswith("/semantic"):
                for method in route.methods:
                    routes.add((method, f"/api/v1{route.path}"))

    return routes


def _result(state: FreshnessState, **fields: object) -> FreshnessResult:
    return FreshnessResult(state=state, **fields)


class RecordingFreshness:
    """Records calls in a shared log and returns fixed results."""

    def __init__(
        self,
        log: list[str],
        result: FreshnessResult,
        changes: ChangeSet | None = None,
    ) -> None:
        self.log = log
        self.result = result
        self._changes = changes
        self.roots: list[Path] = []

    def changes(self, root: Path) -> ChangeSet | None:
        self.log.append("changes")
        return self._changes

    def refresh(self, root: Path, changes: ChangeSet | None = None) -> FreshnessResult:
        self.log.append("refresh")
        self.roots.append(root)
        return self.result

    def status(self, root: Path) -> FreshnessResult:
        self.log.append("status")
        return self.result


class FakeChatService:
    def __init__(self, log: list[str]) -> None:
        self.log = log

    def chat(self, request: ChatRequest) -> ChatResponse:
        self.log.append("answer")
        return ChatResponse(content="the answer")

    def stream(self, request: ChatRequest) -> Iterator[ChatChunk]:
        self.log.append("answer")
        yield ChatChunk(content="Hello", is_final=False)
        yield ChatChunk(content="!", is_final=True)


@pytest.fixture(autouse=True)
def _clean_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def log() -> list[str]:
    return []


def _install(
    log: list[str],
    result: FreshnessResult,
    changes: ChangeSet | None = None,
) -> RecordingFreshness:
    fake = RecordingFreshness(log, result, changes)
    app.dependency_overrides[get_index_freshness] = lambda: fake
    app.dependency_overrides[get_chat_service] = lambda: FakeChatService(log)
    return fake


def _stream(root: Path | None) -> str:
    params = {"query": "q"}

    if root is not None:
        params["root_directory"] = str(root)

    with TestClient(app).stream(
        "GET",
        "/api/v1/chat/stream",
        params=params,
    ) as response:
        assert response.status_code == 200

        return "".join(response.iter_text())


UPDATED = _result(FreshnessState.UPDATED, changed_files=2, updated_files=2)


def test_every_semantic_route_is_covered() -> None:
    assert _semantic_routes() == ENTRY_POINTS


def test_chat_refreshes_first_and_returns_the_result(log, tmp_path) -> None:
    fake = _install(log, UPDATED)

    response = TestClient(app).post(
        "/api/v1/chat",
        json={"query": "q", "root_directory": str(tmp_path)},
    )

    assert response.status_code == 200
    assert log == ["refresh", "answer"]
    assert fake.roots == [tmp_path]
    assert response.json()["index"]["state"] == "updated"


def test_chat_without_root_directory_skips_freshness(log) -> None:
    _install(log, UPDATED)

    response = TestClient(app).post("/api/v1/chat", json={"query": "q"})

    assert response.status_code == 200
    assert log == ["answer"]
    assert response.json()["index"] is None


def test_stream_sends_progress_then_index_then_the_answer(log, tmp_path) -> None:
    _install(log, UPDATED, ChangeSet(changed=["a.py", "b.py"]))

    body = _stream(tmp_path)

    assert log == ["changes", "refresh", "answer"]
    assert body.startswith('event: index-progress\ndata: {"files": 2}\n\n')

    progress_end = body.index("event: index\n")
    assert progress_end > 0

    index_event, _, rest = body[progress_end:].partition("\n\n")
    assert index_event.startswith('event: index\ndata: {"state":"updated"')
    assert rest == "data: Hello\n\ndata: !\n\n"


def test_stream_without_root_directory_skips_freshness(log) -> None:
    _install(log, UPDATED, ChangeSet(changed=["a.py"]))

    body = _stream(None)

    assert log == ["answer"]
    assert "event:" not in body
    assert body == "data: Hello\n\ndata: !\n\n"


@pytest.mark.parametrize(
    "state",
    [
        FreshnessState.UP_TO_DATE,
        FreshnessState.NOT_INDEXED,
        FreshnessState.INCOMPATIBLE,
    ],
)
def test_quiet_states_send_no_index_events(log, tmp_path, state) -> None:
    _install(log, _result(state))

    body = _stream(tmp_path)

    assert log == ["changes", "refresh", "answer"]
    assert "event:" not in body
    assert body == "data: Hello\n\ndata: !\n\n"


def test_a_partial_result_is_reported_in_the_stream(log, tmp_path) -> None:
    _install(
        log,
        _result(FreshnessState.PARTIAL, pending_files=3, note="still updating"),
    )

    body = _stream(tmp_path)

    assert "event: index-progress" not in body
    assert "event: index\n" in body
    assert "still updating" in body


@pytest.fixture
def project(tmp_path: Path) -> Path:
    metadata_path = project_metadata_path(tmp_path)
    metadata_path.parent.mkdir(parents=True)
    metadata_path.write_bytes(b"{}")
    return tmp_path


def test_semantic_search_refreshes_first(log, project, monkeypatch) -> None:
    fake = _install(log, UPDATED)

    from app.workspace.service import RepositoryWorkspace

    def search(self, query: str, limit: int = 10) -> SemanticSearchResult:
        log.append("search")
        return SemanticSearchResult(indexed=True, hits=[])

    monkeypatch.setattr(RepositoryWorkspace, "search_semantic", search)

    response = TestClient(app).get(
        "/api/v1/workspace/search/semantic",
        params={"root_directory": str(project), "query": "q"},
    )

    assert response.status_code == 200
    assert log == ["refresh", "search"]
    assert fake.roots == [project.resolve()]
    assert response.json()["index"]["state"] == "updated"


def test_index_status_route_reports_without_updating(log, project) -> None:
    fake = _install(
        log,
        _result(FreshnessState.STALE, changed_files=1, pending_files=1),
    )

    response = TestClient(app).get(
        "/api/v1/workspace/index-status",
        params={"root_directory": str(project)},
    )

    assert response.status_code == 200
    assert response.json()["state"] == "stale"
    assert log == ["status"]
    assert fake.roots == []
