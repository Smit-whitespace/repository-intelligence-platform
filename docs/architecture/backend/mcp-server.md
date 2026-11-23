# MCP Server

> **Status:** Complete (stdio transport)
> **Reading Time:** 5 minutes
> **Audience:** Users connecting AI agents, backend contributors
> **Prerequisites:** [Workspace](workspace.md)
> **Next Reading:** [Indexing](indexing.md)

---

## Executive Summary

RIP can run as a [Model Context Protocol](https://modelcontextprotocol.io) server, so AI agents such as Claude Code and Claude Desktop can use RIP's repository intelligence instead of building their own. The agent starts `python -m app.mcp_server --root <repository>` in the background and talks to it over stdin/stdout. That one process serves one repository for its whole life, so an agent can never point the tools at another directory.

---

## Tools

| Tool | What it does | Writes anything? |
|------|--------------|------------------|
| `read_file` | Lines of a text file, up to 2,000 per call | No |
| `list_tree` | Paginated directory tree | No |
| `search_text` | Literal or regex line search, optional `path_glob` | No |
| `find_symbols` | Where Python classes, functions and methods are defined | No |
| `search_semantic` | Code ranked by meaning ("where are edits applied?") | No |
| `index_status` | Whether the repository is indexed, with which embedding model | No |
| `reindex` | Updates the semantic index (changed files only) | RIP's own index only, never repository files |
| `propose_edit` | Stores search/replace edits as a reviewable proposal with a diff | No (a proposal in RIP's storage) |
| `get_proposal`, `list_proposals` | Proposal diff, status and validation results | No |
| `apply_proposal` | Writes a proposal (snapshot, all-or-nothing), then runs validation | **Yes**, only with `--editing apply` |
| `rollback_proposal` | Undoes an applied proposal | **Yes**, only with `--editing apply` |

**Editing modes** (`--editing`, default `propose`):

| Mode | Edit tools | Who applies |
|------|-----------|-------------|
| `off` | none | Nobody, through RIP |
| `propose` | `propose_edit`, `get_proposal`, `list_proposals` | A person, in the RIP app's Editing page |
| `apply` | all of the above, plus `apply_proposal`, `rollback_proposal` | The agent |

Tools a mode does not allow are not registered at all. `apply` is an explicit opt-in because applying runs the project's validation commands, which execute repository code (that is what tests do).

Every tool returns structured JSON (with an output schema) and is annotated with MCP's read-only hints, so clients can approve read-only tools more freely. The server also sends usage instructions that tell the agent which tool fits which question.

---

## Set up with Claude

Replace the paths with your own. `<RIP>` is where this repository is checked out, and `<REPO>` is the repository you want the agent to explore.

**Prerequisites:** backend dependencies installed (`uv sync`), so `<RIP>\.venv\Scripts\python.exe` exists. For `search_semantic` and `reindex`, Ollama must be running with the embedding model (`ollama pull nomic-embed-text`). The other tools work without Ollama.

### Claude Code

Run this in a terminal. On macOS or Linux, the interpreter is `<RIP>/.venv/bin/python`.

```powershell
claude mcp add --transport stdio --scope user --env PYTHONPATH="<RIP>\backend" rip -- "<RIP>\.venv\Scripts\python.exe" -m app.mcp_server --root "<REPO>"
```

- Options go before the server name (`rip`), and everything after `--` is the command that starts the server.
- `--scope user` makes the server available in all your projects. Use `--scope project` to write a shared `.mcp.json` into the current project instead, or leave it out to use `local` (only you, only this project).
- Quote paths that contain spaces.

Check that it connected:

```powershell
claude mcp list
```

`rip` should show as connected. Inside a Claude Code session, `/mcp` lists the server and its tools.

**Equivalent `.mcp.json`** (project scope, committed with a project). Backslashes are doubled in JSON:

```json
{
  "mcpServers": {
    "rip": {
      "type": "stdio",
      "command": "<RIP>\\.venv\\Scripts\\python.exe",
      "args": ["-m", "app.mcp_server", "--root", "<REPO>"],
      "env": { "PYTHONPATH": "<RIP>\\backend" }
    }
  }
}
```

Claude Code asks you to approve project-scoped servers the first time.

### Claude Desktop

Open **Settings → Developer → Edit Config**, which opens `%APPDATA%\Claude\claude_desktop_config.json` on Windows, and add:

```json
{
  "mcpServers": {
    "rip": {
      "command": "<RIP>\\.venv\\Scripts\\python.exe",
      "args": ["-m", "app.mcp_server", "--root", "<REPO>"],
      "env": { "PYTHONPATH": "<RIP>\\backend" }
    }
  }
}
```

Quit Claude Desktop completely and start it again. If the server does not appear, its logs (and RIP's stderr) are in `%APPDATA%\Claude\logs\`.

To let the agent apply its own edits, add `--editing apply` after `--root "<REPO>"`.

### A first session

Ask the agent something like: *"Use the rip tools: check index_status, reindex if needed, then find where file edits are applied and explain the safety checks."* On first use, the server registers `<REPO>` as a RIP project (metadata only, in `<REPO>\.local_openclaw\`). Nothing is indexed until `reindex` is called.

---

## Architecture

```
Claude Code / Claude Desktop
        │  MCP over stdio (JSON-RPC on stdin/stdout)
        ▼
python -m app.mcp_server --root <REPO>      app/mcp_server/__main__.py
        │  registers <REPO> if needed, binds one workspace
        ▼
build_server(workspace, indexing_service)   app/mcp_server/server.py
        │  thin tool adapters; blocking work runs in a worker thread
        ▼
RepositoryWorkspace (read tools)   IndexingService (index_status, reindex)
```

- **No business logic in the adapter.** Each tool calls the same method the REST API uses, so path security, limits and error messages are identical. Domain errors become MCP tool errors carrying the service's message.
- **Stdout is protocol only.** All logging goes to stderr, and a test launches the real subprocess to prove it.
- **One process, one repository.** The root comes from the user's own configuration, which is also what makes registering it on startup legitimate. Home directories and drive roots are refused, both here and in the REST API.
- **Model configuration changes reach running servers.** Before every tool call the server checks whether `models.json` changed, so an agent's `reindex` never rebuilds the index with a model you have since replaced.
- **Failures are failures.** A `reindex` in which every file failed (for example, Ollama is not running) is reported as a tool error, not as a successful run, so the agent does not assume the index is current.
- **Indexing is locked across processes.** The RIP app and an MCP server can run against the same project at once. Indexing takes an OS file lock (`.local_openclaw/index/index.lock`), so a second indexer gets "another process is indexing" (HTTP 409 in REST, a tool error in MCP) instead of corrupting ChromaDB. The OS releases the lock if the holder crashes.

---

## Known Limitations

- **Only the stdio transport.** That is what local agents use. A Streamable HTTP endpoint for remote agents would need authentication first.
- **The semantic index goes stale as the agent edits files** until `reindex` runs. Reindexing only embeds changed files, so the server instructions tell agents to reindex after editing.
- **Edits cannot delete or rename files.** Agents with their own file tools can still do so outside RIP.
- **Concurrent reads of one ChromaDB directory from two processes** (the app and an MCP server) are expected to work, but only writes are locked.

---

## Related Documents

| Document | Link |
|----------|------|
| Workspace (the tools' implementation) | [workspace.md](workspace.md) |
| Indexing | [indexing.md](indexing.md) |
| API Reference | [../../api/README.md](../../api/README.md) |
