# Architecture

## System boundary

The core system is a Python task-orchestration harness. It accepts a user goal, constructs a typed task, selects a model role, validates the returned structured output, and follows recovery paths when validation fails. Optional integration surfaces are documented separately from the core flow.

## Core data flow

1. A goal enters through the command-line or API-facing task path.
2. The orchestrator normalizes the goal into a typed task.
3. The router classifies the task and selects a configured model role.
4. The model boundary receives a prompt and returns text intended to represent structured output.
5. The validator parses and checks the response against task-specific requirements.
6. A valid result is returned; an invalid result can trigger retry, fallback, supervisor escalation, or clarification.
7. Execution events, reports, and runtime state use local filesystem boundaries.

## Confirmed components

| Component | Responsibility |
|---|---|
| Typed task schemas | Define task types, status, constraints, expected output, and confidence requirements. |
| Typed event schemas | Represent execution events, statuses, model/role fields, validation status, and details. |
| Router | Classifies goals, detects domain signals, and chooses configured model roles. |
| Orchestrator | Coordinates task normalization, optional retrieval context, model attempts, recovery paths, and result recording. |
| Validator | Parses structured responses and enforces task-specific output requirements. |
| Local model boundary | Sends generation and, where configured, embedding requests to a locally configured service. |
| Optional RAG boundary | Retrieves context from locally configured retrieval storage and an embedding boundary. |
| FastAPI boundary | Provides optional HTTP endpoints for task execution and inspection. |
| MCP boundary | Provides optional stdio tool-server interfaces for retrieval and web operations. |
| Logging/reporting boundary | Writes local event records and daily summaries. |
| State boundary | Persists runtime task statistics and related state locally. |

## Inputs and outputs

Inputs include user goals, task constraints, configuration, and optional locally available retrieval context. Outputs include structured task results, clarification responses, event records, reports, API responses, and runtime state.

## Model and tool boundaries

The core harness does not implement a model. It calls a configured local model service. Optional retrieval and MCP paths introduce additional boundaries and should not be assumed to be available in a clean clone. The repository also contains workflow definitions that are outside the core proof path and require separate review.

## Error and failure paths

When a model response fails validation, the orchestrator can retry the selected route. If the retry remains invalid, it can select a fallback route. Continued failure can lead to supervisor escalation, a clarification response, or a failed result. The validator is the boundary that determines whether a structured response is acceptable.

## Privacy and trust boundaries

Goals and model responses may cross the configured model boundary. Retrieval context may be read from local data. Events, reports, and state may contain task and execution details. Public documentation should use synthetic examples and must not include local paths, credentials, private corpus contents, raw logs, or machine-specific configuration.

## Public versus private scope

The intended public scope is the core routing, validation, structured-output, recovery-path, API, and test evidence. Local corpus material, live configuration, machine-specific MCP configuration, operational handoffs, raw runtime artifacts, and outbound automation workflows are excluded or require separate review.

## Unverified areas

Clean-clone execution, dependency completeness, live model availability, retrieval-data provenance, MCP configuration portability, and outbound workflow behavior require owner confirmation.
