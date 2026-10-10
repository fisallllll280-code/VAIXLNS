# VAIXLNS VX/XV CLI Alpha — Quickstart

## Scope

The current reference package turns a natural-language request into an inspectable task plan and can save a local continuity checkpoint. It does not call an LLM, modify a repository, run arbitrary commands, or connect external services.

## Install from a checkout

From the repository root, using Python 3.12:

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

python -m pip install -e ".[test]"
python -m pytest -q tests/test_vx_xv_cognitive_runtime.py
```

## Create a plan

```bash
vaixlns-plan "Explain this repository, identify missing tests, and propose a safe repair plan"
```

The CLI prints the plan and saves a local SQLite event checkpoint by default. To print without saving:

```bash
vaixlns-plan --no-store "Build a repository status dashboard"
```

Set a different local memory path with `--memory PATH` or the `VAIXLNS_XV_MEMORY` environment variable.

## Important limitations

- The current planner uses deterministic keyword-based intent classification; it is not yet an LLM-backed natural-language understanding system.
- Saved SQLite data is local, not encrypted, and not automatically backed up.
- A task plan is not an execution record. No patch is applied by this CLI.
- Do not store passwords, API keys, private keys, or financial credentials in the memory database.
- Public release remains blocked until tests, packaging, security, privacy, and end-to-end behavior are independently checked.
