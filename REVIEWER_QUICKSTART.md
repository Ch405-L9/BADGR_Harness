# Reviewer Quickstart

## Purpose

This is a safe inspection path for the public-preparation branch. It is designed to help a reviewer understand the core design without claiming that the complete workflow runs from a clean clone.

## Prerequisites

A reviewer needs access to the repository and a Git client. No live model service, retrieval database, workflow runner, external API, or paid service is required for the inspection path.

## Five-to-ten-minute route

1. Read [README.md](README.md) for the project scope and limitations.
2. Read [ARCHITECTURE.md](ARCHITECTURE.md) for the core data flow and trust boundaries.
3. Inspect `router.py` and the routing tests to see the generic-versus-specialist boundary.
4. Inspect `validator.py` and validation tests to see structured-output checks.
5. Inspect `orchestrator.py` and its mocked-path tests to see retry, fallback, supervisor, and clarification behavior.
6. Inspect `api.py` and its tests for the optional HTTP boundary.
7. Review Git history for the domain-gated routing correction.
8. Read [PUBLIC_SCOPE.md](PUBLIC_SCOPE.md) before evaluating optional integrations.

## Commands for inspection

The following commands are read-only examples for a reviewer to inspect repository content:

```bash
git status --short --branch
git log --oneline -n 20
git ls-files
sed -n '1,240p' README.md
sed -n '1,260p' ARCHITECTURE.md
sed -n '1,240p' router.py
sed -n '1,260p' validator.py
```

## Tests and demo status

The repository contains tests, including mocked orchestration paths, but this branch does not claim that tests have been rerun here. An owner must confirm the supported dependency setup and run the approved test command before publishing test results or totals.

A dependency-free deterministic demo is not claimed by this branch. If one is approved later, it should use synthetic goals and mocked model/tool boundaries and must preserve the core routing and validation behavior.

## Live and optional paths

Live model, retrieval, MCP, n8n, and other local-service workflows may require local configuration. Do not invoke those paths as part of this inspection route. Do not assume that their configuration, data, or outbound behavior is suitable for public use.

## Owner confirmation required

Before public release, the owner should confirm: the supported runtime and dependency setup; the approved test command and actual result; the status of the optional integrations; the provenance and publication status of retrieval data; and the safe handling of any local configuration.

## Troubleshooting

If a file is absent, a command requires an unapproved service, or a documented claim cannot be reproduced from the repository, stop the review at that point and treat the item as **owner confirmation required** rather than substituting a guessed result.
