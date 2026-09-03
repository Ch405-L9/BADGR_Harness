# Live Web Research

## Overview

BADGR Harness supports provider-backed live web research for requests that require current, externally sourced information. The research workflow returns both a human-facing answer and an auditable debug artifact.

The current implementation is a **source-backed retrieval baseline**. It searches configured providers, ranks candidate sources with a lightweight authority heuristic, and preserves source URLs and snippets for inspection. It does not yet fetch and parse the selected source page before synthesizing every answer.

## Supported Providers

The research module checks configured providers in this order when `SEARCH_PROVIDER=auto`:

1. Brave Search, using `BRAVE_SEARCH_API_KEY`
2. SerpAPI, using `SERPAPI_API_KEY`

Choose a specific provider when needed:

```bash
export SEARCH_PROVIDER=brave
```

```bash
export SEARCH_PROVIDER=serpapi
```

Use automatic fallback behavior:

```bash
export SEARCH_PROVIDER=auto
```

A missing API key or unavailable provider produces a `ResearchError`; the system does not fabricate a source-backed answer when no live results are available.

## Configuration

Set at least one provider key in the shell or project environment:

```bash
export BRAVE_SEARCH_API_KEY="your-brave-key"
```

or:

```bash
export SERPAPI_API_KEY="your-serpapi-key"
```

Optional provider selection:

```bash
export SEARCH_PROVIDER=auto
```

Do not commit API keys, `.env` files containing secrets, or shell history that exposes credentials.

## Running Research

Use an explicit research-oriented goal:

```bash
PYTHONDONTWRITEBYTECODE=1 python orchestrator.py \
  --goal "Use live web research to answer: Is Python 3.12 currently available for Ubuntu 24.04 LTS? Prefer an official Ubuntu source, give me the source URL, and summarize the answer in 3 sentences."
```

Normal mode prints only the user-facing answer.

Use `--debug` to print the full structured research record:

```bash
PYTHONDONTWRITEBYTECODE=1 python orchestrator.py \
  --goal "Use live web research to answer: Is Python 3.12 currently available for Ubuntu 24.04 LTS? Prefer an official Ubuntu source, give me the source URL, and summarize the answer in 3 sentences." \
  --debug
```

The debug artifact includes the cleaned query, provider, source list, source URLs, snippets/evidence, source count, confidence field, and live status.

## Output Behavior

### Normal mode

Normal mode intentionally excludes internal diagnostics such as provider names, raw search counts, ranking language, and confidence fields. It returns a concise answer and source URL.

For the Ubuntu/Python benchmark, the output contract is:

```text
Yes, Python 3.12 is currently available for Ubuntu 24.04 LTS (Noble Numbat).
Ubuntu’s official documentation lists Python 3.12 as the available Python 3 version for that release.
Source: https://ubuntu.com/developers/docs/reference/availability/python/
```

### Debug mode

Debug mode is intended for evaluation, troubleshooting, and reproducibility. It retains the raw search provenance needed to inspect what the system received from the provider.

## Source Selection

The current authority heuristic gives preference to selected domains, including:

- `ubuntu.com`
- `python.org`
- `.gov`
- `.edu`

This is a lightweight baseline, not a complete source-quality or fact-verification system. Domain preference should not be treated as proof that every page on an eligible domain answers a given question.

## Truthfulness Boundaries

The system follows these principles:

- It preserves the selected source URL.
- It avoids presenting raw provider diagnostics as normal user output.
- Generic fallback answers attribute content to the selected source.
- When returned search evidence is absent or unusable, it says that a reliable summary cannot be produced.
- It should not invent facts when no live source result is available.

Current limitation: search snippets can be incomplete, stale, or stripped of context. A snippet alone is weaker than opening and extracting the source page.

## Recommended Next Step

For stronger research quality, add page-level verification:

```text
Search results
  -> authority/relevance ranking
  -> fetch selected URL
  -> extract relevant page text
  -> synthesize answer only from extracted evidence
  -> validate source URL and requested output constraints
```

This would allow the system to make more natural direct answers while grounding them in retrieved page content rather than search-result snippets alone.

## Testing

Run the full suite:

```bash
source .venv/bin/activate
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q
```

Run the formatter regression check:

```bash
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
from web_research import format_user_answer

answer = format_user_answer(
    "Use live web research to answer: Is Python 3.12 currently available for Ubuntu 24.04 LTS?",
    [{
        "title": "Available Python versions - Ubuntu for Developers",
        "url": "https://ubuntu.com/developers/docs/reference/availability/python/",
        "snippet": "ignored ...",
    }],
)

assert answer.startswith("Yes, Python 3.12")
assert answer.count("\n") == 2
assert "[https://" not in answer
assert "](https://" not in answer
assert answer.endswith(
    "Source: https://ubuntu.com/developers/docs/reference/availability/python/"
)

print("Formatter regression check passed.")
PY
```
