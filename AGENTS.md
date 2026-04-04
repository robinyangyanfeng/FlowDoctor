# AGENTS.md

## FlowDoctor Mission
- First-principles goal: **help users understand failures faster**.
- FlowDoctor is an **early-alpha, local-first CLI** that produces concrete debugging artifacts.
- Prioritize evidence capture and clarity over automation; this project is not trying to auto-fix everything.

## Product Reality (Keep This True)
- Treat artifact outputs as core contract:
  - `scan` -> `repo_profile.json`
  - `diagnose` -> `failure_bundle.json`
  - `env draft` -> `.devcontainer/devcontainer.json`
- Keep behavior local-first: operate on local paths/logs and avoid introducing remote-service assumptions.

## Coding Rules
- Make the **smallest practical diff** for the requested change.
- Keep Python code **typed** (type hints on new/changed function boundaries; keep models explicit).
- Avoid unnecessary dependencies; prefer stdlib and existing packages (`typer`, `pydantic`, `rich`) unless a new dependency is clearly justified.
- Preserve CLI stability where possible; if changing behavior, make the change explicit and test-backed.

## Testing Rules
- After code changes, run: `uv run pytest`.
- Any behavior change must include or update tests (especially CLI/output behavior under `tests/`).
- Do not ship schema-affecting changes without tests that assert the new behavior.

## Documentation Rules
- If CLI output schema changes (JSON fields, value semantics, output file paths/names, or command output contract), update `README.md` in the same change.
- Keep README examples and artifact descriptions aligned with actual CLI behavior.
