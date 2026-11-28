"""Every semantic entry point updates the index before it answers."""

import json
import typing
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.editing import router as editing_router
from app.api.routes.health import router as health_router
from app.api.routes.models import router as models_router
from app.api.routes.projects import router as projects_router
from app.api.routes.repository import router as repository_router
from app.api.routes.system import router as system_router
from app.api.routes.workspace import router as workspace_router
from app.chat.models import ChatChunk, ChatRequest, ChatResponse
from app.chat.service import ChatService
from app.core.storage.locations import project_metadata_path
from app.dependencies.providers import (
    get_chat_service,
    get_index_freshness,
    get_proposal_service,
)
from app.editing.planner import EditPlanner
from app.editing.proposals import EditProposalView, ProposalSource, ProposalStatus
from app.indexing.exceptions import IndexIncompatibleError
from app.indexing.freshness import ChangeSet
from app.indexing.models import FreshnessResult, FreshnessState
from app.indexing.retrieval_service import RetrievalService
from app.main import app
from app.workspace.models import SemanticSearchResult

API_ROUTERS = (
    auth_router,
    chat_router,
    editing_router,
    health_router,
    models_router,
    projects_router,
    repository_router,
    system_router,
    workspace_router,
)
"""Every router app.api.router mounts under /api/v1."""

ENTRY_POINTS = {
    ("POST", "/api/v1/chat"),
    ("GET", "/api/v1/chat/stream"),
    ("GET", "/api/v1/workspace/search/semantic"),
    ("POST", "/api/v1/editing/proposals/plan"),
}
"""Routes that search the index semantically, so update it first."""

NO_SEMANTIC_SEARCH = {
    # The workspace holds a RetrievalService, but these routes only read
    # files, list them, search text or symbols, or report index status.
    ("GET", "/api/v1/workspace/file"),
    ("GET", "/api/v1/workspace/tree"),
    ("GET", "/api/v1/workspace/search/text"),
    ("GET", "/api/v1/workspace/symbols"),
    ("GET", "/api/v1/workspace/index-status"),
    # The proposal service holds the edit planner, but only /plan plans:
    # these store explicit operations, list, show, apply, reject or roll
    # back proposals, or manage validation.
    ("POST", "/api/v1/editing/proposals"),
    ("GET", "/api/v1/editing/proposals"),
    ("GET", "/api/v1/editing/proposals/{proposal_id}"),
    ("POST", "/api/v1/editing/proposals/{proposal_id}/apply"),
    ("POST", "/api/v1/editing/proposals/{proposal_id}/reject"),
    ("POST", "/api/v1/editing/proposals/{proposal_id}/rollback"),
    ("GET", "/api/v1/editing/validation"),
    ("PUT", "/api/v1/editing/validation"),
    ("POST", "/api/v1/editing/validation/run"),
}
"""Routes that reach a semantic consumer but never search with it."""

SEMANTIC_CONSUMERS = (RetrievalService, ChatService, EditPlanner)
"""Types that run, or plan with, semantic search."""


def _reaches_semantic_search(
    annotation: object,
    seen: set[type],
) -> bool:
    """True when a type is, or is built from, a semantic consumer.

    Follows constructor annotations, so ``RepositoryWorkspace`` (built
    with a RetrievalService) and ``ProposalService`` (built with the edit
    planner) count, whatever their routes are called.
    """

    candidates = typing.get_args(annotation) or (annotation,)

    for candidate in candidates:
        if not isinstance(candidate, type) or candidate in seen:
            continue

        seen.add(candidate)

        if issubclass(candidate, SEMANTIC_CONSUMERS):
            return True

        try:
            hints = typing.get_type_hints(candidate.__init__)
        except Exception:
            continue

        if any(
            _reaches_semantic_search(hint, seen)
            for name, hint in hints.items()
            if name != "return"
        ):
            return True

    return False


def _dependency_calls(dependant: Dependant) -> Iterator[Callable[..., object]]:
    for dependency in dependant.dependencies:
        if dependency.call is not None:
            yield dependency.call

        yield from _dependency_calls(dependency)


def _uses_semantic_consumer(route: APIRoute) -> bool:
    for call in _dependency_calls(route.dependant):
        try:
            returned = typing.get_type_hints(call).get("return")
        except Exception:
            continue

        if returned is not None and _reaches_semantic_search(returned, set()):
            return True

    return False


