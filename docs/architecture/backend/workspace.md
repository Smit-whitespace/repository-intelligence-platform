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
REST routes (app/api/routes/workspace.py)    MCP adapter (V1 M2)
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
2. **Every path goes through `_resolve`.** It rejects absolute paths (POSIX, Windows drive and UNC forms), paths that escape the root after resolving symlinks, and paths inside `.git/` or `.local_openclaw/`.
3. **Traversal never leaves the root.** Symlinks are listed only when they resolve inside the root, and symlinked directories are never descended into, which also rules out cycles.
4. **Secret-like files are never read or searched:** `.env`, `.env.*` (except `.example`, `.sample`, `.template` and `.dist` templates), `*.pem`, `*.key`, `*.p12`, `*.pfx` and SSH private keys. Tool output may be sent to hosted models.
5. **Every tool is bounded**, and every list result says when it was truncated:

| Tool | Limits |
|------|--------|
| `read_file` | 1 MB per file, 2,000 lines per call, `next_start_line` to resume |
| `list_tree` | depth 1–20, page size 1–2,000, `offset` pagination |
| `search_text` | 1–500 matches, 10 s time budget, lines cut to 10,000 characters before matching, 300-character excerpts |
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
- Python's `re` has no match timeout, so a pathological regular expression can still be slow on a single long line. The line-length cap and time budget limit the damage but cannot interrupt one match.
- Ignore rules are the same fixed name list the indexer uses; `.gitignore` is not read, so build output such as `frontend/dist/` is searched.
- Text search reads files on every call; there is no content cache. This is fast for repositories of a few thousand files (about 50 ms for this repository).

---

## Related Documents

| Document | Link |
|----------|------|
| Editing | [editing.md](editing.md) |
| Retrieval | [retrieval.md](retrieval.md) |
| API Reference | [../../api/README.md](../../api/README.md) |
