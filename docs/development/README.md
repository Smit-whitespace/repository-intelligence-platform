# Development Documentation

> **Status:** Complete
> **Sprint Introduced:** Sprint 4
> **Last Updated:** Sprint 12.1
> **Reading Time:** 2 minutes
> **Audience:** All contributors
> **Prerequisites:** [Vision](../../vision/README.md)

---

## Executive Summary

This section documents everything required to develop, validate, and release Repository Intelligence Platform. Follow these guides to maintain architectural consistency across contributions.

---

## Contents

| Guide | Description |
|-------|-------------|
| [Environment Setup](environment.md) | Prerequisites, installation, configuration |
| [Coding Standards](standards.md) | Style, typing, naming, imports |
| [Validation Workflow](validation.md) | Ruff, MyPy, Pytest — how to run and interpret |
| [Testing Guide](testing.md) | Test structure, conventions, coverage |
| [Release Process](release-process.md) | Versioning, tagging, release checklist |
| [Sprint Workflow](sprint-workflow.md) | Planning, implementation, freeze process |

## Extension Guides

| Guide | Description |
|-------|-------------|
| [Adding a Backend Service](guides/adding-backend-service.md) | New service class + provider + injection |
| [Adding API Endpoints](guides/adding-api-endpoints.md) | Router, schema, dependency wiring |
| [Adding a Vector Store](guides/adding-vector-store.md) | Implement `VectorStore` for a new backend |
| [Adding Language Support](guides/adding-language-support.md) | Implement `ChunkAlgorithm` for a new language |

---

## Related Documents

| Document | Link |
|----------|------|
| Architecture | [architecture/](../architecture/system-overview.md) |
| ADR Index | [adr/](../adr/README.md) |
| Reference | [reference/](../reference/README.md) |
