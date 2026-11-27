# Roadmap

> **Status:** Living document — updated each sprint.

## Purpose

Documents what has shipped and the forward plan.

## Releases

- **v1.1.0** (2026-11-27) — Sprint 14. Chat answers explain how the code works (held-out answer coverage 31% → 43%, no more invented names), measured with `python -m eval.answers`; a looping model can no longer write one answer for hours. RIP's data moves from `.local_openclaw` to `.rip` automatically on first start, and settings use `RIP_` (`LOC_` still works, with a warning). If a repository's `.gitignore` lists `.local_openclaw/`, add `.rip/` ([ADR-0021](../adr/adr-0021-rip-storage-and-settings-names.md)).
- **v1.0.0** (2026-11-26) — first stable release. On top of Sprints 12.1 to 13: an API token with a one-use sign-in link, the MCP server for AI agents, search ranking measured and improved on a held-out set, screenshots, and CI on every pull request. Release steps: [release process](../development/release-process.md).

## Completed Milestones

- Sprint 12.1 — Project Initialization Service
- Sprint 12.2 — Repository-Aware Answer Quality
- Sprint 13 — CWD-Independent Project Persistence (persistence identity derives from the opened project root, never the process working directory; project-scoped retrieval; Windows file-handle cleanup; runtime-verified)
- Sprint 14 — Response Quality: answers measured and made to explain the code flow; runaway answers capped; `.local_openclaw`/`LOC_` renamed to `.rip`/`RIP_` ([freeze report](../sprints/sprint-14.md); results in [Measuring Answer Quality](../architecture/backend/chat.md#measuring-answer-quality)). Deeper explanations without a cost elsewhere are deferred: two rounds of prompt wording did not produce them.

## Planned Milestones

- Sprint 15 — TBD. Proposed: index freshness. RIP refreshes a project's index only when the project is opened or reindexed, and does not say when the index is older than the files; in Sprint 14 a one-day-old index made the model refuse 27% of held-out questions.

## Format

Each sprint entry includes: Objective, Scope, Deliverables, Out of Scope, Exit Criteria.
