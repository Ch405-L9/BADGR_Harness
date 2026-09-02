# BADGR Harness Search Baseline — Changelog and Test Runbook

**Status:** Ready for owner-side live-provider verification  
**Scope:** Source-backed web research only; no architecture redesign

## What was found

The active `BADGR_Harness` repository did not contain SerpApi or Brave integration. Its active web surface was `web_ops_mcp.py`, which uses DuckDuckGo and browser/page extraction helpers. The orchestrator sent the original live-web goal directly to Ollama, so the model could answer from prior knowledge without a retrieval boundary. That explains the benchmark result: the claim was plausible, but no source URL or evidence was required by the execution path.

The current checkout is the public `main` branch at commit `30490de001a22822bec8b664c7e6e872045f7c68`. The Pro Hunter project was not present in this checkout or in the sandbox. No SerpApi or Brave code was found in the repository's tracked history. A separate screenshot referenced additional systems, but screenshots were treated as context rather than proof.

## Implemented baseline

The new `web_research.py` module provides a narrow, auditable search boundary. It uses the official Brave Web Search API first when `SEARCH_PROVIDER=auto` and `BRAVE_SEARCH_API_KEY` is set. It falls back to SerpApi when Brave is unavailable and `SERPAPI_API_KEY` is configured. It supports explicit provider selection through `SEARCH_PROVIDER=brave` or `SEARCH_PROVIDER=serpapi`.

Each successful result contains the normalized query, provider name, title, URL, snippet, source count, evidence excerpts, and a three-sentence summary. The boundary fails closed when no provider is configured or when all providers fail. It never fabricates a citation or reports a mocked result as live.

Research intent is now classified before generic classification keywords. Goals containing language such as `live web research`, `web search`, `search online`, `source URL`, `cite`, or `sources` route to the research boundary. The ordinary Ollama orchestration path remains unchanged for non-research tasks.

The `.env.example` file now documents the provider variables. Credentials must be placed only in the user's private `.env` file and must never be committed.

## Files changed

| File | Change |
|---|---|
| `web_research.py` | Added Brave-first / SerpApi-fallback search boundary and provenance-rich output. |
| `router.py` | Added explicit research classification before generic classification. |
| `schemas/task_schema.py` | Added `TaskType.RESEARCH`. |
| `orchestrator.py` | Routes research goals to the live evidence boundary. |
| `.env.example` | Documents provider variables without values. |
| `requirements.txt` | Retains the earlier optional scraper dependency correction (`beautifulsoup4`, `lxml`). |
| `tests/test_web_research.py` | Added provider parsing, fallback, routing, no-key failure, and JSON-safety tests. |

## Exact test commands

From the repository root:

```bash
source .venv/bin/activate
set -a
source .env
set +a
python -m pytest -q
```

The expanded clean-room run completed with **88 passed and 2 warnings** in **1.61 seconds**. The warnings came from the installed Starlette/HTTPX test-client compatibility layer and did not fail the suite.

To confirm that the configured provider variables are present without printing secret values:

```bash
for n in BRAVE_SEARCH_API_KEY SERPAPI_API_KEY SEARCH_PROVIDER; do
  if [ -n "${!n:-}" ]; then echo "$n=SET"; else echo "$n=UNSET"; fi
done
```

To run the requested live benchmark:

```bash
PYTHONDONTWRITEBYTECODE=1 python orchestrator.py --goal "Use live web research to answer: Is Python 3.12 currently available for Ubuntu 24.04 LTS? Prefer an official Ubuntu source, give me the source URL, and summarize the answer in 3 sentences."
```

Expected output properties are:

| Property | Required behavior |
|---|---|
| `task_type` | `research` |
| `provider` | `brave` or `serpapi` |
| `summary` | Exactly three evidence-oriented sentences |
| `sources` | Non-empty list containing title, URL, snippet, and provider |
| `source_count` | Equal to the number of returned sources |
| `live` | `true` |
| unsupported/no-key case | Non-zero failure with `No live search results available`; no fabricated answer |

To test provider selection explicitly:

```bash
SEARCH_PROVIDER=brave PYTHONDONTWRITEBYTECODE=1 python orchestrator.py --goal "Use live web research to answer: Is Python 3.12 currently available for Ubuntu 24.04 LTS? Prefer an official Ubuntu source, give me the source URL, and summarize the answer in 3 sentences."
SEARCH_PROVIDER=serpapi PYTHONDONTWRITEBYTECODE=1 python orchestrator.py --goal "Use live web research to answer: Is Python 3.12 currently available for Ubuntu 24.04 LTS? Prefer an official Ubuntu source, give me the source URL, and summarize the answer in 3 sentences."
```

Do not run both explicit commands against the same provider unless the account quota permits it.

## Verification limits

The sandbox used for implementation had neither `BRAVE_SEARCH_API_KEY` nor `SERPAPI_API_KEY`, and the local Ollama service was not reachable. Therefore, the live external-provider benchmark could not be honestly marked as passed here. The provider adapters were tested with deterministic mocked API payloads, and the no-key failure was tested directly. Owner-side execution with a real provider key is still required before claiming live-search readiness.

The implementation does not scrape search-result HTML, bypass access controls, or invoke outbound URLs returned by search. Search snippets are treated as untrusted evidence. A future source-reading stage should fetch selected sources with timeouts, preserve the original URLs, and keep the final answer tied to the retrieved evidence.

## References

[1]: https://api-dashboard.search.brave.com/app/documentation/web-search/get-started "Brave Search API Web Search Getting Started"
[2]: https://serpapi.com/search-api "SerpApi Google Search Engine Results API"
