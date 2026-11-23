# API Reference

> **Status:** Complete
> **Sprint Introduced:** Sprint 4
> **Last Updated:** Sprint 13
> **Reading Time:** 5 minutes
> **Audience:** Backend and frontend contributors
> **Prerequisites:** [Architecture Overview](../architecture/system-overview.md)

---

## Executive Summary

The backend exposes a REST API through FastAPI. All endpoints are versioned under `/api/v1/` (via router prefix). The API is documented interactively via Swagger at `/docs` when the server is running.

---

## Health

| Method | Path | Operation ID | Description |
|--------|------|-------------|-------------|
| GET | `/health` | `getHealth` | Backend health status + version |

**Response:** `HealthResponse` — `status`, `application`, `version`

---

## Projects

| Method | Path | Operation ID | Description |
|--------|------|-------------|-------------|
| POST | `/projects/open` | `openProject` | Open and initialize a project |
| GET | `/projects/info` | `getProjectInfo` | Get project metadata |

### POST /projects/open

Initiates the full project initialization pipeline (validate → persist → scan → index).

**Request:** `OpenProjectRequest` — `root_directory: Path`

**Response:** `OpenProjectResponse` — `project: str`, `root_directory: Path`, `indexing_diagnostics` (optional; present when a full index ran)

**See:** [Project Management Architecture](../architecture/backend/project-management.md), ADR-0009, ADR-0013

### GET /projects/info

**Query:** `root_directory: Path`

**Response:** `ProjectInfoResponse` — `name`, `root_directory`, `storage_directory`, `created_at`

---

## Repository

| Method | Path | Operation ID | Description |
|--------|------|-------------|-------------|
| GET | `/repository/index` | `getRepositoryIndex` | Full index (summary + entries) |
| GET | `/repository/scan` | `scanRepository` | Entries only |
| GET | `/repository/summary` | `getRepositorySummary` | Summary only |

**Query:** `root_directory: Path` (all three)

**See:** [Repository Architecture](../architecture/backend/repository.md)

---

## Chat

| Method | Path | Operation ID | Description |
|--------|------|-------------|-------------|
| POST | `/chat` | `chat` | Generate repository-aware response |
| GET | `/chat/stream` | `streamChat` | Stream repository-aware response (SSE) |

### POST /chat

**Request:** `ChatRequest` — `query: str`, `root_directory: str | None` (optional; scopes retrieval to the opened project)

**Response:** `ChatResponse` — `content: str`

### GET /chat/stream

**Query:** `query: str`, `root_directory: str | None` (optional)

**Response:** `text/event-stream` — `data: <content>\n\n`

> Retrieval is project-scoped: a chat request without `root_directory` (or for a project that has never been indexed) receives no repository context.

**See:** [Chat Architecture](../architecture/backend/chat.md)

---

## Editing

| Method | Path | Operation ID | Description |
|--------|------|-------------|-------------|
| POST | `/editing/edit` | `planEdit` | Generate a ChangeSet (no mutation) |
| POST | `/editing/apply` | `applyChangeSet` | Apply a ChangeSet with snapshot |
| POST | `/editing/rollback` | `rollbackChangeSet` | Rollback to a snapshot (204 No Content) |

### POST /editing/edit

**Request:** `EditRequest`

**Response:** `EditResponse` — proposed changes

### POST /editing/apply

**Request:** `ApplyRequest` — `repository_root`, `change_set`

**Response:** `ApplyResponse` — `snapshot_id: str`

### POST /editing/rollback

**Request:** `RollbackRequest` — `repository_root`, `snapshot_id`

**Response:** `204 No Content`

### Proposals (preferred)

| Method | Path | Operation ID | Description |
|--------|------|-------------|-------------|
| POST | `/editing/proposals` | `proposeEdits` | Store search/replace operations as a proposal with a diff |
| POST | `/editing/proposals/plan` | `planEditProposal` | Let the edit model write the edits from an instruction |
| GET | `/editing/proposals` | `listEditProposals` | Proposals, newest first |
| GET | `/editing/proposals/{id}` | `getEditProposal` | Diff, status, validation results |
| POST | `/editing/proposals/{id}/apply` | `applyEditProposal` | Apply by id (snapshot, all-or-nothing), then validate |
| POST | `/editing/proposals/{id}/reject` | `rejectEditProposal` | Reject a pending proposal |
| POST | `/editing/proposals/{id}/rollback` | `rollbackEditProposal` | Undo an applied proposal |
| GET / PUT | `/editing/validation` | `getValidationConfig` / `updateValidationConfig` | The project's validation commands |
| POST | `/editing/validation/run` | `runValidation` | Run validation commands now |

