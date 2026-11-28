# Sprint 15 — Index Freshness

## Sprint Objective

Make every answer and every semantic search reflect the files as they are now. In Sprint 14, an index one day older than the code made the model refuse 27% of held-out questions, and a fresh index raised held-out coverage more than any prompt change did. RIP now updates the files that changed since indexing before it answers, waits at most a time limit, finishes the rest in the background, and says so whenever an answer could not include them.

## Architecture Changes

No subsystem boundaries moved. ChatService and RetrievalService still never index (ADR-0004, ADR-0012); the entry points call freshness first, following ADR-0013's orchestration pattern ([ADR-0022](../adr/adr-0022-index-freshness.md)):

```
Before Sprint 15:
    Index built or refreshed only on project open or MCP reindex
    Chat / semantic search / edit planning / MCP search_semantic → RetrievalService (index as it is)
    Dashboard "Indexing" tile: hardcoded "available"

After Sprint 15:
    Chat (POST, stream) / semantic search / edit planning / MCP search_semantic
        → IndexFreshness.refresh(root)
            detect_changes: content hashes on disk vs stored hashes (mtime/size cache)
            IndexingService.update_files: changed files only, under project_index_lock,
                until RIP_INDEXING_REFRESH_SECONDS (default 15; 0 = off)
            the rest: one background thread per project
        → RetrievalService / ChatService (unchanged)
    Responses carry an `index` result; the chat stream sends index-progress / index / error events
    GET /workspace/index-status and MCP index_status report the state without updating
    Dashboard "Indexing" tile shows the real state
```

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `backend/app/indexing/freshness.py` | Created | Change detection, hash cache, `IndexFreshness` (refresh, status, background update) |
| `backend/app/indexing/service.py` | Modified | `update_files` with a deadline; one per-file step shared with full indexing; stops on a model change |
| `backend/app/indexing/indexer.py`, `chroma_store.py`, `stores.py` | Modified | Stored file hashes; removing a file's chunks; model check before writing |
| `backend/app/indexing/models.py`, `exceptions.py`, `lock.py` | Modified | `FreshnessState`, `FreshnessResult`, `FileUpdateResult`; neutral busy wording |
| `backend/app/repository/chunking.py` | Modified | `yields_no_chunks`: empty non-Python files are not counted as changed |
| `backend/app/api/routes/chat.py`, `workspace.py`, `editing.py` | Modified | Freshness before answering, searching and planning; `GET /workspace/index-status` |
| `backend/app/api/exception_handlers.py` | Modified | One status table, shared with the stream's `event: error` |
| `backend/app/mcp_server/server.py` | Modified | `search_semantic` refreshes first; `index_status` reports freshness; instructions updated |
| `backend/app/core/config/*`, `.env.example` | Modified | `RIP_INDEXING_REFRESH_SECONDS` |
| `frontend/src/features/chat/ChatPage.tsx`, `lib/sse/sseClient.ts` | Modified | Named stream events; "Updating index (N files)…"; a note under the answer |
| `frontend/src/features/dashboard/*`, `lib/api/queries.ts`, `features/projects/ProjectsPage.tsx` | Modified/Created | Real index state on the Dashboard, kept current |
| `backend/tests/api/test_index_freshness_entry_points.py` | Created | Every route that depends on retrieval, chat or the planner goes through freshness |
| `docs/adr/adr-0022-index-freshness.md` | Created | The decision |
| `docs/architecture/backend/indexing.md`, `chat.md`, `mcp-server.md`, `editing.md` | Modified | Freshness section, stream events, Round 3 results |

## Vertical Slices

| Slice | Scope | Status |
|-------|-------|--------|
| 1 — Stored hashes | The index reports each file's content hash | ✅ |
| 2 — Update given files | `update_files`: changed files only, file by file, up to a deadline | ✅ |
| 3 — Change detection | Edited, new, deleted and newly ignored files, by content hash, with a cache | ✅ |
| 4 — Freshness step | `refresh` / `status`, background update, notes; never fails a question | ✅ |
| 5 — Entry points | Chat, semantic search, edit planning, MCP; coverage test | ✅ |
| 6 — App | Progress line, notes, real Dashboard state | ✅ |
| 7 — Measurement | Held-out answers on a stale index, no-change cost, time limit | ✅ |

## Validation Results

| Gate | Result | Notes |
|------|--------|-------|
| Ruff | ✅ All checks passed | — |
| MyPy | ✅ No issues (`app`, `eval`) | — |
| Pytest | ✅ 672 passed, 2 skipped | — |
| Frontend | ✅ typecheck, ESLint, build, 60 Vitest tests | — |
| CI | ✅ Backend and Frontend on PR #16 | — |

Measured ([Round 3](../architecture/backend/chat.md#measuring-answer-quality)):

| Held-out set, deliberately stale index | Run 1 | Run 2 |
|---|---|---|
| Automatic updates off | 53.9% | 56.7% |
| Automatic updates on | 65.6% | 65.0% |
| Freshly built index | 66.7% | 61.7% |

- Refusals were 0% in every run; the stale index cost coverage instead, mostly files cited (63% → 37%).
- A check with nothing changed, on RIP's own repository: 0.12 s warm, 0.53 to 0.64 s in a fresh process.
- With a 2 s limit and 50 edited files, the first answer was ready after 2.41 s with 47 files pending; the background finished them in 47.6 s.

## Known Technical Debt

- A file that was indexed and later cannot be indexed (for example, edited into invalid UTF-8) keeps its old chunks until it is edited again.
- `freshness.py` holds both change detection and the freshness step (about 760 lines); the indexing tests repeat some helpers.
- The first answer's start was not timed separately from the update; only the update's time was measured.
- `ruff format --check` fails across the repository; CI does not run it.

## Deferred Work

- **Why answers still miss.** With a current index, held-out coverage sits at about 62–67%. The next step is to record, for each miss, whether retrieval returned the expected files, to decide between retrieval and context changes.
- **Deeper explanations** (from Sprint 14), still open.
- **`SignIn.tsx` search miss** (from Sprint 14), still open.

## Lessons Learned

- **A measurement has to go through the path users take.** The answer runner calls ChatService directly, bypassing the routes, so it measured nothing about freshness until it called `refresh` itself, from a re-staled index each run.
- **Measuring finds bugs that tests miss.** Timing the no-change check on RIP's own repository showed that an empty file counted as changed on every question.
- **A coverage test must find entry points by what they use, not by their URL.** The path-based version missed edit planning.
- **Background work needs the same care as the request path.** The final review found a model change during a background update and a file that always fails, both outside the request's time limit.

---

**Sprint 15 is now FROZEN.**
