# Public Scope

This branch is a public technical portfolio preparation branch. It is intended to make the repository easier to review while preserving the distinction between confirmed core behavior and optional or private operational material.

## Core public scope

The intended public scope is:

- Task routing and domain-gated specialist selection.
- Typed task and event schemas.
- Structured-output validation.
- Retry, fallback, supervisor escalation, and clarification paths.
- API code and test evidence.

These areas should be documented using only behavior supported by the repository and owner-verified evidence.

## Excluded or separately reviewed scope

The following are excluded from the core public review path or require separate owner review:

- Local corpus material and retrieval data.
- Live model configuration and model availability.
- Machine-specific MCP configuration.
- Operational handoff files.
- Raw logs and runtime state.
- Outbound automation workflows.
- External-service and local-service configuration.

A reviewer should not infer that an optional integration is portable, reproducible, or safe to activate from the existence of its source files alone.

## Publication rules

Public documentation should use synthetic examples where examples are needed. It should not expose credentials, local paths, machine identities, private prompts, private data, raw logs, or unverified claims. Publication status for dependencies, licenses, retrieval sources, and optional integrations requires owner confirmation.
