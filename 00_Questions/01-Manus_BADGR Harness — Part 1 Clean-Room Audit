# BADGR Harness — Part 1 Clean-Room Audit

**Audit date:** 2026-09-02  
**Repository:** `https://github.com/Ch405-L9/BADGR_Harness`  
**Audited checkout:** `/home/ubuntu/projects/badgr_harness`  
**Authoritative requested path:** `/home/t0n34781/projects/badgr_harness` (not present in this sandbox)

## A. Executive Verdict

**FUNCTIONAL WITH FIXES.** The core BADGR Harness imports cleanly, compiles, and passes all repository tests in an isolated clean-room virtual environment. The deterministic mocked orchestration path was also executed successfully and persisted the expected event lineage. The configured live model path is not demonstrable in this environment because Ollama is unreachable and no live model endpoint responded. One optional scraper dependency defect was found and corrected by declaring `beautifulsoup4` and `lxml` in `requirements.txt`. Optional retrieval and MCP modules import after that correction, but their live data/service behavior remains unverified.

The checkout is exactly equal to `origin/main` at commit `30490de001a22822bec8b664c7e6e872045f7c68`, with no pre-existing working-tree changes. The requested `/home/t0n34781/projects/...` path and a fourth PNG referenced by the instructions were absent; therefore, those claims could not be compared directly.

## B. Environment

| Item | Observed evidence | Status |
|---|---|---|
| Kernel / architecture | `Linux 0a02c8e71ab6 6.18.38+ ... x86_64` | PASS |
| Distribution metadata | `lsb_release` command unavailable | UNVERIFIED; do not infer from screenshot |
| Python | `/usr/bin/python3`, Python 3.12.3 | PASS |
| pip | pip 24.0 system-wide | PASS |
| Git | git 2.43.0 | PASS |
| GitHub CLI | gh 2.97.0, GitHub connector disabled | UNVERIFIED for authenticated GitHub operations; public HTTPS clone succeeded |
| Test framework | pytest 9.1.1 in isolated venv | PASS |
| Node/npm | Node v22.13.0, npm 10.9.2 | PRESENT; not required for core |
| Browser | Chromium at `/usr/bin/chromium`; Chrome/Firefox not found | PRESENT, not required for core |
| Ollama | No executable; `localhost:11434` connection refused | FAIL — ENVIRONMENT |
| ChromaDB | Installed in clean-room venv; no `rag_db/` corpus present | PASS — PARTIAL |
| FastAPI/Uvicorn | Installed in clean-room venv | PASS — optional boundary |
| Playwright/Selenium | Playwright available system-side; Selenium unavailable | PRESENT / UNVERIFIED; not required for core |
| Docker/Podman/uv/Poetry/Conda | uv present; Docker, Podman, Poetry, Conda not found | Not required for core |

A recoverable snapshot was created before source modification at:

- [Snapshot archive](/home/ubuntu/audit_snapshots/badgr_harness_20260902T192856Z.tar.gz)
- [Snapshot metadata](/home/ubuntu/audit_snapshots/badgr_harness_20260902T192856Z.metadata.txt)

No credentials were printed or included in this report.

## C. Repository and Visual Evidence Audit

The repository clone was created in the writable sandbox because `/home/t0n34781/projects` was not writable or present. The clone has remote `origin` set to the public GitHub URL, branch `main`, and commit `30490de001a22822bec8b664c7e6e872045f7c68`. `git rev-list --left-right --count HEAD...origin/main` returned `0 0`; no local-vs-remote divergence exists. The original checkout was clean. After the minimal dependency correction, only `requirements.txt` is modified.

Three PNGs were available, not four:

| PNG | Directly observed context | Audit treatment |
|---|---|---|
| `01_hunter_browser.png` | Wide system overview showing BADGR Harness and Pro Hunter as two intended systems, with the Harness responsible for orchestration/router/validator and shared RAG/MCP hosting | Context only; authoritative local path was absent |
| `02_HW_ollama.png` | Screenshot context showing local Ollama models, model quick reference, shared infrastructure, and a hardware report | Context only; live Ollama was checked directly and was unreachable |
| `03_PIVOT.png` | Screenshot context showing skill profiles, job sites, scraping tiers, and a proposed Pro Hunter/web-scraping relationship | Context only; no Pro Hunter checkout was present |
| Fourth PNG | Not present in `/home/ubuntu/upload` | UNVERIFIED / unavailable |

The wide first image was inspected as three ordered overlapping horizontal crops. No screenshot claim was treated as proof of current runtime functionality.

## D. Dependency Audit

