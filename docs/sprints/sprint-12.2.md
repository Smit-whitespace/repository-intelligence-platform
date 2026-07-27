# Sprint 12.2 — Repository-Aware Answer Quality

## Sprint Objective

Improve the quality of repository-aware chat responses by enhancing retrieval precision, context assembly structure, prompt grounding, and providing a repeatable evaluation framework — all within the existing frozen architecture (no interface changes, no subsystem merges).

## Stabilization Overview

After the initial four-slice implementation, a stabilization pass resolved four remaining engineering concerns:
1. **Token Budgeting** — replaced character-based budget with `tiktoken`-based token counting
2. **Retrieval Score Semantics** — documented `similarity_score` as a heuristic ranking score (not cosine similarity)
3. **Repository Grounding Prompt** — strengthened prompt language (repository-specific "I couldn't find enough evidence", explicit anti-fabrication rules, no-context distinction)
4. **Golden Repository Evaluation Suite** — 20 curated benchmarks covering all subsystems

## Architecture Changes

**No architectural changes.** All modifications are internal to existing service implementations and new standalone modules:

- `RetrievalService.search()` — added deduplication, score normalization, score documentation
- `DefaultContextAssembly.assemble()` — added similarity filtering, content deduplication, file-grouped ordering, token budget, grounding instruction, context overview, empty-context path
- `backend/eval/` — new standalone evaluation module (not wired into the app)

```
Before Sprint 12.2:
    RetrievalService.search()
        ├── raw L2 distances returned as similarity_score
        └── duplicate chunk_ids preserved
    DefaultContextAssembly.assemble()
        ├── all results included verbatim
        ├── flat relevance-order concatenation
        └── weak system prompt: "Use the provided repository context"

After Sprint 12.2:
    RetrievalService.search()
        ├── L2 distance → 0-1 ranking score via 1/(1+d)
        │   └── documented as heuristic, not calibrated cosine similarity
        ├── duplicate chunk_ids deduplicated (keeps lowest distance)
        └── order preserved
    DefaultContextAssembly.assemble()
        ├── results below min_similarity filtered (default 0.3)
        ├── duplicate content removed
        ├── grouped by file path, sorted by start_line
        ├── file groups ordered by best relevance in group
        ├── token budget enforced via tiktoken (default 2000 tokens)
        ├── grounding instruction: cite sources, repo-specific "I couldn't find enough evidence"
        │   └── anti-fabrication rules (files, functions, classes, APIs)
        ├── context overview listing files and relevance levels
        ├── no-context instruction distinguishing general vs. repo knowledge
        └── when all results filtered: no-context path triggered
```

## Files Changed

### Implementation (4 files)

| File | Action | Description |
|------|--------|-------------|
| `backend/app/indexing/retrieval_service.py` | Modified | Added `_deduplicate()`, `_normalize_score()`, documented score semantics |
| `backend/app/indexing/retrieval_models.py` | Modified | Documented `similarity_score` as heuristic ranking metric |
| `backend/app/context_assembly/service.py` | Modified | Added similarity filter, content dedup, file grouping, token budget via `tiktoken`, grounding prompt, context overview, no-context path |
| `backend/app/context_assembly/providers.py` | Formatted | Lint formatting only |

### Evaluation Suite (4 files)

| File | Action | Description |
|------|--------|-------------|
| `backend/eval/__init__.py` | Created | Evaluation suite package |
| `backend/eval/models.py` | Created | `RetrievalTestCase` (extended with `expected_concepts`, `expected_symbols`), `RetrievalEvalResult`, `RetrievalEvalReport` |
| `backend/eval/metrics.py` | Created | `precision`, `recall`, `f1_score`, `reciprocal_rank` |
| `backend/eval/runner.py` | Created | `RetrievalEvaluator`, `create_retrieval_evaluator` factory |
| `backend/eval/benchmarks.py` | Created | 20 golden repository benchmarks covering all subsystems |

### Tests (8 files)

| File | Action | Description |
|------|--------|-------------|
| `backend/tests/indexing/test_retrieval_service.py` | Created | 12 tests: deduplication, score normalization, empty results, order preservation |
| `backend/tests/context_assembly/__init__.py` | Created | Test package |
| `backend/tests/context_assembly/test_service.py` | Created | 15 tests: filtering, dedup, grouping, token budget, grounding, overview, no-context |
| `backend/tests/eval/__init__.py` | Created | Test package |
| `backend/tests/eval/test_metrics.py` | Created | 17 tests: precision, recall, F1, reciprocal rank |
| `backend/tests/eval/test_runner.py` | Created | 8 tests: evaluator with mock service |
| `backend/tests/eval/test_benchmarks.py` | Created | 9 tests: benchmark count, validity, coverage across subsystems |
| `backend/tests/api/test_workflows.py` | Modified | Updated message index for 4-message prompt structure |

## Completed Stabilization Tasks

