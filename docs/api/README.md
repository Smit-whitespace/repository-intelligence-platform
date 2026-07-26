# API Reference

> **Status:** Complete
> **Sprint Introduced:** Sprint 4
> **Last Updated:** Sprint 12.1
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

**Response:** `OpenProjectResponse` — `project: str`, `root_directory: Path`

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

**Request:** `ChatRequest` — `query: str`

**Response:** `ChatResponse` — `content: str`

### GET /chat/stream

**Query:** `query: str`

**Response:** `text/event-stream` — `data: <content>\n\n`

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

**See:** [Editing Architecture](../architecture/backend/editing.md)

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

- **400 Bad Request** — validation error
- **404 Not Found** — resource not found
- **500 Server Error** — unexpected failure

Error bodies follow FastAPI's default validation format.

---

## Related Documents

| Document | Link |
|----------|------|
| Architecture Overview | [architecture/system-overview.md](../architecture/system-overview.md) |
| Project Management | [architecture/backend/project-management.md](../architecture/backend/project-management.md) |
| Repository | [architecture/backend/repository.md](../architecture/backend/repository.md) |
| Chat | [architecture/backend/chat.md](../architecture/backend/chat.md) |
| Editing | [architecture/backend/editing.md](../architecture/backend/editing.md) |
