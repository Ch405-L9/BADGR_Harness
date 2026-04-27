# BADGR Harness

Strict local LLM harness starter with routing, validation, fallback, and logs.

## What this builds first
- A model registry (`models.yaml`)
- Typed schemas for tasks and logs (`schemas/`)
- A rule-based router (`router.py`)
- A validator for worker JSON output (`validator.py`)
- A simple orchestrator loop for retry, fallback, escalation, logging, and reports (`orchestrator.py`)

## Live workflow
1. User makes request.
2. Harness converts it into a structured task object.
3. Router classifies the task.
4. Router picks the cheapest capable model.
5. Worker model runs.
6. Validator checks the output against schema.
7. If valid, return result and log success.
8. If invalid, retry once.
9. If still invalid, send to fallback model.
10. If fallback fails, escalate to supervisor model.
11. If supervisor still lacks clarity, ask the human a short question.
12. Write all steps to log.
13. Add summary to daily report.

## Starter models
- Supervisor: `qwen2.5:14b`
- Code worker: `qwen2.5-coder:7b`
- General fallback: `mistral:7b`
- Optional emergency cloud fallback: `kimi-k2.5:cloud`

## Setup
```bash
source .venv/bin/activate
python -m pytest -q
python orchestrator.py --goal "Classify this request and return strict JSON"
```
