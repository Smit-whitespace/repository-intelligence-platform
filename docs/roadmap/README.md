# Roadmap

> **Status:** Living document — updated each sprint.

## Purpose

Documents what has shipped and the forward plan.

## Releases

- **v1.0.0** (2026-11-26) — first stable release. On top of Sprints 12.1 to 13: an API token with a one-use sign-in link, the MCP server for AI agents, search ranking measured and improved on a held-out set, screenshots, and CI on every pull request. Release steps: [release process](../development/release-process.md).

## Completed Milestones

- Sprint 12.1 — Project Initialization Service
- Sprint 12.2 — Repository-Aware Answer Quality
- Sprint 13 — CWD-Independent Project Persistence (persistence identity derives from the opened project root, never the process working directory; project-scoped retrieval; Windows file-handle cleanup; runtime-verified)

## In Progress

- Sprint 14 — **Response Quality.** Improve RIP's answers so they provide more comprehensive explanations and useful reasoning/context around repository findings, rather than merely returning terse source-grounded answers. This is a **response-quality improvement**, not a retrieval-correctness change.
  - Done: answers are measured (`python -m eval.answers`); a looping model can no longer write one answer for over an hour; a measured instruction and a 4,000-token context raised answer coverage from 31% to 43% on held-out questions without inventing more names.
  - Done (round 2): the held-out refusals turned out to come from an index older than the code, not from the prompt; on a fresh index the same prompt covers 64% held out with no refusals. A deeper-answer prompt improved the tuning questions but not the held-out ones, so it was not kept. Results: [Measuring Answer Quality](../architecture/backend/chat.md#measuring-answer-quality).
  - Open: deeper explanations without a cost elsewhere; two rounds of prompt wording have not produced them.

## Planned Milestones

- Sprint 15 — TBD. Proposed: index freshness. RIP refreshes a project's index only when the project is opened or reindexed, and does not say when the index is older than the files; in Sprint 14 a one-day-old index made the model refuse 27% of held-out questions.

## Format

Each sprint entry includes: Objective, Scope, Deliverables, Out of Scope, Exit Criteria.
