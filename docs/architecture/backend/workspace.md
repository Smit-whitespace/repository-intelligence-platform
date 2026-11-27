# Workspace Subsystem

> **Status:** Complete (V1 M1)
> **Last Updated:** V1 M1
> **Reading Time:** 4 minutes
> **Audience:** Backend contributors, MCP adapter authors
> **Prerequisites:** [System Overview](../system-overview.md)
> **Related APIs:** `GET /workspace/file`, `GET /workspace/tree`, `GET /workspace/search/text`, `GET /workspace/symbols`, `GET /workspace/search/semantic`
> **Next Reading:** [Editing](editing.md)

---

## Executive Summary

The Workspace subsystem gives external clients (REST now, MCP next) read-only tools to explore one repository: read file lines, list the tree, search text, find symbol definitions and run semantic search. A `RepositoryWorkspace` is bound to a single registered project root when it is opened, and every tool resolves paths through one function. That makes path security a property of one module instead of something each adapter has to get right.

---

## Responsibilities

- Validate that a root is a registered RIP project before any tool runs.
- Resolve repository-relative paths safely (the single path-security boundary).
- Provide bounded, read-only tools whose results say when they were cut short.
- Delegate semantic search to the existing `RetrievalService`, without indexing.

## Ownership Boundaries

| Owns | Does not own |
|------|--------------|
| Path resolution and read policy for client tools | Writing files (Editing owns all modification) |
| Tree traversal, text search, Python symbol extraction | Indexing or embeddings (Indexing) |
| Result limits and truncation reporting | Ranking (Retrieval) |

---

## Architecture

```
REST routes (app/api/routes/workspace.py)    MCP server (app/mcp_server/)
                  \                            /
                   get_workspace_opener()  (app/dependencies/providers.py)
                                 |
                   RepositoryWorkspace.open(root)   -- registered-root check
                                 |
     read_file · list_tree · search_text · find_symbols · search_semantic
                                 |
                   _resolve(path)  -- the path-security boundary
                                 |
            filesystem          PythonSymbolExtractor        RetrievalService
```

Routes are thin adapters: they translate query parameters and nothing else. Validation, limits and errors live in the workspace, so the MCP adapter will behave identically without duplicating logic.

---

## Key Files

| File | Purpose |
|------|---------|
| `app/workspace/service.py` | `RepositoryWorkspace`, path safety, traversal, all tools |
| `app/workspace/symbols.py` | `PythonSymbolExtractor`: `ast`-based definitions with a per-file cache |
| `app/workspace/models.py` | Result models; every list result carries a truncation flag |
| `app/workspace/exceptions.py` | Typed errors, mapped to HTTP status codes in `app/api/exception_handlers.py` |
| `app/core/storage/locations.py` | `is_registered_project`, `PROTECTED_DIRECTORY_NAMES` (shared with Editing) |

---

## Invariants

> [!IMPORTANT]

1. **Only registered projects can be opened** (`UnregisteredWorkspaceError`, HTTP 403).
2. **Every path goes through `_resolve`.** It rejects absolute paths (POSIX, Windows drive and UNC forms), paths that escape the root after resolving symlinks, and paths inside `.git/` or `.rip/`.
3. **Traversal never leaves the root.** The walk only descends into a directory that resolves to itself, so symlinks, Windows junctions (which Python's `is_symlink` does not report) and other reparse points are never walked into. That also rules out cycles. A link is listed only when its target is inside the root and outside protected directories. The walk is iterative (deep trees cannot overflow the stack) and stops after 100,000 entries.
4. **Secret-like files are never read or searched:** `.env`, `.env.*`, `.envrc`, `.netrc`, `.npmrc`, `.pypirc`, `.git-credentials`, `.pgpass`, `credentials`, `credentials.json`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore` and SSH private keys (`id_rsa*` and similar, but not `*.pub`). Templates ending in `.example`, `.sample`, `.template` or `.dist` stay readable. The check runs on the resolved target, so a symlink with an innocent name cannot expose a secret file. Tool output may be sent to hosted models.
5. **Every tool is bounded**, and every list result says when it was truncated:

| Tool | Limits |
|------|--------|
| `read_file` | 1 MB per file, 2,000 lines per call, `next_start_line` to resume; a `start_line` past the end is an error that gives the file's length |
| `list_tree` | depth 1–20, page size 1–2,000, `offset` pagination |
| `search_text` | 1–500 matches (truncated only when more exist), 10 s time budget that also bounds each single regex match, lines cut to 10,000 characters before matching (a longer line without a match in that part makes the result truncated and is named in the reason), 300-character excerpts |
| `find_symbols` | 1–500 definitions |
| `search_semantic` | 1–50 chunks |

6. **Line numbers match editors.** Lines split only on `\n`, `\r\n` and `\r`, and returned content keeps its original line endings.
7. **"Not found" is never ambiguous.** Symbol results list the languages searched and the files skipped for syntax errors, and semantic results say whether the project is indexed at all.

---

## Why This Design

- **One bound object instead of a root on every call.** The MCP server (M2) will be launched for one repository, so binding at open time matches how it runs, and the REST adapter simply opens a workspace per request.
- **Ranked chunks instead of an assembled prompt.** Context Assembly builds a chat prompt with instructions. An external agent is the LLM itself, so it needs chunks with paths and line ranges, not someone else's prompt.
- **Python's own `ast` for symbols.** Exact for Python with no new dependency. Other languages would need tree-sitter or a language server; until then, results say "Python" explicitly.

---

## Known Limitations

- Symbol lookup covers Python only; JavaScript, TypeScript and Java are not parsed yet.
- There is no find-references tool. Text search is the textual substitute.
- Regular expressions use the `regex` engine (already installed with `tiktoken`) because Python's `re` cannot time out a match; a catastrophically backtracking pattern ends the search with a truncation reason instead of hanging a server thread.
- Hard links are indistinguishable from ordinary files, so a hard link inside the repository to a file outside it is readable. Creating one requires write access to the repository already.
- Paths containing NUL bytes, and on Windows any `:` (alternate data streams), are rejected.
- Listing and search use the same ignore rules as indexing: the names RIP always skips plus the repository's `.gitignore` files and `.git/info/exclude`. `read_file` can still open an ignored file by path.
- Text search reads files on every call; there is no content cache. This is fast for repositories of a few thousand files (about 50 ms for this repository).

---

## Related Documents

| Document | Link |
|----------|------|
| Editing | [editing.md](editing.md) |
| Retrieval | [retrieval.md](retrieval.md) |
| API Reference | [../../api/README.md](../../api/README.md) |
