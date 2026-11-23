<div align="center">

# Repository Intelligence Platform (RIP)

**Local-first repository intelligence for people and AI agents.**

<a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
<img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+">
<img src="https://img.shields.io/badge/node-20+-green.svg" alt="Node 20+">

</div>

RIP indexes your codebase on your own machine. By default everything runs locally with Ollama — no cloud services, no API keys. Hosted models (OpenAI-compatible APIs, Anthropic) are an explicit opt-in, per operation.

It helps developers **understand, query, and safely modify codebases** by building repository-aware context that can be retrieved and supplied to an LLM — and AI agents such as Claude Code can use the same repository tools over MCP instead of building their own indexing.

Instead of treating a repository as a collection of isolated text chunks, RIP provides a structured pipeline for turning a codebase into something both **developers and AI tools can query intelligently**.

---

## ✨ Features

- **💬 Repository-Aware Chat** — Ask questions about your codebase in natural language. RIP retrieves relevant repository context and answers based on the code that actually exists.

- **🔎 Semantic Retrieval** — Uses vector embeddings to identify relevant code for a query. Results are ranked, deduplicated, and assembled into focused context before generation.

- **✏️ Reviewable Editing** — Describe a change (or let an agent propose one), review the diff, then apply it. Edits are exact search/replace operations applied by proposal id, with a snapshot, all-or-nothing writes, conflict detection, rollback, and your own validation commands (for example `pytest -q`) run afterwards.

- **🤖 MCP Server for AI Agents** — `python -m app.mcp_server --root <repo>` gives Claude Code, Claude Desktop and other MCP clients read, search, symbol, semantic-search, reindex and (opt-in) editing tools for one repository.

- **🧩 Configurable Models** — A required primary model, optional per-capability and per-task overrides, and a separate embedding model; Ollama, any OpenAI-compatible API, or Anthropic. The Settings page shows which model each operation uses and why.

- **♻️ Always-Current Search** — Respects `.gitignore`, and reindexing embeds only changed files, so agents can reindex after every edit.

- **📁 Project Management** — Open a local project and let RIP manage repository scanning, indexing state, and project-local persistence.

- **🔒 Local-First Execution** — Repository analysis, retrieval, model inference, and editing workflows stay on your machine unless you assign an operation to a hosted model.

---

## 🧠 Why Repository Intelligence?

LLMs can reason well about code **when they receive the right context**.

The difficult part is often deciding:

- Which files matter for this question?
- Where is a behavior implemented?
- Which pieces of code are related?
- What context should be sent to the model?
- What should be inspected before modifying the repository?

RIP focuses on that layer between the **repository** and the **model**.

```text
Repository
    ↓
Scanning / Chunking
    ↓
Indexing
    ↓
Retrieval
    ↓
Repository-Aware Chat
    ↓
Controlled Editing
```

The goal is to make repository understanding a reusable capability — for developers in the RIP app, and for AI agents through the MCP server.

---

## 🏗️ Architecture

RIP is built as a modular pipeline with clear subsystem boundaries:

| Subsystem | Responsibility |
|-----------|---------------|
| **Repository** | Scan, chunk, and manage repository files |
| **Indexing** | Embed chunks and store them in a vector database |
| **Retrieval** | Search indexed content by semantic similarity |
| **Chat** | Orchestrate retrieval, prompt assembly, and LLM generation |
| **Workspace** | Read-only, path-safe repository tools shared by REST and MCP |
| **Editing** | Proposals, review, apply, validation, and rollback of code changes |
| **Models** | Provider adapters and task → capability → primary model resolution |
| **MCP Server** | Exposes the workspace, indexing, and editing tools to AI agents |

Every subsystem exposes a defined interface with concrete implementations behind it.

Components are wired through dependency injection, keeping the system testable and allowing individual parts of the repository-intelligence pipeline to evolve independently.

---

## 🔐 Privacy & Offline-First

RIP is designed around local execution.

- **Local by default** — With the default configuration, repository scanning, retrieval, inference, and editing run locally with Ollama. A hosted provider is used only for the operations you assign to it ([ADR-0018](docs/adr/adr-0018-hosted-model-providers.md)); API keys are read from environment variables and never stored or returned.
- **No telemetry** — No analytics, crash reporting, or usage tracking is built into RIP, and ChromaDB's telemetry is disabled.
- **Safe by construction** — Tools only operate on registered project roots, never read secret-like files (`.env`, keys), never write `.git` or RIP's own storage, and the API only accepts requests addressed to `localhost`. RIP signs the proposals, snapshots, and validation commands it stores, so a cloned repository cannot smuggle in its own ([ADR-0019](docs/adr/adr-0019-signed-project-state.md)).
- **Project-local storage** — Indexes, snapshots, and project metadata live inside:

```text
<project-root>/.local_openclaw/
```

Persistence identity comes from the **opened project root**, not the process working directory.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- [Ollama](https://ollama.com/)
- `nomic-embed-text`
- `qwen3:8b`

Pull the required models:

```bash
ollama pull nomic-embed-text
ollama pull qwen3:8b
```

### Setup

```bash
# Clone
git clone https://github.com/Smit-whitespace/repository-intelligence-platform
cd repository-intelligence-platform

# Install backend dependencies
uv sync

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Run

Start the backend:

```bash
cd backend
uv run python -m uvicorn app.main:app --reload
```

On Windows, if `uv` fails with:

```text
uv trampoline failed to canonicalize script path
```

run:

```bash
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Start the frontend in another terminal:

```bash
cd frontend
npm run dev
```

Open the address shown by the frontend development server.

> The backend resolves project persistence from the **opened project root** (`<project-root>/.local_openclaw/`), never from the process working directory. The backend can therefore be started from a different directory without changing the persistence identity of the opened project.

### Connect an AI agent (optional)

Register RIP as an MCP server in Claude Code, Claude Desktop, or another MCP client; see the [MCP Server guide](docs/architecture/backend/mcp-server.md) for the exact commands.

---

## 📚 Documentation

The repository contains detailed architecture, development, reference, and project-direction documentation.

- [**START-HERE**](docs/START-HERE.md) — Begin here if you're new to the project
- [**Architecture Overview**](docs/architecture/README.md) — System structure and architectural decisions
- [**Vision & Roadmap**](docs/vision/README.md) — Project direction and future plans
- [**Development Guide**](docs/development/environment.md) — Development environment setup
- [**API Reference**](docs/api/README.md) — API documentation
- [**Model Configuration**](docs/architecture/backend/models.md) — Local and hosted models, per-capability overrides, embeddings
- [**MCP Server**](docs/architecture/backend/mcp-server.md) — Connect Claude Code, Claude Desktop, or other MCP agents to RIP
- [**Reference**](docs/reference/glossary.md) — Glossary, configuration, and supporting references

---

## 📸 Screenshots

*Screenshots will be added as the frontend stabilizes.*

---

## 🚧 Project Status

RIP is under active development.

Repository scanning, indexing, retrieval, chat, reviewable editing, model configuration, and the MCP server are functional and covered by tests:

```text
repository → indexing → retrieval → chat → editing
                                  ↘ MCP server for agents
```

The current focus is on strengthening repository intelligence, improving the developer experience, and evolving the system without sacrificing its local-first and modular architecture.

See the [vision document](docs/vision/README.md) for the broader project direction.

---

## 🤝 Contributing

Contributions are welcome.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md) before getting started.

---

## 📄 License

Licensed under the [MIT License](LICENSE).

Copyright © 2026 Smit-whitespace.
