# BADGR Harness Live Web Research Baseline Report

**Status:** Implemented and locally validated  
**Branch:** `main`  
**Validation:** 90 tests passed  
**Scope:** Live source-backed research baseline, clean normal output, structured debug output, and evidence-attributed rendering

## Executive Summary

This update adds a provider-backed live web research workflow to BADGR Harness. The system can route explicit research requests to configured live-search providers, preserve source provenance, prefer selected official or institutional domains, and produce a concise user-facing response by default.

The implementation separates normal output from debug output. Normal mode is designed for users and benchmark capture; debug mode retains the structured research artifact needed to inspect the query, provider, source list, snippets, evidence, source count, confidence value, and live-search status.

The work was validated locally with 90 passing automated tests. The current implementation is intentionally documented as a retrieval and evidence-rendering baseline: live search results are available and attributed, but selected pages are not yet fetched and parsed for full page-level verification.

## Delivered Changes

### Live Search Baseline

The research subsystem supports provider-backed search with:

- Brave Search when `BRAVE_SEARCH_API_KEY` is configured
- SerpAPI when `SERPAPI_API_KEY` is configured
- Automatic provider fallback when `SEARCH_PROVIDER=auto`
- Safe failure when no configured provider can return results
- Structured preservation of titles, URLs, snippets, provider identity, and evidence

### Research Output Modes

The command-line interface now supports:

```bash
python orchestrator.py --goal "..."
```

for concise normal output, and:

```bash
python orchestrator.py --goal "..." --debug
```

for full structured research/debug output.

This prevents internal phrases such as “Live search returned N source result(s)” from appearing in the default user response.

### Evidence-Attributed Rendering

The renderer now:

- Selects a preferred source using an authority heuristic
- Produces a direct answer for the tested Python 3.12 / Ubuntu 24.04 request
- Attributes generic rendered evidence to the selected source
- Provides a clear insufficient-evidence response when no usable snippet exists
- Preserves a source URL in all normal source-backed answers

## Benchmark Demonstration

### Input

```text
Use live web research to answer: Is Python 3.12 currently available for Ubuntu 24.04 LTS? Prefer an official Ubuntu source, give me the source URL, and summarize the answer in 3 sentences.
```

### Expected Normal Output

```text
Yes, Python 3.12 is currently available for Ubuntu 24.04 LTS (Noble Numbat).
Ubuntu’s official documentation lists Python 3.12 as the available Python 3 version for that release.
Source: https://ubuntu.com/developers/docs/reference/availability/python/
```

### Required Behavior

- Direct answer starts with “Yes, Python 3.12”
- Official Ubuntu source URL is present
- Output has exactly three lines
- Raw search-result ellipses are absent
- Internal ranking text is absent
- The source URL is a plain URL in the Python return value

## Validation Evidence

The latest local test run completed successfully:

```text
90 passed
```

The formatter regression contract checks that the Ubuntu/Python answer:

- Begins with the expected direct answer
- Contains the Ubuntu documentation URL
- Has two newline characters, corresponding to three lines
- Does not contain raw `...` snippet text
- Does not contain “The top official source”
- Does not contain Markdown link syntax in the returned string

## Technical Boundaries

### What This Baseline Does

- Performs live provider-backed search
- Captures source provenance
- Ranks selected authority domains ahead of generic domains
- Distinguishes normal output from debug output
- Attributes generic evidence rather than presenting it as unsupported system knowledge
- Fails rather than fabricating a result when no live provider returns sources

### What This Baseline Does Not Yet Do

- Fetch and parse the selected source page
- Extract page-level passages tied precisely to the question
- Independently verify that a search snippet matches the current source page
- Calibrate confidence from validated historical outcomes
- Provide a general semantic authority model across all domains and topics
- Guarantee a complete answer when snippets are truncated or context-poor

## Risk and Mitigation

| Risk | Current Mitigation | Recommended Next Improvement |
|---|---|---|
| Search snippets are incomplete or truncated | Generic answers attribute content to the selected source | Fetch and extract the selected page |
| Search ranking does not prove truth | Authority heuristic is only a preference signal | Add relevance and evidence-entailment checks |
| User output leaks diagnostics | Normal and `--debug` modes are separated | Add CLI snapshot tests |
| No provider is configured | Raises a safe research error | Add clear setup guidance in the CLI |
| Confidence is not calibrated | Confidence remains a diagnostic field | Evaluate against labeled benchmark cases and calibrate |

## Recommended Roadmap

### Phase 1: Completed

- Live search provider integration
- Research routing
- Source provenance fields
- Human-readable normal output
- Debug artifact mode
- Ubuntu/Python output regression test
- Evidence-attributed fallback

### Phase 2: Page-Level Evidence

Add an HTTP fetcher for the selected source URL, then:

```text
Search
  -> rank sources
  -> fetch selected page
  -> extract readable text
  -> find question-relevant evidence
  -> answer only from extracted evidence
  -> retain source URL and passage in debug output
```

### Phase 3: Grounded Synthesis

Use a constrained answer-generation prompt or deterministic template that requires:

- Direct answer to the original question
- Claims limited to extracted evidence
- Explicit uncertainty when evidence is insufficient
- Source URL in the requested format
- No provider/debug/ranking language in normal output

### Phase 4: Evaluation and Confidence

Build a labeled benchmark set with expected answers, source-quality requirements, and output constraints. Measure retrieval quality separately from generation quality, then calibrate confidence based on observed correctness rather than using a fixed or uninitialized value.

## Operational Commands

### Activate the environment

```bash
cd ~/projects/badgr_harness
source .venv/bin/activate
```

### Run all tests

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q
```

### Run normal research mode

```bash
PYTHONDONTWRITEBYTECODE=1 python orchestrator.py \
  --goal "Use live web research to answer: Is Python 3.12 currently available for Ubuntu 24.04 LTS? Prefer an official Ubuntu source, give me the source URL, and summarize the answer in 3 sentences."
```

### Run debug research mode

```bash
PYTHONDONTWRITEBYTECODE=1 python orchestrator.py \
  --goal "Use live web research to answer: Is Python 3.12 currently available for Ubuntu 24.04 LTS? Prefer an official Ubuntu source, give me the source URL, and summarize the answer in 3 sentences." \
  --debug
```

## Conclusion

BADGR Harness now has a tested, auditable live web research baseline. The most important improvement is architectural: research retrieval is no longer treated as the final user experience. The system now separates evidence collection from user-facing rendering, keeps audit details available in debug mode, and applies more truthful evidence-attributed language when a fully direct answer is not available.

The next high-value improvement is page-level evidence extraction. That is the path from source-backed search snippets to consistently grounded, natural research answers.
