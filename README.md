<p align="center">
  <h1 align="center">Repository Intelligence Platform (RIP)</h1>
  <p align="center"><strong>An offline-first, repository-aware AI coding assistant.</strong></p>
  <p align="center">
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
    <img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+">
    <img src="https://img.shields.io/badge/node-20+-green.svg" alt="Node 20+">
  </p>
</p>

RIP runs entirely on your local machine — no cloud services, no API keys, no data ever leaves your computer. It understands your codebase, answers natural-language questions about it, and helps you make changes with confidence.

---

## Screenshots

*Screenshots will be added after the first stable release.*

---

## Features

- **Repository-Aware Chat** — Ask questions about your codebase in natural language. RIP retrieves relevant code context and answers based on your actual repository structure.
- **Semantic Retrieval** — Uses vector embeddings to find the most relevant code for any query. Results are ranked, deduplicated, and assembled into context for accurate answers.
- **Controlled Editing** — Plan, review, and apply code changes with confidence. Editing operations are versioned with snapshots for rollback.
- **Project Management** — Open any project directory and RIP automatically indexes its structure, code semantics, and dependencies.

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
| **Editing** | Apply, review, and rollback code changes |

Every subsystem has a public interface and at least one implementation. Components are wired through dependency injection, making the system testable and extensible.

## Privacy & Offline-First

- **100% offline** — All computation runs locally. No cloud dependency.
- **No telemetry** — No data is sent anywhere. No analytics, no crash reports, no usage tracking.
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
- [Reference](docs/reference/glossary.md) — Glossary, configuration, cheat sheets

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md) before getting started.

## Project Status

RIP is in active development. The core pipeline (repository scanning → indexing → retrieval → chat → editing) is functional. See the [vision document](docs/vision/README.md) for the roadmap.

## License

Licensed under the [MIT License](LICENSE). Copyright (c) 2026 Smit-whitespace.
