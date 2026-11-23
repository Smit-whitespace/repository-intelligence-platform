<p align="center">
  <h1 align="center">Repository Intelligence Platform (RIP)</h1>
  <p align="center"><strong>Local-first repository intelligence for people and AI agents.</strong></p>
  <p align="center">
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
    <img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+">
    <img src="https://img.shields.io/badge/node-20+-green.svg" alt="Node 20+">
  </p>
</p>

RIP indexes your codebase on your own machine, answers natural-language questions about it, and makes reviewable, reversible code changes. AI agents such as Claude Code can use the same repository tools over MCP instead of building their own indexing. By default everything runs locally with Ollama; hosted models (OpenAI-compatible APIs, Anthropic) are an explicit opt-in.

---

## Screenshots

*Screenshots will be added after the first stable release.*

---

## Features

- **Repository-Aware Chat** — Ask questions about your codebase in natural language. RIP retrieves relevant code context and answers based on your actual repository structure.
- **Semantic Retrieval** — Uses vector embeddings to find the most relevant code for any query. Results are ranked, deduplicated, and assembled into context for accurate answers.
- **Reviewable Editing** — Describe a change (or let an agent propose one), review the diff, then apply it. Edits are exact search/replace operations applied by proposal id, with a snapshot, all-or-nothing writes, conflict detection, rollback, and your own validation commands (for example `pytest -q`) run afterwards.
- **MCP Server for AI Agents** — `python -m app.mcp_server --root <repo>` gives Claude Code, Claude Desktop and other MCP clients read, search, symbol, semantic-search, reindex and (opt-in) editing tools for one repository.
- **Configurable Models** — A required primary model, optional per-capability and per-task overrides, and a separate embedding model; Ollama, any OpenAI-compatible API, or Anthropic. The Settings page shows which model each operation uses and why.
- **Always-Current Search** — Respects `.gitignore`, and reindexing embeds only changed files, so agents can reindex after every edit.
- **Project Management** — Open any project directory and RIP indexes its structure and code semantics.

## Architecture

```
Repository → Indexing → Retrieval → Chat → Editing
```

RIP is built as a modular pipeline with clear subsystem boundaries:

| Subsystem | Responsibility |
|-----------|---------------|
| **Repository** | Scan, chunk, and manage repository files |
| **Indexing** | Embed chunks and store in a vector database |
| **Retrieval** | Search indexed content by semantic similarity |
| **Chat** | Orchestrate retrieval + prompt assembly + LLM generation |
| **Workspace** | Read-only, path-safe repository tools shared by REST and MCP |
| **Editing** | Proposals, review, apply, validation and rollback of code changes |
| **Models** | Provider adapters and task → capability → primary model resolution |
| **MCP Server** | Exposes the workspace, indexing and editing tools to AI agents |

Every subsystem has a public interface and at least one implementation. Components are wired through dependency injection, making the system testable and extensible.

## Privacy & Offline-First

- **Local by default** — With the default configuration all computation runs locally with Ollama. A hosted provider is used only for the operations you assign to it ([ADR-0018](docs/adr/adr-0018-hosted-model-providers.md)); API keys are read from environment variables and never stored or returned.
- **No telemetry** — RIP sends no analytics, crash reports or usage tracking, and disables ChromaDB's telemetry.
- **Safe by construction** — Tools only operate on registered project roots, never read secret-like files (`.env`, keys), never write `.git` or RIP's own storage, and the API only accepts requests addressed to `localhost`.
- **Local storage** — Indexes, snapshots, and project metadata live in a `.local_openclaw` directory inside each opened project root. Persistence identity comes from the opened project, never from the process working directory.

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- [Ollama](https://ollama.ai) with `nomic-embed-text` and `qwen3:8b` models

### Setup

```bash
# Clone
git clone https://github.com/Smit-whitespace/repository-intelligence-platform
cd repository-intelligence-platform

# Install backend dependencies
uv sync

# Install frontend dependencies
cd frontend && npm install && cd ..

# Pull Ollama models
ollama pull nomic-embed-text
ollama pull qwen3:8b
```

### Run

```bash
# Terminal 1: Start the backend (from the backend/ directory)
cd backend
uv run python -m uvicorn app.main:app --reload

# On Windows, if uv fails with "uv trampoline failed to canonicalize script path":
#   .venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Terminal 2: Start the frontend
cd frontend && npm run dev
```

Open your browser to the address shown in the terminal output.

> The backend resolves all project persistence from the **opened project root** (`<project root>/.local_openclaw/`), never from the process working directory. You can start the backend from any directory.

## Documentation

- [START-HERE](docs/START-HERE.md) — Begin here if you're new to the project
- [Architecture Overview](docs/architecture/README.md) — System design and decisions
- [Vision & Roadmap](docs/vision/README.md) — Project direction and future plans
- [Development Guide](docs/development/environment.md) — Setting up a development environment
- [API Reference](docs/api/README.md) — OpenAPI documentation
- [Model Configuration](docs/architecture/backend/models.md) — Local and hosted models, per-capability overrides, embeddings
- [MCP Server](docs/architecture/backend/mcp-server.md) — Connect Claude Code, Claude Desktop or other MCP agents to RIP
- [Reference](docs/reference/glossary.md) — Glossary, configuration, cheat sheets

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md) before getting started.

## Project Status

RIP is in active development. Repository scanning, indexing, retrieval, chat, reviewable editing, model configuration and the MCP server are functional and covered by tests. See the [vision document](docs/vision/README.md) for the roadmap.

## License

Licensed under the [MIT License](LICENSE). Copyright (c) 2026 Smit-whitespace.
