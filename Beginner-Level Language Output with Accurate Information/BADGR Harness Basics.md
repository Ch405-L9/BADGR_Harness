# BADGR Harness Basics

This document describes the small, functional baseline for beginner-friendly answers. The harness now uses plain-language instructions for every local-model role, sends generic factual questions to the live evidence path when they are written as questions, and keeps BADGR-specific questions on the local knowledge-base path. It still fails closed when live search has no configured provider; this is safer than presenting an unsupported answer as certain.

## Install and run locally

Use an isolated virtual environment for this repository. It prevents BADGR dependencies from changing the system Python or another project.

```bash
cd ~/projects/badgr_harness
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp -n .env.example .env
```

Set one live-search provider in `.env` before factual-question tests. The provider keys are private and must not be committed.

```bash
SEARCH_PROVIDER=brave
BRAVE_SEARCH_API_KEY=replace_with_your_key
```

## Three beginner tests

These are deliberately small smoke tests. They check routing and output contracts; they do not pretend that a unit test alone can prove every fact in the world.

| Area | Test goal |
|---|---|
| Math | `What is 12 times 8?` |
| Writing | `What is a clear topic sentence?` |
| Technology | `Can a browser read a JSON file?` |

Run the deterministic test suite with:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q
```

Run each live test after `.env` is configured:

```bash
python orchestrator.py --goal "What is 12 times 8? Give a beginner explanation and cite one reliable source."
python orchestrator.py --goal "What is a clear topic sentence? Give a beginner explanation and cite one reliable source."
python orchestrator.py --goal "Can a browser read a JSON file? Give a beginner explanation and cite one reliable source."
```

For the audit record, add `--debug`. Normal output is for a beginner; debug output includes provider, query, snippets, and source metadata.

```bash
python orchestrator.py --goal "Can a browser read a JSON file? Give a beginner explanation and cite one reliable source." --debug
```

## Make the long command short and global

The repository includes `bin/badgr`, a safe wrapper that finds its own repository directory, loads `.env`, uses `.venv` when present, and runs the harness.

```bash
cd ~/projects/badgr_harness
chmod +x bin/badgr
mkdir -p ~/.local/bin
ln -sf "$PWD/bin/badgr" ~/.local/bin/badgr
export PATH="$HOME/.local/bin:$PATH"
badgr "What is a clear topic sentence? Give a beginner explanation and cite one reliable source."
```

To keep the PATH change after a new shell, add this once to `~/.bashrc`:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Globalize through a shell function instead

If a symlink is not wanted, use a shell function. This is useful when the repository moves between machines.

```bash
badgr() {
  local repo="$HOME/projects/badgr_harness"
  cd "$repo" || return 1
  set -a
  [ -f .env ] && . ./.env
  set +a
  if [ -x .venv/bin/python ]; then
    .venv/bin/python orchestrator.py --goal "$*"
  else
    python3 orchestrator.py --goal "$*"
  fi
}
```

Put the function in `~/.bashrc`, then run `source ~/.bashrc`.

## Accuracy boundary

A high accuracy target is a validation goal, not a guarantee. The functional safeguards are evidence-first routing, source provenance, confidence validation for local-model JSON, beginner-language prompts, retry/fallback/supervisor recovery, and fail-closed behavior when evidence is unavailable. Search snippets are not the same as page-level proof. For high-stakes topics, read the cited source and request debug output before acting.

The current baseline does not independently prove every retrieved claim, calculate calibrated confidence from a labeled benchmark, or guarantee that a source page has not changed. Those are later improvements, not part of this basics-only completion.
