#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${HOME}/projects/badgr_harness"

cd "$PROJECT_ROOT"
source .venv/bin/activate

echo "== Location =="
pwd

echo "== Python / venv =="
which python
python --version
python -m pip --version

echo "== Required packages =="
python - <<'PY'
import importlib
mods = [
    'pytest',
    'yaml',
    'pydantic',
    'dotenv',
    'jsonschema',
    'langgraph',
    'langchain',
    'litellm',
    'mcp',
]
missing = []
for mod in mods:
    try:
        importlib.import_module(mod)
        print(f'OK  {mod}')
    except Exception as exc:
        print(f'MISSING  {mod} -> {exc}')
        missing.append(mod)
if missing:
    raise SystemExit(1)
PY

echo "== Required project files =="
for f in \
  orchestrator.py \
  router.py \
  validator.py \
  config.py \
  models.yaml \
  prompts/worker_system.txt \
  prompts/fallback_system.txt \
  prompts/supervisor_system.txt \
  schemas/task_schema.py \
  schemas/log_schema.py \
  tests/conftest.py \
  tests/test_router.py \
  tests/test_orchestrator.py \
  tests/test_validator.py
do
  if [[ -f "$f" ]]; then
    echo "OK  $f"
  else
    echo "MISSING  $f"
    exit 1
  fi
done

echo "== Ollama API health =="
python - <<'PY'
import json
from urllib.request import urlopen
with urlopen('http://localhost:11434/api/tags', timeout=10) as resp:
    data = json.loads(resp.read().decode('utf-8'))
models = [m.get('model') for m in data.get('models', [])]
print('OLLAMA_OK')
print('MODELS_FROM_API=')
for model in models:
    print(f'  - {model}')
PY

echo "== Registry model check =="
python - <<'PY'
from pathlib import Path
import json
import yaml
from urllib.request import urlopen

registry = yaml.safe_load(Path('models.yaml').read_text(encoding='utf-8'))['models']
expected = [cfg['model_name'] for cfg in registry.values()]
with urlopen('http://localhost:11434/api/tags', timeout=10) as resp:
    api_models = {m.get('model') for m in json.loads(resp.read().decode('utf-8')).get('models', [])}
missing = [m for m in expected if ':cloud' not in m and m not in api_models]
print('EXPECTED_MODELS=')
for model in expected:
    print(f'  - {model}')
if missing:
    print('MISSING_LOCAL_MODELS=')
    for model in missing:
        print(f'  - {model}')
    raise SystemExit(1)
print('REGISTRY_MODELS_OK')
PY

echo "== Unit tests =="
python -m pytest -q

echo "== Harness smoke test =="
python orchestrator.py --goal "Classify this request and return strict JSON"

echo "== Phase 1 preflight passed =="