Proposal errors: `400` for operations that do not apply (the message lists each one), `404` unknown proposal, `409` wrong state (for example applying twice) or a file changed since the proposal was made.

**Errors:** `403` for a root that is not a registered RIP project; `409` when a file no longer matches the edit's `original_content` (apply) or changed after the apply (rollback); `500` when a failed apply could not be fully reverted (the message names the snapshot to roll back with).

**See:** [Editing Architecture](../architecture/backend/editing.md)

---

## Workspace

Read-only repository tools for external clients. Every endpoint takes `root_directory` (a registered project root) and repository-relative paths.

| Method | Path | Operation ID | Description |
|--------|------|-------------|-------------|
| GET | `/workspace/file` | `readWorkspaceFile` | Line range of a text file (max 2,000 lines per call) |
| GET | `/workspace/tree` | `listWorkspaceTree` | Paginated directory tree, ignored and protected directories skipped |
| GET | `/workspace/search/text` | `searchWorkspaceText` | Literal or regex line search, optional `path_glob` |
| GET | `/workspace/symbols` | `findWorkspaceSymbols` | Class, function and method definitions (Python only) |
| GET | `/workspace/search/semantic` | `searchWorkspaceSemantic` | Indexed chunks ranked by similarity |

**Errors:** `400` invalid argument, path outside the root, protected path, or secret-like file; `403` unregistered root; `404` missing file or directory; `413` file over 1 MB; `415` binary or non-UTF-8 file; `409` (semantic search) index built with a different embedding model.

**See:** [Workspace Architecture](../architecture/backend/workspace.md)

---

## Models

| Method | Path | Operation ID | Description |
|--------|------|-------------|-------------|
| GET | `/models` | `listModels` | Models installed in the local Ollama server |
| GET | `/settings/model` | `getActiveModel` | The model chat uses (resolved) |
| PUT | `/settings/model` | `updateActiveModel` | Set the primary model to an installed Ollama model |
| GET | `/models/configuration` | `getModelConfiguration` | Full configuration, file path, and which API keys are set (never their values) |
| PUT | `/models/configuration` | `updateModelConfiguration` | Validate and save a configuration; applies on the next request |
| GET | `/models/effective` | `getEffectiveModels` | Effective model per operation and the level it came from |

A missing API key or unusable configuration returns **400** with a message naming what to fix. An invalid configuration body returns **422** and is not saved.

**See:** [Model Configuration](../architecture/backend/models.md)

---

## System

| Method | Path | Operation ID | Description |
|--------|------|-------------|-------------|
| GET | `/system/status` | `getSystemStatus` | Backend and provider health |
| GET | `/system/capabilities` | `getSystemCapabilities` | Feature discovery for frontend |
| GET | `/system/version` | `getSystemVersion` | Application + API version info |

---

## Common Response Patterns

All endpoints return standardized error responses:

- **400 Bad Request** — the request is well-formed but cannot be processed
- **403 Forbidden** — the root is not a registered RIP project
- **404 Not Found** — resource not found
- **409 Conflict** — stale edit, unsafe rollback, or incompatible index
- **413 / 415** — file too large / not text (Workspace)
- **422 Unprocessable Entity** — request validation failed (FastAPI's default format)
- **500 Server Error** — unexpected failure

Requests whose `Host` header is not in `LOC_SERVER_ALLOWED_HOSTS` (default `localhost,127.0.0.1`) are rejected with **400** before reaching any endpoint. This blocks DNS rebinding.

Domain errors return `{"detail": "<message>"}`.

---

## Related Documents

| Document | Link |
|----------|------|
| Architecture Overview | [architecture/system-overview.md](../architecture/system-overview.md) |
| Project Management | [architecture/backend/project-management.md](../architecture/backend/project-management.md) |
| Repository | [architecture/backend/repository.md](../architecture/backend/repository.md) |
| Chat | [architecture/backend/chat.md](../architecture/backend/chat.md) |
| Editing | [architecture/backend/editing.md](../architecture/backend/editing.md) |
| Workspace | [architecture/backend/workspace.md](../architecture/backend/workspace.md) |
| Model Configuration | [architecture/backend/models.md](../architecture/backend/models.md) |