| Task | Scope | Status |
|------|-------|--------|
| 1 — Token Budgeting | `max_context_chars` → `max_context_tokens` (2000 default), `tiktoken` `cl100k_base` encoding, per-block token counting | ✅ |
| 2 — Retrieval Score Semantics | `similarity_score` documented as heuristic ranking score (not cosine similarity), `_normalize_score` docstring updated | ✅ |
| 3 — Repository Grounding Prompt | Repository-specific "I couldn't find enough evidence", anti-fabrication rules, no-context distinction between general and repo knowledge | ✅ |
| 4 — Golden Repository Evaluation Suite | 20 benchmarks covering project init, scanning, indexing, retrieval, context assembly, chat, editing, storage, DI, architecture ownership | ✅ |

## Final Behavior

### Retrieval (`RetrievalService.search()`)

- Accepts `SearchQuery` with `query` string and optional `limit` (default 10)
- Embeds query via `EmbeddingProvider`
- Searches `VectorStore` for nearest neighbors
- Deduplicates by `chunk_id` (keeps lowest distance)
- Converts L2 distance to heuristic ranking score via `1 / (1 + distance)`
- Returns `SearchResponse` with ordered results
- Score is documented as relative ranking metric, not calibrated similarity

### Context Assembly (`DefaultContextAssembly.assemble()`)

- Filters results below `min_similarity` (default 0.3)
- Removes duplicate content
- Groups by file path, sorts chunks by `boundary.start_line`
- Orders file groups by best relevance score (descending)
- Builds per-file blocks: `File: {path}\n\n{content}`
- Enforces token budget via `tiktoken` `cl100k_base` (default 2000 tokens)
- Produces a 4-message prompt: system instruction → context overview → repository context → user query
- When no results: 2-message prompt: no-context instruction → user query

### Grounding (system prompt)

- With context: instructs to answer ONLY from provided context, cite source file paths, respond with "I couldn't find enough evidence in the indexed repository" when evidence is insufficient, never fabricate files/functions/classes/APIs
- Without context: instructs to clearly distinguish general knowledge from repository expectations, never fabricate code

### Evaluation Suite (`eval/`)

- `RetrievalTestCase`: query + expected file paths + optional expected content/concepts/symbols
- Metrics: precision, recall, F1, reciprocal rank (MRR)
- `RetrievalEvaluator`: runs retrieval against test cases, computes per-case and aggregate metrics
- `BENCHMARKS`: 20 curated test cases covering all architectural subsystems

## Validation Results

| Gate | Result | Notes |
|------|--------|-------|
| Ruff | ✅ All checks passed | — |
| MyPy | ✅ No issues | — |
| Pytest | ✅ 174 passed, 1 failed | `test_no_custom_middleware_is_registered` is pre-existing (CORS middleware mismatch, unrelated) |

## Known Technical Debt

- **Score normalization is heuristic**: `1 / (1 + distance)` is not calibrated to the embedding model's actual distribution. Documented as a ranking score, not cosine similarity.
- **No conversation history**: The prompt has no interleaving with prior turns (out of scope for this sprint).
- **Token encoding is model-independent**: `cl100k_base` is a reasonable default but may not match every chat model's tokenizer exactly.
- **Evaluation suite not wired into CI**: Benchmarks exist but are not automatically run on changes.

## Deferred Work

- **Calibrated score normalization**: Replace heuristic with distribution-aware normalization (min-max or z-score over a representative query set).
- **Model-specific token encoding**: Use the chat model's actual tokenizer for precise budget enforcement.
- **CI integration**: Wire the evaluation suite into CI to detect retrieval regressions automatically.
- **Conversational history**: Extend prompt to include prior turns for multi-turn chat.
- **Benchmark-driven tuning**: Use the golden suite to tune `min_similarity` and `max_context_tokens` defaults.

## Lessons Learned

- **Token budget changes test behavior**: Switching from char to token budgeting changes which chunks fit within a given budget. Tests that hardcode budget values with specific content must account for token counts of the formatted block (including `File: {path}\n\n` prefix), not just the content string.
- **Block-level vs content-level budget checks**: The content-level pre-check (`total_tokens + group_tokens + content_token`) is optimistic and can admit content whose formatted block later exceeds the budget via the block-level check. This is by design — the block-level check acts as the hard cutoff, and the content-level pre-check prevents wasted work.
- **Same-file grouping interacts with budget**: When multiple chunks from the same file fail the block-level budget check, the entire file group is skipped. Tests should use separate files when testing per-chunk budget enforcement.
- **Prompt engineering is test-sensitive**: Changing instruction wording requires updating multiple test assertions across the test suite. Constants like `_CONTEXT_MSG_INDEX` and `_USER_MSG_INDEX` reduce maintenance burden.
- **Platform path separators**: `str(Path("src/main.py"))` produces `src\main.py` on Windows. Use `str(Path(...))` in assertions rather than hardcoded forward slashes.

---

**Sprint 12.2 is now FROZEN.**
