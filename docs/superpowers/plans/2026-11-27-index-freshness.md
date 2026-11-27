# Index Freshness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Before every chat answer and semantic search, RIP updates the files that changed since the last index, waiting at most `RIP_INDEXING_REFRESH_SECONDS` (default 15), and says so when it could not finish.

**Architecture:** A new `IndexFreshness` service in the Indexing subsystem detects changed files (content hashes against the hashes stored with each chunk, with an mtime/size cache) and updates them through a new `IndexingService.update_files`, under the existing inter-process index lock, handing what is left to a per-project background thread. The chat routes, the semantic search route and the MCP `search_semantic` tool call it before handing off to `ChatService` / `RepositoryWorkspace`, which stay unchanged (ADR-0004, ADR-0012).

**Tech Stack:** Python 3.12, FastAPI, Pydantic, ChromaDB, pytest; React + TypeScript, TanStack Query, Vitest.

**Spec:** `docs/superpowers/specs/2026-11-27-index-freshness-design.md`

## Global Constraints

- No new dependencies (backend or frontend).
- `ChatService`, `RetrievalService` and `RepositoryWorkspace.search_semantic` never index (ADR-0004, ADR-0012); freshness is called **before** them, at the entry points.
- `project_index_lock` is the only writer gate; freshness never waits on it.
- Setting: `RIP_INDEXING_REFRESH_SECONDS`, int, default `15`; `0` = never update automatically (the change set is still reported).
- A freshness failure never fails the request: it is logged and becomes a `note`.
- An index built with a different embedding model is never rebuilt by freshness.
- Commit messages carry **no** AI attribution (no `Co-Authored-By`, no "Generated with"); this is the repository owner's standing rule.
- Run backend commands from `backend/`: `..\.venv\Scripts\python.exe -m pytest …`; frontend from `frontend/`: `npm test`.

## Review Focus

1. **Windows path separators.** Indexing stores `str(entry.relative_path)` (backslashes on Windows). The change set must compare paths in that same form, or every nested file looks changed forever. Test: a file in a subfolder is `up_to_date` after indexing (Task 3).
2. **A file disappears between scan and hash.** Expect it reported as removed, no exception. Test in Task 3.
3. **A file stops being text** (overwritten with binary) or becomes newly git-ignored. Expect it reported as removed and its chunks deleted. Tests in Task 3.
4. **The embedding provider is down during an update.** Expect the answer served from the current index with a note, failed files keeping their chunks, and the next request retrying. Test in Task 4.
5. **A chat request with no `root_directory`.** Expect no freshness call and no `event: index`. Test in Task 5.

---

### Task 1: File hashes from the vector store

**Files:**
- Modify: `backend/app/indexing/stores.py` (abstract `VectorStore`)
- Modify: `backend/app/indexing/chroma_store.py`
- Modify: `backend/app/indexing/indexer.py`
- Test: `backend/tests/indexing/test_freshness.py` (new; reuse `CountingEmbedder`, `resolver`, `project` and `_index` by importing them from `tests/indexing/test_incremental_indexing.py`, or move them to `tests/indexing/conftest.py` if importing between test modules is awkward)

**Interfaces:**
- Produces: `VectorStore.get_file_hashes(where: dict | None = None) -> dict[str, str] | None` (default implementation returns `None`, like `get_chunk_ids_by_path`); `ChromaVectorStore.get_file_hashes` returns `{relative_path: sha256}` from chunk metadata.
- Produces: `RepositoryIndexer.indexed_file_hashes(root_directory: str) -> dict[str, str]` (empty when there is no store, the store returns `None`, or a rebuild is pending).

- [ ] **Step 1: Write the failing test**

```python
def test_indexed_file_hashes_match_the_files(project, resolver):
    _index(project, CountingEmbedder(), resolver)
    indexer = RepositoryIndexer(embedding_provider=CountingEmbedder(), vector_store_resolver=resolver)

    hashes = indexer.indexed_file_hashes(str(project.resolve()))

    assert set(hashes) == {"main.py", "utils.py"}
    assert hashes["main.py"] == calculate_sha256(project / "main.py")
```

