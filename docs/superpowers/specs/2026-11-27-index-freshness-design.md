# Sprint 15 — Index Freshness: Design

> **Status:** Approved (2026-11-27)
> **Date:** 2026-11-27
> **Sprint:** 15

## Intent

RIP answers questions from a semantic index of the repository. Today that index is built or refreshed only when a project is opened (or when an MCP agent calls `reindex`), and nothing says when it has fallen behind the files. In Sprint 14, an index one day older than the code made the model refuse 27% of held-out questions — correctly, since it was never shown the code they asked about — and a fresh index raised held-out answer coverage from 43% to 64%, more than any prompt change did.

**Goal:** every answer and every semantic search reflects the files as they are now. When files have changed since the last index, RIP updates just those files before answering, up to a time limit, and says so whenever it could not finish.

## Goals

- Before a semantic search, chat answer or MCP `search_semantic`, detect files changed since the last index (edited, new, deleted, or newly ignored) and update only those.
- Wait at most a time limit (default 15 seconds) for the update. Past it, answer from the current index, say in the answer's surroundings that the index is still updating and how many files are not yet included, and finish the update in the background.
- Show the real index state: the Dashboard's "Indexing" tile, today hardcoded to `available`, reports "up to date", "N files changed since indexing", "updating", "not indexed" or "needs reindex (different embedding model)".
- Cost close to nothing when nothing changed: on RIP's own repository (≈350 files) the check adds well under half a second; a cache keeps it small on large repositories.

## Non-goals

- A file watcher or any always-running background indexing (option 3, rejected below).
- Rebuilding an index built with a different embedding model. That stays an explicit reindex, as today; freshness reports the mismatch and does nothing else.
- Indexing a project that has never been indexed. Opening the project does that, as today.
- An "Update index" button in the app. The update is automatic; a button can follow if the automatic path proves insufficient.
- Changes to text search, file reading or symbol search: they read files from disk and are already current.

## Anti-goals (failure even if it "works")

- A question fails, or waits indefinitely, because of freshness. Any freshness error is logged and the question is answered from the current index with a note.
- A wait longer than the limit, apart from finishing the file being embedded when the limit is reached.
- An answer from a stale index with no indication that it is stale.
- Two processes writing one project's index at once. The existing inter-process index lock stays the only writer gate.
- ChatService or RetrievalService performing indexing (ADR-0004, ADR-0012 stay as they are).

## Constraints

- **Frozen decisions:** ADR-0004 (retrieval never indexes) and ADR-0012 (ChatService never indexes or writes the vector store). Orchestration above them follows ADR-0013's pattern.
- **One writer per project:** `project_index_lock` (inter-process). The app and an MCP server can both be running against the same project.
- **No new dependencies.**
- **Existing data model:** every stored chunk carries its file's `relative_path` and `sha256`. Chunk ids include the content hash, so unchanged content keeps its vector. No index format change is needed.
- **Never silently switch** provider or model after an error (standing rule).

## Approaches

| | Approach | Trade-offs | Decision |
|---|---|---|---|
| 1 | **Update first, at each entry point.** A freshness service in the Indexing subsystem updates changed files up to the limit; the chat stream route, the semantic search route and the MCP `search_semantic` tool call it before handing off to `ChatService` / `RetrievalService`, which are unchanged. | Respects ADR-0004/0012 and mirrors ADR-0013; the chat stream can show "Updating index…" before the answer. Three call sites must stay consistent, so a test checks every semantic entry point calls it. | **Chosen** (by the user) |
| 2 | Inside `RetrievalService.search`. | One place, cannot be forgotten. Reverses ADR-0004/0012 (a read path writes the index), and runs too deep inside chat to show progress first. | Rejected |
| 3 | File watcher feeding a dirty-file list. | Instant checks, but a new dependency (`watchdog`), a long-running watcher per project, cross-process coordination, and it embeds files nobody asks about. | Rejected |

Behavior chosen by the user: **update before answering** (not warn-only, not background-only), **wait up to a limit** (not always wait).

## Design

### 1. Detecting changes

`IndexFreshness` (new, `app/indexing/freshness.py`, owned by the Indexing subsystem) computes a project's **change set**:

- **Current files:** the same selection indexing uses — `RepositoryScanner` with the repository's ignore rules, `is_indexable_file_name`, text files only — each with its content SHA-256.
- **Indexed files:** each stored `relative_path` with its `sha256`, read from the project's vector store (a new store method returning `{path: sha256}`; one value per path, since all chunks of a file share it).
- **Change set:** `changed` (hash differs), `added` (not indexed), `removed` (indexed but gone, now ignored, or no longer text).

**Hash cache (in-process):** per project, `{path: (mtime_ns, size, sha256)}`. A file whose modification time and size are unchanged reuses its cached hash instead of being read. A cold process hashes everything once.

### 2. Updating a given set of files

