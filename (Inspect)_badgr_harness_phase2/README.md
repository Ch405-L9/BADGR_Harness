# BADGR Harness Phase 2

A strict local LLM harness starter with routing, validation, fallback, escalation, JSONL logs, and daily report output.

## What this package includes

- `models.yaml` model registry with role metadata, timeout, and fallback chains
- `config.py` path and environment configuration
- `router.py` task classification and model selection
- `validator.py` strict worker-output validation
- `orchestrator.py` retry, fallback, escalation, logging, and reporting loop
- `schemas/` typed task and log models
- `prompts/` worker, fallback, and supervisor system prompts
- `tests/` pytest coverage for router, validator, and orchestrator flow

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python orchestrator.py --goal "Classify this request and return strict JSON"
```

## Notes

- The harness targets Ollama over HTTP by default.
- Prompt filenames are supported in both old and new forms for backward compatibility.
- Schema field names support both snake_case and compact legacy forms.
