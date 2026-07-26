# ADR-0014: Repository Scan Ownership

**Status:** Adopted

**Context:**

Both `RepositoryService.build_index()` and `IndexingService.index_repository()` scan the repository filesystem. This scan duplication was identified during Sprint 12.1 review. A decision was needed: eliminate the duplication by sharing scan results, or accept it as an architectural property.

**Decision:**

The duplicate scan is accepted as a known architectural property. `build_index()` uses `RepositoryScanner.scan()` + `enrich_fast()`. `index_repository()` uses `RepositoryScanner.scan()` + `enrich()`. They serve different consumers and have different enrichment requirements. Sharing scan results would require either:

1. Adding state to `RepositoryService` (rejected — services should be stateless)
2. Creating a shared scan result cache (rejected — optimization without proven need)

**Consequences:**

Positive:
- Services remain stateless
- No shared mutable state
- Each scan is correct for its enrichment path

Negative:
- Filesystem scanned twice during initialization
- Perceptible delay on large repositories

**Alternatives Considered:**

- Cache scan results in `ProjectInitializationService`: rejected — premature optimization, adds state
- Combine `build_index` and `index_repository` enrichment: rejected — they use different enrichment methods for different consumers
- Incremental optimization: planned — revisit when performance data demonstrates a need