`IndexingService` gains `update_files(root, paths_to_index, paths_to_remove, deadline)`. It runs the same per-file pipeline as `index_repository` (metadata, load, chunk, embed only chunks whose ids are new) — refactored into one shared per-file step so the two paths cannot drift — and deletes the chunks of each updated or removed file that are no longer current. It works file by file and stops starting new files once `deadline` has passed; the file in progress finishes. It returns which paths were done and which remain.

Order: **most recently modified first**, so the files someone just edited — the likeliest subject of their question — are in the index soonest.

All of this runs inside `project_index_lock`. If the lock is held by another process, `update_files` does not wait: it reports `busy`.

### 3. The freshness step

`IndexFreshness.refresh(root) -> FreshnessResult`:

1. If the project is not indexed, or its index is incompatible (different embedding model), return that state and do nothing.
2. Compute the change set. If empty, return `up_to_date`.
3. Call `update_files` with a deadline of now + `RIP_INDEXING_REFRESH_SECONDS` (default 15; `0` turns automatic updating off, reporting the change set only).
4. If files remain, start (or join) a **background update** for that project: one daemon thread per project root per process, single-flight, which takes the lock and finishes the remaining files with no deadline. If another process holds the lock, the background update is not started; that process is already updating.

If this process's own background update for the project is already running, `refresh` does not try the lock: it returns `partial` with the pending count, and the answer carries the note. Removed files are processed before edited and new ones (deleting chunks is fast and stops answers citing deleted code).

`FreshnessResult` carries: `state` (`up_to_date` | `updated` | `partial` | `busy` | `off` | `not_indexed` | `incompatible`), counts of changed/added/removed files, files updated now, files still pending, and seconds spent.

A failure anywhere in this step (embedding provider down, a file unreadable) is logged and turned into a result with a note; it never raises to the caller. Files that fail keep their existing chunks, as `index_repository` already does.

`IndexFreshness.status(root)` returns the same state and counts **without updating** (for the Dashboard and the MCP `index_status` tool), and `updating` while a background update for that project is running in this process.

### 4. Entry points

Each semantic entry point calls `refresh` first, then proceeds exactly as today:

| Entry point | What the caller sees |
|---|---|
| `GET /api/v1/chat/stream` | Before the first answer chunk, an SSE event `event: index` with the `FreshnessResult` as JSON when there was work (`updated`, `partial`, `busy`). The app shows "Updating index (N files)…" while waiting for the stream to start (the request is in flight during the update) and, for `partial`/`busy`, a one-line note above the answer: "The index is still updating; N changed files are not included in this answer." Unnamed `data:` events are unchanged, so the answer text protocol is not affected. |
| `POST /api/v1/chat` | The response gains an `index` field with the `FreshnessResult`. |
| `GET /api/v1/workspace/search/semantic` | The response gains an `index` field with the `FreshnessResult`. |
| MCP `search_semantic` | Result gains the same field; for `partial`/`busy`, a note in the text result. |
| MCP `index_status` | Gains the freshness state and counts (from `status`, no update). MCP `reindex` is unchanged. |
| `GET /api/v1/workspace/index-status?root_directory=…` (new) | The state and counts from `status`, no update. The Dashboard's "Indexing" tile uses it for the active project. (`GET /system/status` has no project, so its `indexing_state` cannot report one; it stays as it is.) |

A test enumerates the semantic entry points (routes using `RetrievalService`/`ChatService`, and the MCP `search_semantic` tool) and fails if one does not go through freshness.

### 5. Configuration

`RIP_INDEXING_REFRESH_SECONDS` (int, default `15`): the most time spent updating before an answer. `0`: never update automatically; entry points still report the change set.

## How we will know it works

- **Answer quality on a stale index:** index the Sprint 14 snapshot, then change files so the index is a known amount behind (for example, restore the 2026-11-25 versions of the files the held-out questions ask about). Run `python -m eval.answers --set holdout` with freshness on: coverage and refusals should match the freshly indexed run (≈64%, 0% refusals); with `RIP_INDEXING_REFRESH_SECONDS=0` they should match the stale run.
- **No-change cost:** time `refresh` on RIP's own repository with nothing changed — warm cache and cold — and record both. Target: well under 0.5 s warm.
- **Limit:** with more changed files than fit in the limit, the first answer starts within the limit plus one file's embedding, says how many files are pending, and the background update completes them.
- **Concurrency:** with the MCP server reindexing the same project, an app question returns `busy` with a note and an answer, and nothing waits on the lock.
- **Tests** for each piece: change set (edit, add, delete, newly ignored, edit-then-revert counts as unchanged), cache reuse, deadline stop, single-flight background, busy lock, error-to-note, incompatible index untouched, entry-point coverage.

## Left to the builder

- Module and class names beyond `IndexFreshness`, `FreshnessResult`, `update_files`.
- How `update_files` shares code with `index_repository` (one per-file function is required; its shape is free).
- The exact SSE event payload field names and the frontend component that shows the progress line and note.
- Whether the hash cache lives on `IndexFreshness` or a helper it owns.
- Logging wording (follow the existing `logging.getLogger(__name__)` style).