- [ ] **Step 2:** Run `..\.venv\Scripts\python.exe -m pytest tests/indexing/test_freshness.py -v`. Expected: FAIL, `AttributeError: … indexed_file_hashes`.
- [ ] **Step 3:** Implement the three methods. Chroma: `collection.get(where=where, include=["metadatas"])`, one entry per `relative_path` (all chunks of a file share `sha256`). Indexer: same guards as `existing_chunk_ids_by_path`, `where={"root_directory": root_directory}`.
- [ ] **Step 4:** Run the test. Expected: PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(indexing): read each indexed file's hash"`

---

### Task 2: Update a given set of files

**Files:**
- Modify: `backend/app/indexing/service.py`
- Modify: `backend/app/indexing/indexer.py`
- Modify: `backend/app/indexing/models.py`
- Test: `backend/tests/indexing/test_freshness.py`

**Interfaces:**
- Consumes: Task 1.
- Produces: `FileUpdateResult(BaseModel)` in `app/indexing/models.py`: `done: list[str]`, `remaining: list[str]`, `failed: list[str]`.
- Produces: `IndexingService.update_files(root_directory: Path, to_index: Sequence[str], to_remove: Sequence[str], deadline: float | None = None, clock: Callable[[], float] = time.monotonic) -> FileUpdateResult`. Paths are relative, in the stored form. Holds `project_index_lock` for the whole call and raises `IndexingBusyError` like `index_repository`. Processes `to_remove` first, then `to_index` in the given order; stops **starting** files once `clock() >= deadline`.
- Produces: `RepositoryIndexer.remove_paths(root_directory: str, relative_paths: Sequence[str]) -> int` (chunks deleted) and `RepositoryIndexer.remove_chunks_of_path_except(root_directory: str, relative_path: str, keep_chunk_ids: Collection[str]) -> int`.

- [ ] **Step 1: Write the failing tests**

```python
def test_update_files_embeds_only_the_edited_file(project, resolver):
    _index(project, CountingEmbedder(), resolver)
    (project / "main.py").write_text("def main():\n    return 'changed'\n", encoding="utf-8")
    embedder = CountingEmbedder()

    result = _service(embedder, resolver).update_files(project, ["main.py"], [])

    assert result.done == ["main.py"] and result.remaining == []
    assert all("changed" in text for text in embedder.embedded)
    assert not any("helper" in text for text in embedder.embedded)
    assert all("changed" in content for content in _contents(project, resolver, "main.py"))  # old chunk gone

def test_update_files_removes_deleted_files(project, resolver): ...
    # delete utils.py, update_files(project, [], ["utils.py"]) -> "utils.py" not in _indexed_paths

def test_update_files_stops_starting_files_at_the_deadline(project, resolver):
    ticks = iter([0.0, 0.0, 99.0, 99.0])  # second file starts after the deadline
    result = _service(CountingEmbedder(), resolver).update_files(
        project, ["main.py", "utils.py"], [], deadline=10.0, clock=lambda: next(ticks),
    )
    assert result.done == ["main.py"] and result.remaining == ["utils.py"]

def test_a_file_that_fails_keeps_its_chunks(project, resolver): ...
    # embedder raising on "changed" content -> result.failed == ["main.py"], old chunks still indexed
```

`_service(embedder, resolver)` builds `IndexingService` exactly like `_index` without calling it; `_contents` reads chunk documents for a path from the store. Add both helpers to the test module.

- [ ] **Step 2:** Run them. Expected: FAIL, `AttributeError: … update_files`.
- [ ] **Step 3:** Extract the per-file body of `_index_repository` (metadata, load, chunk, set `root_directory`, embed new chunk ids, record failures) into one private method that both `_index_repository` and `update_files` call; the existing `index_repository` tests must stay green unchanged. In `update_files`, after a file's new chunks are indexed, call `remove_chunks_of_path_except` with that file's current chunk ids. A file whose path no longer exists or is no longer text is treated as removed.
- [ ] **Step 4:** Run `..\.venv\Scripts\python.exe -m pytest tests/indexing -v`. Expected: all PASS, including the existing incremental-indexing tests.
- [ ] **Step 5: Commit** — `git commit -m "feat(indexing): update a given set of files"`

---

### Task 3: Detect changed files

**Files:**
- Create: `backend/app/indexing/freshness.py`
- Test: `backend/tests/indexing/test_freshness.py`

