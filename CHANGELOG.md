# Changelog

## Unreleased

### Live Web Research Baseline

- Finalized the source-backed live web research baseline for the research task boundary.
- Documented Brave Search as the first provider and SerpAPI as the fallback when `SEARCH_PROVIDER=auto`.
- Clarified that explicitly selecting `brave` or `serpapi` does not invoke the alternate provider.
- Preserved fail-closed behavior when no configured provider can return usable live-search results.
- Preserved source provenance including provider, query, title, URL, snippets, evidence, and source count.
- Confirmed normal output is separated from structured debug output.
- Documented the current boundary: search-result snippets are used as evidence, but selected source pages are not yet fetched and independently verified.
- Established the Part 1 gate as ready to proceed to the LOCAL agent training phase.
- Preserved the current BM25 dataset submodule state for separate review; no dataset reset, checkout, repair, or commit is included in this change.
- Deferred the root-owned `__pycache__` permission issue because it is not required for the current test path, which uses `PYTHONDONTWRITEBYTECODE=1`.
- Recorded the missing parent `.gitmodules` metadata as a separate repository issue; it is intentionally outside this research-baseline change.

- Normalized the public schema surface to canonical modules in `schemas/task_schema.py` and `schemas/log_schema.py`.
- Removed redundant duplicate implementation files from the public code path and retained only a minimal compatibility shim where needed.
- Updated the public README to document the canonical schema policy and the branch scope.

