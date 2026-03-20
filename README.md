# FlowDoctor

Turn hard-to-run repos into AI-ready workspaces.

## What FlowDoctor means

FlowDoctor is a local-first CLI that prepares hard-to-run repositories for debugging and future AI-assisted workflows by producing three concrete artifacts: a repo profile, a failure bundle, and a minimal devcontainer draft.

It is a preparation layer, not a full automation layer. The goal is to make messy local state easier to understand, reproduce, and hand off.

## Why this project exists

Many repositories fail before useful debugging even starts. Environment setup drifts, dependency assumptions are unclear, entry points are hard to locate, and logs are noisy.

That hurts real work: people spend time reconstructing context, and AI tools receive unstructured input. FlowDoctor exists to structure the problem first so debugging can start from evidence instead of guesswork.

## What it does today

- `flowdoctor scan [PATH]`: reads a target repository directory; outputs JSON to stdout and `repo_profile.json` inside the target repository; useful for creating a quick structured project profile for tooling and handoff.
- `flowdoctor diagnose LOG_FILE`: reads a log file; outputs JSON to stdout and `failure_bundle.json` in the current working directory; useful for turning noisy failures into structured debugging evidence.
- `flowdoctor env draft [PATH]`: reads a target repository directory; outputs JSON to stdout and `<target repo>/.devcontainer/devcontainer.json`; useful for creating a minimal reproducible environment starting point.

Current `scan` repo type inference rules (in order):

1. `pyproject.toml` -> `python`
2. `requirements.txt` -> `python`
3. `package.json` -> `node`
4. `Cargo.toml` -> `rust`
5. `go.mod` -> `go`
6. `CMakeLists.txt` -> `cpp`
7. `Makefile` -> `generic-make`
8. otherwise -> `unknown`

## Why these outputs matter

- `repo_profile.json`: helps quickly identify what kind of project you are looking at and provides a stable, machine-readable snapshot of repo basics.
- `failure_bundle.json`: converts raw log noise into structured failure evidence that is easier to inspect, compare, and pass to another person or tool.
- `.devcontainer/devcontainer.json`: provides a concrete starting point for a reproducible local environment instead of starting from a blank file.

In practice, these artifacts make debugging handoffs cleaner and reduce repeated setup work.

## Quick start

Assuming you are already in this repository and already have `uv` installed:

```bash
uv sync
uv run flowdoctor --help
uv run flowdoctor scan .
```

## Installation

FlowDoctor currently runs from source in this repository.

Requirements:
- Python 3.12
- `uv`

Install dependencies:

```bash
uv sync
```

## Usage

Generate a repo profile:

```bash
uv run flowdoctor scan .
```

Creates `./repo_profile.json` in the target repo.

Generate a failure bundle from a log:

```bash
uv run flowdoctor diagnose sample.log
```

Creates `./failure_bundle.json` in the current working directory.

Draft a minimal devcontainer file:

```bash
uv run flowdoctor env draft .
```

Creates `./.devcontainer/devcontainer.json` in the target repo.

## Who this is for

- Developers dealing with hard-to-run local repositories.
- Systems, infrastructure, compiler, EDA, simulation, and AI-infra users who need faster debugging setup.
- Maintainers who want better structured artifacts for debugging handoff.

## Current status

FlowDoctor is experimental and early alpha.

- Not production-ready.
- Interface and output details may change.
- Not all repo types or environments are handled yet.
- `pytest` passes locally today.

## What FlowDoctor is not

FlowDoctor is not:

- a full bug-fixing agent
- a complete environment manager
- an MCP implementation today
- a hosted remote service

It does not replace coding agents, and it does not automatically reproduce every complex environment.

## Roadmap

Future work (not implemented yet):

- richer repo detection
- better environment drafting
- better failure analysis
- future MCP-facing integration

## Contributing

Contributions are welcome. Open an issue or pull request with a focused, practical proposal.

## License

See [LICENSE](LICENSE).
