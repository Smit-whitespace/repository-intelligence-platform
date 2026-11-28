# ADR-0022: Index Freshness

**Status:** Adopted

**Context:**

RIP's semantic index was brought up to date only when a project was opened or when `reindex` was called. Edits made afterwards (by the user, or by an agent through the MCP server) were invisible to chat and semantic search until then, and nothing said so. In Sprint 14 an index one day older than the code made the model refuse 4 of 15 held-out questions, which looked like an over-cautious prompt (see [Measuring Answer Quality](../architecture/backend/chat.md#measuring-answer-quality)).

Constraints from earlier decisions: retrieval and chat never index (ADR-0004, ADR-0012); indexing is started by project initialization, which this decision supplements but does not change (ADR-0013); embedding runs locally and is slow enough that a large change cannot be awaited silently; and two processes (the app and an MCP server) may use one index, which an inter-process file lock guards.

**Decision:**

- Update the files that changed since indexing before every chat answer and semantic search.
- Do it at the entry points, not in the services: the chat routes and the workspace semantic-search route call `IndexFreshness.refresh`, and so does the MCP tool `search_semantic`, before they call `ChatService` or `RepositoryWorkspace.search_semantic`. Those services still never index.
- Detect changes by content hash (SHA-256 of each indexable text file against the hash stored in the index), with an in-memory mtime and size cache so unchanged files are not re-read.
- Spend at most `RIP_INDEXING_REFRESH_SECONDS` (default 15) on the update, most recently modified files first. No new file is started after the limit. The rest is finished by one background thread per project, and the response says how many files were not included (a note in the chat and search results; an `index` event in the chat stream).
- Never block on another process: a held index lock gives state `busy` and a note. Never rebuild: an unindexed project or an index built with another embedding model is left alone (`not_indexed`, `incompatible`). `0` turns updating off and reports the number of changed files.
- `index_status` reports the freshness it finds but updates nothing. `reindex` remains for a full rebuild (for example after changing the embedding model); agents no longer need it after editing files.

**Consequences:**

Positive:
- Answers and searches see the current files, or say how many they do not. On a snapshot whose index was behind on 6 files, held-out coverage returned from 53.9% / 56.7% to 65.6% / 65.0% (fresh index: 66.7% / 61.7%).
- Nothing waits longer than the limit plus one file's embedding, and the work not done in time is not lost.
- No new dependency, no watcher process, nothing running when RIP is idle.

Negative:
- Every chat and search scans the project and hashes the files whose mtime or size changed. With nothing changed this took 0.12 s warm and 0.5 s in a fresh process on RIP's own repository.
- The first question after a large change is slower (7 to 8 s for 7 files in the measurement; up to the limit for more).
- The answer that triggers a long update does not include the files still pending; it says so.
- A file that produces no chunks (an empty file) never enters the index, so it counts as changed on every check (see Known Limitations in the indexing document).

**Alternatives Considered:**

- **Inside `RetrievalService`:** retrieval would start writing the index, breaking ADR-0004 and ADR-0012 and making every caller of search pay for it. Rejected.
- **A file watcher:** a long-running process with platform-specific behavior, missed events while RIP is closed, and bursts (a branch switch) it would still have to batch. Checking at the moment of use needs none of that. Rejected.
- **Warn only** (say the index is stale, do not update): the user still gets the answer that refused. Rejected by the user.
- **Always wait** (no limit): a large change would leave a question hanging for minutes. Rejected by the user in favor of a limit with a background finish.
