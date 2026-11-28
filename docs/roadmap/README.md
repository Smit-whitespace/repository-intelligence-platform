# Roadmap

> **Status:** Living document — updated each sprint.

## Purpose

Documents what has shipped and the forward plan.

## Releases

- **v1.2.0** (2026-11-28) — Sprint 15. Answers and semantic search reflect the files as they are now: chat, semantic search, edit planning and MCP `search_semantic` first update the files changed since indexing, for at most `RIP_INDEXING_REFRESH_SECONDS` (default 15; `0` turns it off), finish the rest in the background and say when files could not be included. The Dashboard's Indexing tile shows the real index state. API responses gain an `index` field, the chat stream sends `index-progress`, `index` and `error` events, and `GET /api/v1/workspace/index-status` is new ([ADR-0022](../adr/adr-0022-index-freshness.md)).
- **v1.1.0** (2026-11-27) — Sprint 14. Chat answers explain how the code works (held-out answer coverage 31% → 43%, no more invented names), measured with `python -m eval.answers`; a looping model can no longer write one answer for hours. RIP's data moves from `.local_openclaw` to `.rip` automatically on first start, and settings use `RIP_` (`LOC_` still works, with a warning). If a repository's `.gitignore` lists `.local_openclaw/`, add `.rip/` ([ADR-0021](../adr/adr-0021-rip-storage-and-settings-names.md)).
- **v1.0.0** (2026-11-26) — first stable release. On top of Sprints 12.1 to 13: an API token with a one-use sign-in link, the MCP server for AI agents, search ranking measured and improved on a held-out set, screenshots, and CI on every pull request. Release steps: [release process](../development/release-process.md).

## Completed Milestones

- Sprint 12.1 — Project Initialization Service
- Sprint 12.2 — Repository-Aware Answer Quality
- Sprint 13 — CWD-Independent Project Persistence (persistence identity derives from the opened project root, never the process working directory; project-scoped retrieval; Windows file-handle cleanup; runtime-verified)
- Sprint 14 — Response Quality: answers measured and made to explain the code flow; runaway answers capped; `.local_openclaw`/`LOC_` renamed to `.rip`/`RIP_` ([freeze report](../sprints/sprint-14.md); results in [Measuring Answer Quality](../architecture/backend/chat.md#measuring-answer-quality)). Deeper explanations without a cost elsewhere are deferred: two rounds of prompt wording did not produce them.
- Sprint 15 — Index freshness: answers and semantic search update changed files first, up to a time limit ([freeze report](../sprints/sprint-15.md), [ADR-0022](../adr/adr-0022-index-freshness.md)). On a deliberately stale index, held-out coverage 53.9% / 56.7% without it, 65.6% / 65.0% with it; a check with nothing changed takes 0.12 s warm.

## Planned Milestones

- None scheduled.

## Format

Each sprint entry includes: Objective, Scope, Deliverables, Out of Scope, Exit Criteria.