| Package | Declared before fix | Imported | Installed in clean venv | Required for core | Optional integration | Status |
|---|---:|---:|---:|---:|---:|---|
| pydantic | Yes | Yes | Yes | Yes | No | PASS |
| PyYAML | Yes | Yes | Yes | Yes | No | PASS |
| python-dotenv | Yes | Yes | Yes | Yes | No | PASS |
| pytest | Yes | Tests | Yes | Test-only | No | PASS |
| fastapi | Yes | Yes | Yes | No | API | PASS |
| uvicorn | Yes | Runtime | Yes | No | API | PASS |
| httpx | Yes | Tests/API ecosystem | Yes | No | API tests | PASS |
| chromadb | Yes | Yes | Yes | No | RAG | PASS — PARTIAL |
| pdfplumber | Yes | Yes | Yes | No | RAG ingest | PASS |
| requests | Yes | Yes | Yes | No | RAG/web | PASS |
| beautifulsoup4 | No | `RAG_corpus_crawl_sba.py` | Installed after fix | No | SBA scraper | FIXED; now declared |
| lxml | No | Required by scraper's `lxml-xml` parser mode | Installed after fix | No | SBA scraper | FIXED; now declared |
| `bs4` import | No separate package name | Yes, via BeautifulSoup | Yes after fix | No | SBA scraper | PASS after fix |

The repository's `setup_badgr_harness.sh` declares additional packages not represented in the public `requirements.txt` (`langgraph`, `langchain`, `litellm`, `jsonschema`, and `mcp`). Direct repository imports did not require all of those for the tested core path. The setup script is also destructive because it writes project files; it was not run.

## E. Component Test Matrix

| Component | Test | Result | Evidence | Failure | Next Action |
|---|---|---|---|---|---|
| Repository integrity | Clone, remote, branch, commit, divergence | PASS | Exact equality with `origin/main`; `0 0` divergence | Requested authoritative path absent | Use explicit writable checkout path or provide original checkout |
| Typed schemas | Import and repository tests | PASS | Core imports pass; included tests pass | None | None |
| Router | Generic, classification, extraction, domain-gated routing tests | PASS | Included routing tests pass | None observed | None |
| Validator | JSON parsing, confidence, task-specific fields, malformed output | PASS | Included validator tests pass | None observed | None |
| Orchestrator | Mocked success, retry, fallback, supervisor, clarification, failure paths | PASS | Included orchestration tests pass | Live model unavailable | Re-run live path with approved Ollama service |
| Event recording | Mocked showcase and state tests | PASS — MOCKED | Showcase persisted `task_started`, `primary_model_selected`, `primary_attempt_valid` | No live state write was used in showcase; state unit tests pass | Confirm with approved live run |
| API | Import and TestClient endpoint suite | PASS — MOCKED | API imports; API tests included in 83 passing tests | API process was not exposed or live-tested | Start locally only when live model is available |
| Local model boundary | Ollama endpoint and registry model availability | FAIL — ENVIRONMENT | `curl localhost:11434/api/tags` connection refused | No Ollama server/executable | Start approved local Ollama and verify registry models |
| RAG | Module imports and dependency availability | PASS — PARTIAL | `rag_ingest`, `rag_query` import; ChromaDB installed | No `rag_db/`; live embeddings unavailable | Provide corpus and embedding service for a separate test |
| MCP | `rag_mcp`, `web_ops_mcp` imports | PASS — PARTIAL | Both modules import | Service/tool behavior not exercised | Test stdio tools in a controlled local fixture |
| SBA scraper | Import after dependency fix | PASS — PARTIAL | Import succeeds after adding dependencies | Import has top-level outbound behavior; endpoint returned HTTP 404 and wrote an empty URL file during import check | Refactor execution behind an explicit entry point in a later phase; do not invoke as core |
| Pro Hunter | Expected companion project | UNVERIFIED | No `/home/t0n34781/projects/pro_hunter` or sandbox clone | Not available | Supply or separately audit the project |

## F. Actual Test Results

### Clean-room setup

```text
python3 -m venv .venv_manus_verify
. .venv_manus_verify/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The initial install succeeded. Before the fix, the optional scraper import failed with `ModuleNotFoundError: No module named 'bs4'`. After adding `beautifulsoup4` and `lxml`, those packages were installed into the isolated environment.

### Full test suite

```text
python -m pytest -q
```

Result after the fix:

```text
83 passed, 1 warning in 1.70s
exit status: 0
```

The warning was a `StarletteDeprecationWarning` from the installed FastAPI/Starlette test client integration, stating that the current `httpx` integration is deprecated and recommending `httpx2`. This warning did not fail the suite.

### Syntax and imports

```text
python -m compileall -q .
```

Result: `COMPILEALL_OK`, exit status 0.

Core imports (`config`, `router`, `validator`, `orchestrator`, schemas, and state manager) passed. API, RAG, and MCP module imports passed after the dependency correction. The SBA scraper import passed after the correction but performed top-level outbound work; its request returned HTTP 404 and produced zero harvested URLs. This was not treated as proof of scraper functionality.

### Deterministic showcase

A synthetic, non-sensitive classification goal was run with the model boundary mocked and RAG disabled. The returned structured result was valid and included labels `synthetic` and `classification`. Three events were persisted in order:

```text
task_started
primary_model_selected
primary_attempt_valid
```

This is **PASS — MOCKED**, not live-model proof.

## G. Failure Analysis

### Failure 1 — Missing optional scraper dependencies (resolved)

**Observed evidence:** `RAG_corpus_crawl_sba` failed to import with `ModuleNotFoundError: No module named 'bs4'` in the clean-room environment. The code also invokes BeautifulSoup with `lxml-xml`.

**Probable cause:** The public `requirements.txt` omitted both `beautifulsoup4` and `lxml`. **Confidence: high**, because the imports and parser mode are explicit.

**Fix #1 — applied:** Add `beautifulsoup4` and `lxml` to `requirements.txt`; install them in the isolated verification environment.

**Expected result:** The scraper module imports. **Observed:** import passed.

**Fix #2:** If the project chooses not to support the SBA scraper in the public dependency set, move it to a separately documented optional requirements file and classify it as unavailable by design.

**Fix #3:** Replace the parser implementation only if a later controlled test demonstrates a parser-specific incompatibility. No such redesign was justified in Part 1.

**Verification:** `python audit_imports.py` equivalent import check; scraper import passed after fix; full suite remained 83 passed.

**Rollback:** Remove the two added lines from `requirements.txt`; restore from the snapshot archive if needed.

### Failure 2 — Live Ollama unavailable (unresolved environment failure)

**Observed evidence:** No `ollama` executable was found and `curl --max-time 2 http://localhost:11434/api/tags` failed to connect.

