# Sprint 14 — Response Quality

## Sprint Objective

Make RIP's chat answers explain more — how the code works and why — instead of only pointing at source files, without inventing files, classes or functions. Every change had to be measured: kept only if it beat the gap between two runs of the same version, invented no more names, refused no more often, and held up on 15 held-out questions never used for tuning.

## Architecture Changes

No subsystem boundaries moved. Changes inside the chat path, a new evaluation tool, and the storage and settings names:

```
Before Sprint 14:
    ChatService → ContextAssembly (rules-only instruction, 2,000-token context)
        → OllamaChatProvider (no output cap; timeout never applied)
    Answer quality: not measured
    Storage: <root>/.local_openclaw, ~/.local_openclaw; settings: LOC_*

After Sprint 14:
    ChatService → ContextAssembly ("explain the flow" instruction, 4,000-token context)
        → OllamaChatProvider (4,096-token cap with a visible note; streams, so the
          timeout means "Ollama went silent")
    Answer quality: python -m eval.answers (coverage, invented names, refusals)
    Storage: <root>/.rip, ~/.rip (moved automatically); settings: RIP_* (LOC_* still read)
```

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `backend/app/chat/ollama_provider.py` | Modified | Output cap, truncation note, timeout that applies |
| `backend/app/llm/factory.py` | Modified | Passes the provider's timeout |
| `backend/app/context_assembly/service.py` | Modified | Measured instruction; 4,000-token default context |
| `backend/eval/answer_quality.py`, `backend/eval/answers.py` | Created | Answer scoring and its CLI |
| `backend/app/core/storage/locations.py` | Modified | `.rip`, `user_storage_directory`, moving `.local_openclaw` |
| `backend/app/core/config/provider.py` | Modified | `RIP_` prefix, `LOC_` fallback with a warning |
| `backend/app/core/security/api_token.py`, `backend/app/core/storage/integrity.py`, `backend/app/llm/store.py`, `backend/app/repository/ignore.py` | Modified | Per-user paths and ignore rules use the new names |
| `docs/adr/adr-0021-rip-storage-and-settings-names.md` | Created | The rename decision |
| `docs/architecture/backend/chat.md` | Modified | "Measuring Answer Quality": method and both rounds |

## Vertical Slices

| Slice | Scope | Status |
|-------|-------|--------|
| 1 — Runaway answers | A looping model wrote one answer for over 1.5 hours; capped, with a working timeout | ✅ |
| 2 — Answer evaluation | `python -m eval.answers`: coverage of expected files, symbols and concepts; invented names; refusals | ✅ |
| 3 — Prompt round 1 | "Explain the flow" + 4,000-token context: held-out coverage 31% → 43%, inventing 13%/0% → 0%/0% | ✅ shipped |
| 4 — Prompt round 2 | Fresh index; exact-names rule (no effect); deeper-answer prompt better on tuning but worse held out (54% vs 64%) | ✅ measured, nothing shipped |
| 5 — `.rip` / `RIP_` rename | Last Local OpenClaw names replaced; existing data moved automatically (ADR-0021) | ✅ |

## Validation Results

| Gate | Result | Notes |
|------|--------|-------|
| Ruff | ✅ All checks passed | — |
| MyPy | ✅ No issues (`app`, `eval`) | — |
| Pytest | ✅ 607 passed, 2 skipped | — |
| Frontend | ✅ typecheck, ESLint, 43 Vitest tests | — |
| CI | ✅ Backend and Frontend on every PR | — |

## Known Technical Debt

- The `LOC_` fallback and the `.local_openclaw` legacy name are compatibility code, to remove in a later major version.
- Coverage counts expected names and concept words; it stands in for a useful explanation, so reports still need reading.
- The Python package is still named `local-openclaw` in `pyproject.toml`.

## Deferred Work

- **Deeper explanations without a cost elsewhere.** Two rounds of prompt wording did not produce them; the deeper prompt named classes instead of files on held-out questions.
- **Index freshness** (proposed Sprint 15): RIP does not say when the index is older than the files, and a one-day-old index made the model refuse 27% of held-out questions.
- **`SignIn.tsx` search miss**: one held-out question whose expected file search does not return.

## Lessons Learned

- **Check the inputs before tuning the prompt.** The "over-cautious" refusals of round 1 were correct refusals: the index was older than the code. A fresh index raised held-out coverage from 43% to 64% with no prompt change, more than any prompt did.
- **The held-out set earns its keep.** The deeper-answer prompt won on the tuning questions (16 better, 7 worse) and lost held out (2 better, 6 worse).
- **Measure on a frozen, freshly indexed copy**, so editing the code during a run cannot change what is measured.
- **A test that starts a real process must get the test's settings and home folder.** One MCP server test used the developer's real home folder; with the automatic move in place, running the suite renamed it.

---

**Sprint 14 is now FROZEN.**
