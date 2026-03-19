# FlowDoctor

Turn hard-to-run repos into AI-ready workspaces.

## What it does

FlowDoctor is an experimental Python CLI for preparing local repositories for AI-assisted debugging.

Current implemented commands:
- `flowdoctor scan [PATH]`
- `flowdoctor diagnose LOG_FILE`
- `flowdoctor env draft [PATH]`

Current generated outputs:
- `repo_profile.json`
- `failure_bundle.json`
- `.devcontainer/devcontainer.json`

## Why it exists

Many local repos are hard to run consistently: environments drift, logs are noisy, and critical setup/debugging context is scattered. AI tools also work better with structured, bounded context than raw repository dumps.

FlowDoctor focuses on practical first steps: detect basic repo shape, structure failure evidence, and draft a minimal devcontainer config.

## Current features

- `scan [PATH]`
  - Scans a target repo directory.
  - Infers `repo_type` using marker files (ordered rules below).
  - Prints pretty JSON to stdout.
  - Writes `repo_profile.json` into the target repo directory.
- `diagnose LOG_FILE`
  - Reads a log file as UTF-8.
  - Extracts a minimal structured failure bundle.
  - Prints pretty JSON to stdout.
  - Writes `failure_bundle.json` in the current working directory.
- `env draft [PATH]`
  - Generates a minimal devcontainer config.
  - Prints pretty JSON to stdout.
  - Writes `<target repo>/.devcontainer/devcontainer.json`.

Repo type inference rules used by `scan` (in order):
1. `pyproject.toml` -> `python`
2. `requirements.txt` -> `python`
3. `package.json` -> `node`
4. `Cargo.toml` -> `rust`
5. `go.mod` -> `go`
6. `CMakeLists.txt` -> `cpp`
7. `Makefile` -> `generic-make`
8. otherwise -> `unknown`

Current `env draft` Python-oriented output uses:
- image: `mcr.microsoft.com/devcontainers/python:1-3.12-bullseye`
- VS Code extensions including Python and Ruff
- `postCreateCommand: "uv sync"`

## Quick start

Assuming you are in this repo and already have `uv` installed:

```bash
uv sync
uv run flowdoctor --help
uv run flowdoctor scan .
```

## Installation

Current requirements:
- Python 3.12
- `uv`

This project is currently used from source in this repository.

```bash
uv sync
```

## Usage

Scan a repository and write `repo_profile.json` into that repository:

```bash
uv run flowdoctor scan .
```

Diagnose a log file and write `failure_bundle.json` into the current directory:

```bash
uv run flowdoctor diagnose sample.log
```

Draft a devcontainer config and write `.devcontainer/devcontainer.json` into the target repository:

```bash
uv run flowdoctor env draft .
```

## Repository structure

- `src/flowdoctor/__init__.py`: Typer CLI app and command implementations.
- `tests/`: pytest command tests (`scan`, `diagnose`, `env draft`).
- `pyproject.toml`: project metadata and CLI entrypoint.

## Who this is for

- Developers working on hard-to-run local repositories.
- Systems / infra / compiler / EDA / simulation / AI infra users.
- Teams that want cleaner, structured debugging inputs for AI tools.

## Current status

FlowDoctor is experimental, early alpha, and not production-ready.

- Interfaces may change.
- Current local test status: `7 passed`.

## Roadmap

Future work (not implemented yet):
- Richer repository detection.
- Better environment drafting.
- Better failure analysis.
- Possible future MCP integration.

## Contributing

Contributions are welcome. Open an issue or pull request with a focused proposal.

## License

See [LICENSE](LICENSE).