def _routes_with_semantic_consumers() -> set[tuple[str, str]]:
    """Every API route whose dependencies reach a semantic consumer."""

    routes = set()

    for router in API_ROUTERS:
        for route in router.routes:
            if isinstance(route, APIRoute) and _uses_semantic_consumer(route):
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


def test_every_route_with_a_semantic_consumer_is_classified() -> None:
    # A new route that depends on retrieval, chat or the edit planner
    # fails here until it is listed as an entry point (and refreshes) or
    # as one that never searches.
    assert not ENTRY_POINTS & NO_SEMANTIC_SEARCH
    assert _routes_with_semantic_consumers() == ENTRY_POINTS | NO_SEMANTIC_SEARCH


def test_detection_finds_routes_by_dependency_not_by_path() -> None:
    # The plan route neither uses ChatService nor ends in /semantic; it
    # reaches the planner through ProposalService.
    assert ("POST", "/api/v1/editing/proposals/plan") in (
        _routes_with_semantic_consumers()
    )


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


class FailingChatService(FakeChatService):
    def __init__(self, log: list[str], error: Exception) -> None:
        super().__init__(log)
        self.error = error

    def chat(self, request: ChatRequest) -> ChatResponse:
        raise self.error

    def stream(self, request: ChatRequest) -> Iterator[ChatChunk]:
        raise self.error


def _install_failing(log: list[str], error: Exception, result: FreshnessResult):
    fake = RecordingFreshness(log, result, ChangeSet(changed=["a.py"]))
    app.dependency_overrides[get_index_freshness] = lambda: fake
    app.dependency_overrides[get_chat_service] = lambda: FailingChatService(log, error)


def test_a_stream_error_after_the_update_becomes_an_error_event(log, tmp_path) -> None:
    error = IndexIncompatibleError("Index was built with another model.")
    _install_failing(log, error, UPDATED)

    http = TestClient(app).post(
        "/api/v1/chat",
        json={"query": "q", "root_directory": str(tmp_path)},
    )

    body = _stream(tmp_path)

    assert http.status_code == 409
    assert body.index("event: index\n") < body.index("event: error\n")

    event = body[body.index("event: error\n"):]
    data = json.loads(event.split("data: ", 1)[1].strip())

    assert data == {"status": http.status_code, "detail": http.json()["detail"]}
    assert body.endswith("\n\n")


def test_an_unexpected_stream_error_is_a_logged_generic_500(log, tmp_path, caplog) -> None:
    _install_failing(log, RuntimeError("secret internals"), UPDATED)

    with caplog.at_level("ERROR"):
        body = _stream(tmp_path)

    data = json.loads(body[body.index("event: error\n"):].split("data: ", 1)[1].strip())

    assert data == {"status": 500, "detail": "Internal Server Error"}
    assert "secret internals" not in body
    assert "secret internals" in caplog.text


def test_without_a_root_a_stream_error_is_still_an_http_status(log) -> None:
    _install_failing(log, IndexIncompatibleError("Wrong model."), UPDATED)

    response = TestClient(app).get(
        "/api/v1/chat/stream",
        params={"query": "q"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Wrong model."}


def test_the_router_list_matches_the_app() -> None:
    listed = {
        f"/api/v1{route.path}"
        for router in API_ROUTERS
        for route in router.routes
        if isinstance(route, APIRoute) and route.include_in_schema
    }

    assert listed == {
        path for path in app.openapi()["paths"] if path.startswith("/api/v1")
    }


class FakeProposalService:
    def __init__(self, log: list[str]) -> None:
        self.log = log

    def plan(
        self,
        repository_root: Path,
        instruction: str,
        files: list[str],
    ) -> EditProposalView:
        self.log.append("plan")
        now = datetime.now(UTC)
        return EditProposalView(
            proposal_id="p1",
            created_at=now,
            updated_at=now,
            status=ProposalStatus.PENDING,
            source=ProposalSource.PLANNER,
            description=instruction,
            files=[],
            diff="",
        )


def test_edit_planning_refreshes_first(log, tmp_path) -> None:
    fake = _install(log, UPDATED)
    app.dependency_overrides[get_proposal_service] = lambda: FakeProposalService(log)

    response = TestClient(app).post(
        "/api/v1/editing/proposals/plan",
        json={"repository_root": str(tmp_path), "instruction": "add a docstring"},
    )

    assert response.status_code == 200
    assert log == ["refresh", "plan"]
    assert fake.roots == [tmp_path.resolve()]
