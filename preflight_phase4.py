"""
Phase 4 preflight: verify Ollama connectivity and model alignment.

Run this on your machine before any live harness tests:
    python preflight_phase4.py

Exit 0 = all checks passed.
Exit 1 = one or more checks failed (details printed).
"""

from __future__ import annotations

import json
import sys
from urllib import error, request

import yaml

OLLAMA_BASE_URL = "http://localhost:11434"
MODELS_FILE = "models.yaml"


def _check_ollama_alive() -> list[str]:
    """Return list of installed model tags from Ollama, or raise."""
    req = request.Request(
        url=f"{OLLAMA_BASE_URL}/api/tags",
        method="GET",
    )
    with request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return [m["name"] for m in data.get("models", [])]


def _load_registry() -> dict:
    with open(MODELS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f).get("models", {})


def main() -> int:
    failures: list[str] = []

    print("=== BADGR Phase 4 Preflight ===\n")

    # 1. Ollama connectivity
    print("[1] Checking Ollama connectivity ...")
    try:
        installed = _check_ollama_alive()
        print(f"    OK — Ollama is live. {len(installed)} model(s) installed.")
    except error.URLError as exc:
        print(f"    FAIL — Cannot reach Ollama at {OLLAMA_BASE_URL}: {exc}")
        failures.append("Ollama not reachable")
        installed = []
    except Exception as exc:  # noqa: BLE001
        print(f"    FAIL — Unexpected error: {exc}")
        failures.append(f"Ollama check error: {exc}")
        installed = []

    # 2. Model registry alignment
    print("\n[2] Checking models.yaml alignment ...")
    try:
        registry = _load_registry()
    except Exception as exc:  # noqa: BLE001
        print(f"    FAIL — Could not load models.yaml: {exc}")
        failures.append(f"models.yaml load error: {exc}")
        registry = {}

    for key, config in registry.items():
        model_name = config.get("model_name") or config.get("modelname", "")
        if not model_name:
            print(f"    WARN  [{key}] no model_name field")
            continue
        if installed:
            # exact or prefix match (ollama tags can be name:tag or name)
            matched = any(m == model_name or m.startswith(model_name.split(":")[0] + ":") for m in installed)
            if matched:
                print(f"    OK    [{key}] {model_name}")
            else:
                print(f"    FAIL  [{key}] {model_name}  <-- NOT FOUND in ollama list")
                failures.append(f"Model not installed: {model_name}")
        else:
            print(f"    SKIP  [{key}] {model_name}  (Ollama unreachable)")

    # 3. Required lanes present
    # "supervisor" needs a model with role supervisor.
    # "worker" lane needs a model covering at least one of: code, classification, extraction, general.
    # "fallback" needs a model with role fallback.
    print("\n[3] Checking required routing lanes ...")
    worker_roles = {"code", "classification", "extraction", "general"}
    covered: set[str] = set()
    for key, config in registry.items():
        for role in config.get("roles", []):
            covered.add(role)

    def _check_lane(lane: str, match_any: set[str]) -> bool:
        return bool(covered & match_any)

    lanes = [
        ("supervisor", {"supervisor"}),
        ("worker (code/classify/extract/general)", worker_roles),
        ("fallback", {"fallback"}),
    ]
    for lane_name, match_set in lanes:
        if _check_lane(lane_name, match_set):
            print(f"    OK    lane '{lane_name}' covered")
        else:
            print(f"    FAIL  lane '{lane_name}' has no model assigned")
            failures.append(f"No model covers lane: {lane_name}")

    # 4. Unregistered models — show what's installed but not in the registry
    if installed:
        registered_names = {
            config.get("model_name") or config.get("modelname", "")
            for config in registry.values()
        }
        unregistered = [m for m in installed if m not in registered_names]
        if unregistered:
            print(f"\n[4] Unregistered models ({len(unregistered)} installed but not in models.yaml):")
            for m in sorted(unregistered):
                print(f"    --    {m}")
            print("    These models are available to add to models.yaml for use in the harness.")

    # Result
    print()
    if failures:
        print(f"PREFLIGHT FAILED — {len(failures)} issue(s):")
        for f in failures:
            print(f"  - {f}")
        print("\nFix the issues above before running live harness tests.")
        return 1

    print("PREFLIGHT PASSED — harness is ready for live Phase 4 tests.\n")
    print("Next:")
    print('  python orchestrator.py --goal "Classify this request and return strict JSON"')
    print('  python orchestrator.py --goal "Fix this Python bug and return strict JSON"')
    print('  python orchestrator.py --goal "Plan a local harness architecture"')
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