**Interfaces:**
- Consumes: Task 1 (`indexed_file_hashes`).
- Produces: `ChangeSet` (frozen dataclass): `changed: list[str]`, `added: list[str]`, `removed: list[str]`; property `to_index -> list[str]` (`changed + added`, most recently modified first), property `total -> int`.
- Produces: `FileHashCache` with `sha256(path: Path) -> str` keyed by `(path, st_mtime_ns, st_size)`; raises `OSError` if the file vanished.
- Produces: `detect_changes(root_directory: Path, scanner: RepositoryScanner, metadata_extractor: RepositoryMetadataExtractor, indexer: RepositoryIndexer, cache: FileHashCache) -> ChangeSet`. Current files = same selection as indexing: not a directory, `is_indexable_file_name`, `enrich_fast` says text. Paths as `str(entry.relative_path)`.

- [ ] **Step 1: Write the failing tests**

```python
def _changes(project, resolver, cache=None):
    return detect_changes(project.resolve(), RepositoryScanner(), RepositoryMetadataExtractor(),
                          RepositoryIndexer(embedding_provider=CountingEmbedder(), vector_store_resolver=resolver),
                          cache or FileHashCache())

def test_nothing_changed_right_after_indexing(project, resolver):
    (project / "pkg").mkdir(); (project / "pkg" / "deep.py").write_text("X = 1\n", encoding="utf-8")
    _index(project, CountingEmbedder(), resolver)
    assert _changes(project, resolver).total == 0          # Review Focus 1

def test_edit_add_and_delete_are_reported(project, resolver):
    _index(project, CountingEmbedder(), resolver)
    (project / "main.py").write_text("changed\n", encoding="utf-8")
    (project / "new.py").write_text("new\n", encoding="utf-8")
    (project / "utils.py").unlink()
    changes = _changes(project, resolver)
    assert (changes.changed, changes.added, changes.removed) == (["main.py"], ["new.py"], ["utils.py"])

def test_an_edit_that_is_undone_counts_as_unchanged(project, resolver): ...
def test_a_newly_ignored_file_is_removed(project, resolver): ...   # write .gitignore "utils.py" -> removed == ["utils.py"]  (Review Focus 3)
def test_a_file_that_becomes_binary_is_removed(project, resolver): ...  # write b"\x00\x01" to utils.py  (Review Focus 3)
def test_a_file_that_vanishes_while_hashing_is_removed(project, resolver, monkeypatch): ...
    # FileHashCache.sha256 raises FileNotFoundError for utils.py -> removed == ["utils.py"], no exception  (Review Focus 2)
def test_unchanged_files_are_not_read_again(project, resolver, monkeypatch): ...
    # count calls to the hashing function across two detect_changes with one cache -> second call hashes 0 files
```

- [ ] **Step 2:** Run them. Expected: FAIL, `ModuleNotFoundError: app.indexing.freshness`.
- [ ] **Step 3:** Implement `ChangeSet`, `FileHashCache`, `detect_changes` in `app/indexing/freshness.py`. A `.gitignore` itself is indexed like any other file; a `.gitignore` change therefore appears as `changed`, and the ignore rules are already applied by the scanner.
- [ ] **Step 4:** Run `..\.venv\Scripts\python.exe -m pytest tests/indexing/test_freshness.py -v`. Expected: PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(indexing): detect files changed since indexing"`

---

### Task 4: The freshness service and its setting

**Files:**
- Modify: `backend/app/indexing/freshness.py`
- Modify: `backend/app/indexing/models.py`
- Modify: `backend/app/core/config/models.py` (`IndexingSettings.refresh_seconds: int = 15`)
- Modify: `backend/app/core/config/provider.py` (`indexing_refresh_seconds: int = 15` → `IndexingSettings.refresh_seconds`)
- Modify: `backend/app/dependencies/providers.py` (`get_index_freshness()`, `lru_cache(maxsize=1)`)
- Modify: `.env.example`, `docs/reference/configuration.md` (the new setting, one row)
- Test: `backend/tests/indexing/test_freshness.py`

