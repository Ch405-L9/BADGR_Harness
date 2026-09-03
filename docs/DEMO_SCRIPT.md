# Live Research Demo Script

## Purpose

These commands demonstrate the web-research workflow safely. They use read-only web search and normal CLI output; they do not modify application data or external services.

Before recording, activate the virtual environment and ensure at least one search-provider API key is configured.

```bash
cd ~/projects/badgr_harness
source .venv/bin/activate
```

## Global Demo Pattern

Use this command structure for current or externally sourced questions:

```bash
PYTHONDONTWRITEBYTECODE=1 python orchestrator.py \
  --goal "Use live web research to answer: QUESTION. Prefer an official source, give me the source URL, and summarize the answer in 3 sentences."
```

Use this variation to expose the full provenance artifact:

```bash
PYTHONDONTWRITEBYTECODE=1 python orchestrator.py \
  --goal "Use live web research to answer: QUESTION. Prefer an official source, give me the source URL, and summarize the answer in 3 sentences." \
  --debug
```

## Showcase Commands

### 1. Official Ubuntu / Python answer

```bash
PYTHONDONTWRITEBYTECODE=1 python orchestrator.py \
  --goal "Use live web research to answer: Is Python 3.12 currently available for Ubuntu 24.04 LTS? Prefer an official Ubuntu source, give me the source URL, and summarize the answer in 3 sentences."
```

What it demonstrates:

- Explicit live-web research routing
- Official-domain preference
- Concise human-facing answer
- Source URL delivery
- Three-line benchmark formatting

### 2. Normal output versus debug evidence

Run normal mode first:

```bash
PYTHONDONTWRITEBYTECODE=1 python orchestrator.py \
  --goal "Use live web research to answer: Is Python 3.12 currently available for Ubuntu 24.04 LTS? Prefer an official Ubuntu source, give me the source URL, and summarize the answer in 3 sentences."
```

Then run debug mode:

```bash
PYTHONDONTWRITEBYTECODE=1 python orchestrator.py \
  --goal "Use live web research to answer: Is Python 3.12 currently available for Ubuntu 24.04 LTS? Prefer an official Ubuntu source, give me the source URL, and summarize the answer in 3 sentences." \
  --debug
```

What it demonstrates:

- Separation of user-facing output from internal diagnostics
- Provenance retained for evaluation
- Query, provider, sources, snippets, evidence, and live status visible only when requested

### 3. Capture output for a benchmark artifact

```bash
PYTHONDONTWRITEBYTECODE=1 python orchestrator.py \
  --goal "Use live web research to answer: Is Python 3.12 currently available for Ubuntu 24.04 LTS? Prefer an official Ubuntu source, give me the source URL, and summarize the answer in 3 sentences." \
  > /tmp/badgr-web-research-demo.txt

cat /tmp/badgr-web-research-demo.txt
```

What it demonstrates:

- Stdout is clean enough for an automated benchmark harness
- Answer output can be captured independently from debug artifacts

### 4. Run the test suite

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q
```

What it demonstrates:

- Regression coverage for routing, provider normalization, fallback behavior, output rendering, and the Ubuntu/Python benchmark answer contract

## One-Minute Presentation Narrative

“BADGR Harness now has a source-backed live web research path for questions that need current information. In the first version, retrieval worked: the system could query a live provider, return candidate sources, and identify authoritative domains. But the output was still a developer artifact—it exposed raw search snippets, search counts, and diagnostic language instead of answering the user naturally.

We iterated by separating normal and debug modes. Normal mode now produces a concise user-facing response, while debug mode keeps the provider, source list, snippets, evidence, and other provenance available for inspection. We also added an official-source preference and a regression-tested output contract for the Ubuntu and Python benchmark.

The key lesson was that retrieval quality and answer quality are separate problems. Finding a good source is not enough; the system has to synthesize a direct response while staying grounded in evidence. The current baseline attributes generic statements to the selected source and admits when evidence is insufficient. The next phase is page-level fetching and extraction, so answers can be based on verified page content rather than search snippets alone.”

## Recording Tips

- Start with normal mode so the audience sees the clean answer first.
- Run the same question with `--debug` to reveal the research provenance.
- Show `pytest -q` last as the validation step.
- Do not show API keys, `.env` files, terminal history containing secrets, or provider dashboards.
- If a live provider is unavailable during the recording, use the formatter regression test to demonstrate the deterministic rendering contract.
