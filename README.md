<div align="center">

# Repository Intelligence Platform (RIP)

**An offline-first, repository-aware AI coding assistant.**

<a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
<img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+">
<img src="https://img.shields.io/badge/node-20+-green.svg" alt="Node 20+">

</div>

RIP runs entirely on your local machine — no cloud services, no API keys, and no repository data sent to hosted AI services.

It helps developers **understand, query, and safely modify codebases** by building repository-aware context that can be retrieved and supplied to a local LLM.

Instead of treating a repository as a collection of isolated text chunks, RIP provides a structured pipeline for turning a codebase into something both **developers and AI tools can query intelligently**.

---

## ✨ Features

- **💬 Repository-Aware Chat** — Ask questions about your codebase in natural language. RIP retrieves relevant repository context and answers based on the code that actually exists.

- **🔎 Semantic Retrieval** — Uses vector embeddings to identify relevant code for a query. Results are ranked, deduplicated, and assembled into focused context before generation.

- **✏️ Controlled Editing** — Plan, review, and apply code changes through explicit editing workflows. Changes can be backed by snapshots for rollback and inspection.

- **📁 Project Management** — Open a local project and let RIP manage repository scanning, indexing state, and project-local persistence.

- **🔒 Local-First Execution** — Repository analysis, retrieval, model inference, and editing workflows remain on your machine.

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

The goal is to make repository understanding a reusable capability for developers today — and a foundation that developer tools and AI agents can build on in the future.

---

## 🏗️ Architecture

RIP is built as a modular pipeline with clear subsystem boundaries:

| Subsystem | Responsibility |
|-----------|---------------|
| **Repository** | Scan, chunk, and manage repository files |
| **Indexing** | Embed chunks and store them in a vector database |
| **Retrieval** | Search indexed content by semantic similarity |
| **Chat** | Orchestrate retrieval, prompt assembly, and LLM generation |
| **Editing** | Plan, apply, review, and roll back code changes |

Every subsystem exposes a defined interface with concrete implementations behind it.

Components are wired through dependency injection, keeping the system testable and allowing individual parts of the repository-intelligence pipeline to evolve independently.

---

## 🔐 Privacy & Offline-First

RIP is designed around local execution.

- **100% local core workflow** — Repository scanning, retrieval, inference, and editing run locally.
- **No hosted LLM required** — Ollama provides local model execution.
- **No telemetry** — No analytics, crash reporting, or usage tracking is built into RIP.
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

---

## 📚 Documentation

The repository contains detailed architecture, development, reference, and project-direction documentation.

- [**START-HERE**](docs/START-HERE.md) — Begin here if you're new to the project
- [**Architecture Overview**](docs/architecture/README.md) — System structure and architectural decisions
- [**Vision & Roadmap**](docs/vision/README.md) — Project direction and future plans
- [**Development Guide**](docs/development/environment.md) — Development environment setup
- [**API Reference**](docs/api/README.md) — API documentation
- [**Reference**](docs/reference/glossary.md) — Glossary, configuration, and supporting references

---

## 📸 Screenshots

*Screenshots will be added as the frontend stabilizes.*

---

## 🚧 Project Status

RIP is under active development.

The core pipeline:

```text
repository → indexing → retrieval → chat → editing
```

is functional.

The current focus is on strengthening repository intelligence, improving the developer experience, and evolving the system without sacrificing its offline-first and modular architecture.

See the [vision document](docs/vision/README.md) for the broader project direction.

---

## 🤝 Contributing

Contributions are welcome.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md) before getting started.

---

## 📄 License

Licensed under the [MIT License](LICENSE).

Copyright © 2026 Smit-whitespace.
