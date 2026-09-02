# BADGR Harness

Python orchestration and evaluation harness for typed AI workflows, model-role routing, structured-output validation, and controlled failure recovery.

## Project summary

BADGR Harness is a Python-based orchestration harness that converts a user goal into a typed task, routes the task to an appropriate configured model role, validates the structured response, and records the execution outcome.

The project was built to make model-driven workflows more predictable and inspectable. Its core focus is preventing incorrect routing, validating outputs against task-specific requirements, and handling invalid or incomplete responses through retry, fallback, supervisor escalation, or clarification behavior.

Optional integration paths in the repository include retrieval, a FastAPI interface, MCP tools, local model services, and workflow automation. Those integrations have separate configuration and data requirements.

## Engineering evidence

The repository includes source code and tests covering:

- Canonical typed task and event schemas
- Model registry-based routing
- Generic versus domain-specific routing boundaries
- Structured-output validation and task-specific checks
- Retry, fallback, supervisor escalation, and clarification paths
- Local state and event recording
- FastAPI endpoint behavior
- Optional retrieval and MCP integration surfaces

Git history includes a focused domain-gated routing correction. The correction protects generic classification and extraction tasks from being routed to a domain-specialist path without appropriate domain signals.

## Failure, correction, and verification

### Failure or risk

Generic work could be incorrectly selected for a domain-specialist route, creating a mismatch between task intent and model role.

### Correction

The routing logic introduced a domain-specific gate around specialist selection so that generic classification and extraction work remain on an appropriate general route unless domain signals are present.

### Verification

The repository includes routing tests that distinguish generic work from domain-specific work, along with tests for orchestration paths, output validation, state management, retrieval behavior, and API behavior.

Historical reports may contain additional execution counts or phase evidence. Those claims should be treated as separately reviewable evidence unless independently reproduced.

## Core capabilities

- Normalize user goals into typed tasks.
- Classify task goals and select configured model roles.
- Gate specialist routing on domain-specific signals.
- Validate structured worker output, including confidence and task-specific fields.
- Retry invalid output, then use fallback and supervisor paths.
- Return a clarification question when the supervisor cannot proceed confidently.
- Record task events, reports, and runtime state through local filesystem boundaries.
- Expose optional API, retrieval, and MCP integration surfaces.

## Architecture

The core flow is:

`goal → task schema → router → orchestrator → model boundary → validator → result or recovery path`

The repository also includes optional retrieval, FastAPI, MCP, workflow automation, logging/reporting, and state components. See [ARCHITECTURE.md](ARCHITECTURE.md) for the confirmed boundaries and limitations.

## Technology stack

The repository contains Python code using Pydantic, PyYAML, python-dotenv, FastAPI, Pytest, ChromaDB, PDF text extraction, HTTP clients, and stdio MCP server implementations. Exact dependency completeness and clean-clone execution remain owner confirmation items.

## Repository scope

The public-preparation scope centers on routing, validation, structured outputs, retry/fallback/escalation behavior, API code, and their tests. Corpus material, live model configuration, machine-specific MCP configuration, operational handoffs, raw runtime artifacts, and outbound workflow automation require separate review.

## Local setup and review path

This branch is a documentation and publication-preparation branch. It does not claim that the complete workflow runs from a clean clone. Live model, retrieval, MCP, workflow automation, and other local-service workflows may require local configuration and are not represented here as a verified clean-clone public demo.

Use [REVIEWER_QUICKSTART.md](REVIEWER_QUICKSTART.md) for the safe inspection path and the commands that remain for owner confirmation. Do not treat the operational files as a ready-to-run public setup until their dependencies, data boundaries, and configuration have been reviewed.

## Known limitations

The main execution path depends on configured local model services. Retrieval paths depend on local retrieval data and an embedding boundary. Optional API, MCP, and workflow automation paths have their own configuration and data requirements. This branch does not claim production readiness, security guarantees, scalability, or deterministic end-to-end behavior.

## What remains private or separately reviewed

Local corpus material, live model configuration, machine-specific MCP configuration, operational handoffs, raw logs, runtime state, and outbound automation workflows are excluded from the core public scope or require separate owner review. See [PUBLIC_SCOPE.md](PUBLIC_SCOPE.md).

## Public-state cleanup

The public branch keeps the canonical schema modules in [schemas/task_schema.py](schemas/task_schema.py) and [schemas/log_schema.py](schemas/log_schema.py). Legacy compatibility imports remain available through a minimal shim only where needed; duplicate implementation files are not kept as independent public definitions.

This avoids import drift and keeps the public code path consistent with the canonical task and event model definitions.

## License

License and third-party-content status require owner confirmation before public release.