**Probable cause:** Ollama is not installed or not running in this sandbox. **Confidence: high** for environment unavailability; the exact cause between installation and service state is unresolved.

**Fix #1:** Start the approved local Ollama service at `http://localhost:11434`, then verify `/api/tags` and each non-cloud registry model.

**Fix #2:** If the service uses another endpoint, set `OLLAMA_BASE_URL` in a preserved local `.env` and verify the configured protocol.

**Fix #3:** If a model is absent, pull only the owner-approved registry model and rerun the phase preflight. Do not substitute a cloud or paid model without explicit authorization.

**Verification:** `curl -fsS http://localhost:11434/api/tags`; then `python phase1_preflight.sh` only after its expected `.venv` and service prerequisites are deliberately configured.

**Rollback:** Stop the local service and restore any `.env` changes from its preserved original. No live-service changes were made in this audit.

### Failure 3 — Requested authoritative local checkout unavailable

**Observed evidence:** `/home/t0n34781/projects/badgr_harness` did not exist and `/home/t0n34781` was not writable. A public clone was therefore audited at `/home/ubuntu/projects/badgr_harness`.

**Probable cause:** The referenced workstation path is not mounted in this sandbox. **Confidence: high.**

**Fix #1:** Provide or mount the original checkout for a direct local-vs-remote comparison.

**Fix #2:** Continue using the exact public commit audited here, while clearly treating local configuration and ignored files as unverified.

**Fix #3:** Supply a sanitized export of any local-only configuration and corpus metadata for a separate review.

**Verification:** `test -d /home/t0n34781/projects/badgr_harness`; compare `git status`, commit, and file inventory.

**Rollback:** No user checkout was altered.

## H. Live vs Mocked

| Capability | Classification |
|---|---|
| Core module imports | LIVE in isolated clean-room environment |
| Schema validation and routing unit behavior | LIVE tests |
| Orchestrator recovery behavior | PASS — MOCKED model responses through repository tests |
| Deterministic showcase | PASS — MOCKED model and RAG boundary |
| Event file creation in showcase | LIVE filesystem behavior under mocked model boundary |
| API endpoint behavior | PASS — MOCKED via FastAPI TestClient and patched orchestrator |
| Ollama generation | FAILED / UNTESTED because service was unreachable |
| Configured registry models | UNVERIFIED live; no Ollama API |
| ChromaDB retrieval | PASS — PARTIAL imports/dependencies only; no corpus or live embedding |
| MCP tool execution | UNVERIFIED beyond imports |
| SBA outbound harvesting | BLOCKED for core; import side effect observed, operational behavior not approved |
| Pro Hunter integration | UNVERIFIED; project absent |

## I. Showcase Readiness

**READY AFTER FIXES.** A truthful local showcase can demonstrate the core flow with a clearly labeled mocked model boundary: synthetic goal, normalization, routing, structured response validation, success, and local event recording. It must not be presented as live LLM functionality.

A live showcase is **NOT READY** until Ollama is available, the configured model names are confirmed through `/api/tags`, and a safe synthetic request completes through the actual model boundary. RAG, MCP, scraping, and Pro Hunter integration are optional and unavailable for a core demonstration in this environment.

## J. Recommended Next Step

**Smallest technically justified next step:** provide or start the approved local Ollama service and verify the exact configured registry models against `/api/tags`. Then run one synthetic live request and compare its event lineage with the already verified mocked showcase. Do not begin the web-agent/orchestration redesign yet.

## Commands Executed

The audit used the following command classes: public HTTPS clone; Git remote/branch/commit/status/divergence inspection; environment and tool discovery; isolated virtual-environment creation; dependency installation; import checks; `compileall`; repository pytest; deterministic mocked showcase; and safe local endpoint checks. The destructive setup script was read but not executed.

**Part 1 stop condition reached.** No browser agent, architecture replacement, RAG replacement, Ollama replacement, paid API, cloud infrastructure, or orchestration redesign was introduced.