**Interfaces:**
- Consumes: Tasks 2 and 3.
- Produces in `app/indexing/models.py`: `FreshnessState(StrEnum)`: `up_to_date`, `updated`, `partial`, `busy`, `updating`, `off`, `not_indexed`, `incompatible`; `FreshnessResult(BaseModel)`: `state: FreshnessState`, `changed_files: int`, `added_files: int`, `removed_files: int`, `updated_files: int`, `pending_files: int`, `seconds: float`, `note: str | None = None`.
- Produces: `IndexFreshness(indexing_service, scanner, metadata_extractor, indexer, refresh_seconds: int, clock=time.monotonic)` with
  - `changes(root_directory: Path) -> ChangeSet | None` (`None` when not indexed or incompatible),
  - `refresh(root_directory: Path, changes: ChangeSet | None = None) -> FreshnessResult` (computes `changes` itself when not given),
  - `status(root_directory: Path) -> FreshnessResult` (never updates; `updating` while this process's background update for the root runs),
  - `wait_for_background(root_directory: Path, timeout: float) -> bool` (tests and the measurement only).
- Produces: `get_index_freshness() -> IndexFreshness`.

Notes (exact copy; `{n}` is the number of files not included):
- `partial`: `"The index is still updating; {n} changed files are not included in this answer."`
- `busy`: `"Another RIP process is updating the index; {n} changed files may not be included in this answer."`
- `off`: `"Automatic index updates are off; {n} files changed since indexing are not included."`
- failure: `"The index could not be updated ({error}); {n} changed files may not be included in this answer."`

- [ ] **Step 1: Write the failing tests** (build `IndexFreshness` over the Task 2 `_service` and a fake clock)

```python
def test_up_to_date_does_nothing(...):        # state == "up_to_date", embedder.embedded == []
def test_changes_are_updated_before_returning(...):  # edit main.py -> state "updated", updated_files == 1, then detect_changes total == 0
def test_past_the_limit_the_rest_finishes_in_the_background(...):
    # refresh_seconds=1 with a fake clock that jumps past the deadline after the first file; 3 edited files
    # -> state "partial", pending_files == 2, note == "The index is still updating; 2 changed files are not included in this answer."
    # -> wait_for_background(root, 10) is True, then detect_changes total == 0
def test_a_second_refresh_during_the_background_update_reports_partial(...):  # no lock attempt (monkeypatch update_files to fail if called)
def test_busy_lock_answers_without_waiting(monkeypatch, ...):  # update_files raises IndexingBusyError -> state "busy", note set, no background thread
def test_off_reports_the_change_set_only(...):  # refresh_seconds=0 -> state "off", nothing embedded
def test_not_indexed_and_incompatible_do_nothing(...):
def test_a_file_that_fails_to_embed_stays_pending(...):  # Review Focus 4: embedder raises -> state "partial", pending_files == 1, the partial note, old chunks kept, no background thread for failed files; a later refresh with a working embedder updates the file
def test_an_unexpected_error_becomes_the_failure_note(...):  # detect_changes raises RuntimeError("boom") -> no exception; note == "The index could not be updated (boom); 0 changed files may not be included in this answer."
def test_status_never_updates(...):
def test_refresh_seconds_setting(monkeypatch):  # RIP_INDEXING_REFRESH_SECONDS=7 -> read_environment(env_file=None) gives 7; default 15
```

- [ ] **Step 2:** Run them. Expected: FAIL (missing names).
- [ ] **Step 3:** Implement. Background: one `threading.Thread(daemon=True)` per resolved root, tracked in a dict guarded by a `threading.Lock`; it calls `update_files(root, remaining, [], deadline=None)` for the files the deadline left (`FileUpdateResult.remaining`, not `failed`) and logs (never raises) on failure. Files in `failed` count toward `pending_files` and are retried by the next `refresh`. Any exception inside `refresh` other than `IndexingBusyError` → log with `logger.exception`, return the failure note with `n` = the change set's total if known, else 0. Order of `to_index`: `ChangeSet.to_index` (most recently modified first); removals first.
- [ ] **Step 4:** Run `..\.venv\Scripts\python.exe -m pytest tests/indexing tests/core -v`. Expected: PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(indexing): update changed files before answering, up to a time limit"`

---

### Task 5: Call freshness at every semantic entry point (backend)

**Files:**
- Modify: `backend/app/api/routes/chat.py`, `backend/app/chat/schemas.py` (`ChatResponse.index: FreshnessResult | None = None`)
- Modify: `backend/app/api/routes/workspace.py` (semantic search; new `GET /index-status`)
- Modify: `backend/app/workspace/models.py` (`SemanticSearchResult.index: FreshnessResult | None = None`)
- Modify: `backend/app/mcp_server/server.py`, `backend/app/mcp_server/__main__.py` (pass `get_index_freshness()` into `build_server`)
- Test: `backend/tests/api/test_index_freshness_entry_points.py` (new), `backend/tests/mcp_server/test_server.py`

**Interfaces:**
- Consumes: `get_index_freshness()`, `IndexFreshness.changes/refresh/status`, `FreshnessResult`.
- Produces:
  - `POST /api/v1/chat`: when `root_directory` is set, `refresh` first; response `index` = the result.
  - `GET /api/v1/chat/stream`: inside the response generator, when `root_directory` is set: `changes = freshness.changes(root)`; if `changes is not None and changes.total > 0` emit `event: index-progress\ndata: {"files": changes.total}\n\n`; `result = freshness.refresh(root, changes)`; if `result.state != "up_to_date"` emit `event: index\ndata: <result JSON>\n\n`; then the existing unnamed `data:` chunks unchanged.
  - `GET /api/v1/workspace/search/semantic`: `refresh` then `workspace.search_semantic`; result `index` set.
  - `GET /api/v1/workspace/index-status?root_directory=…` (new, `operation_id="getIndexStatus"`) → `FreshnessResult` from `status`.
  - MCP: `build_server(..., index_freshness: IndexFreshness | None = None)`; `search_semantic` refreshes first and returns `index`; `index_status` returns `IndexStatus` plus a new `freshness: FreshnessResult | None` field (from `status`).

- [ ] **Step 1: Write the failing tests** — override `get_index_freshness` with a recording fake returning fixed results.

```python
ENTRY_POINTS = {("POST", "/api/v1/chat"), ("GET", "/api/v1/chat/stream"), ("GET", "/api/v1/workspace/search/semantic")}

def test_every_semantic_route_is_covered():
    # routes whose dependencies include get_chat_service, or whose path ends with "/semantic"
    assert _semantic_routes(app) == ENTRY_POINTS

def test_chat_refreshes_first_and_returns_the_result(...)      # fake called with root before ChatService.chat; body["index"]["state"] == "updated"
def test_stream_sends_progress_then_index_then_the_answer(...)   # body starts with "event: index-progress", then "event: index", then "data: …"
def test_stream_without_root_directory_skips_freshness(...)     # Review Focus 5: fake not called, no "event:" in body
def test_up_to_date_stream_sends_no_index_events(...)
def test_semantic_search_refreshes_first(...)
def test_index_status_route_reports_without_updating(...)       # fake.status called, fake.refresh not called
# tests/mcp_server/test_server.py:
def test_mcp_search_semantic_refreshes_first(...)
def test_mcp_index_status_includes_freshness(...)
```

- [ ] **Step 2:** Run `..\.venv\Scripts\python.exe -m pytest tests/api/test_index_freshness_entry_points.py tests/mcp_server -v`. Expected: FAIL.
- [ ] **Step 3:** Implement the routes and MCP changes. Freshness runs in the request's worker thread (the handlers are sync), never inside `ChatService` or `RepositoryWorkspace`. Update the stream route's OpenAPI example to show the two named events.
- [ ] **Step 4:** Run the full backend suite: `..\.venv\Scripts\python.exe -m pytest -q`, `..\.venv\Scripts\python.exe -m mypy app eval`, `..\.venv\Scripts\python.exe -m ruff check .`. Expected: all pass (the OpenAPI contract test may need the new route and fields added to its expectations).
- [ ] **Step 5: Commit** — `git commit -m "feat: update the index before chat and semantic search"`

---

### Task 6: Show it in the app

**Files:**
- Modify: `frontend/src/lib/sse/sseClient.ts` (+ `sseClient.test.ts`)
- Modify: `frontend/src/features/chat/ChatPage.tsx`
- Modify: `frontend/src/lib/api/endpoints.ts`, `frontend/src/lib/api/queries.ts`, API types file used by `endpoints.ts` (`FreshnessResult`, `getIndexStatus`)
- Modify: `frontend/src/features/dashboard/DashboardPage.tsx`
- Test: `frontend/src/lib/sse/sseClient.test.ts`, `frontend/src/features/chat/ChatPage.test.tsx` (new)

**Interfaces:**
- Consumes: the SSE events and `GET /workspace/index-status` from Task 5.
- Produces: `parseEvent(block: string): { event: string | null; data: string } | null`; `SseClientOptions.onEvent?: (event: string, data: string) => void` — named events go to `onEvent`, unnamed ones to `onMessage` exactly as before.

- [ ] **Step 1: Write the failing tests**

```ts
it("separates named events from answer text", () => {
  expect(parseEvent('event: index\ndata: {"state":"updated"}')).toEqual({ event: "index", data: '{"state":"updated"}' });
  expect(parseEvent("data: Hello")).toEqual({ event: null, data: "Hello" });
});
// ChatPage.test.tsx (mock createSseClient):
it("shows the update progress, then the note for a partial update", ...)
  // onEvent("index-progress", '{"files":3}') -> "Updating index (3 files)…" visible
  // onEvent("index", partial result with note) -> progress gone, note text visible above the answer
it("shows nothing for an update that finished", ...)
```

- [ ] **Step 2:** Run `npm test`. Expected: the new tests FAIL.
- [ ] **Step 3:** Implement. Dashboard "Indexing" tile: label from `getIndexStatus` for the active project — `up_to_date` "Up to date", `updating` "Updating", `off`/`partial`/`busy` "{changed+added+removed} files changed since indexing", `not_indexed` "Not indexed", `incompatible` "Needs reindex (different embedding model)"; no project → "No project".
- [ ] **Step 4:** Run `npm run typecheck`, `npm run lint`, `npm test`, `npm run build`. Expected: all pass.
- [ ] **Step 5: Commit** — `git commit -m "feat(frontend): show index updates in chat and the real index state"`

---

### Task 7: Measure, document, decide

**Files:**
- Create: `docs/adr/adr-0022-index-freshness.md` (decision: update before semantic queries, at the entry points, with a time limit; amends nothing; cites ADR-0004/0012/0013), and its row in `docs/adr/README.md`
- Modify: `docs/architecture/backend/indexing.md` (freshness section), `docs/architecture/backend/chat.md` (lifecycle: freshness before `ChatService`; "Measuring Answer Quality": round 3 results), `docs/architecture/backend/mcp-server.md` (`search_semantic`/`index_status` behavior, and that agents no longer need `reindex` after edits), `docs/roadmap/README.md` (Sprint 15 in progress → results)
- Modify: the MCP server instructions string in `backend/app/mcp_server/server.py` ("call reindex … after editing files" → semantic search updates changed files itself)

- [ ] **Step 1: Stale-index measurement.** Take the frozen snapshot used in Sprint 14 (`.eval-runs/snapshot`, local only), index it, then restore the 2026-11-25 versions of the files the four refused held-out questions need (`frontend/src/stores/authStore.ts`, `frontend/src/components/common/SignIn.tsx`, `backend/app/chat/ollama_provider.py`, `backend/app/llm/config.py`, `backend/app/main.py`, `backend/app/core/security/api_token.py`), reindex, then put the current versions back so the index is stale for exactly those files. Run the held-out answers twice with `RIP_INDEXING_REFRESH_SECONDS=0` and twice with the default.
  Expected: with `0`, the four questions are refused again; with `15`, coverage and refusals match the Sprint 14 fresh-index runs (66.7% / 61.7%, 0% refusals) within run-to-run noise.
- [ ] **Step 2: No-change cost.** Time `refresh` on RIP's repository with nothing changed: cold (new process) and warm (second call). Record both; warm must be under 0.5 s.
- [ ] **Step 3: Limit.** With `RIP_INDEXING_REFRESH_SECONDS=2` and ~50 edited files, record time to first answer chunk and that the note appears and the background update completes.
- [ ] **Step 4:** Write the ADR and the docs with the measured numbers (not targets). Update the MCP instructions string.
- [ ] **Step 5:** Full checks: backend `pytest`, `mypy app eval`, `ruff check .`; frontend `typecheck`, `lint`, `test`, `build`. Expected: all pass.
- [ ] **Step 6: Commit** — `git commit -m "docs: record index freshness (ADR-0022) and its measurements"`
