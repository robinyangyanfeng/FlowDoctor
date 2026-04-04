# FlowDoctor

Help users understand failures faster through structured failure evidence.

## What FlowDoctor means

FlowDoctor is a local-first CLI for failure analysis. Its primary job is to turn noisy logs into a structured `failure_bundle.json` that is easier to inspect, compare, and hand off.

`scan` and `env draft` are supporting capabilities. They add project context and a minimal environment draft, but they are not the core value of the project.

FlowDoctor is a preparation layer, not a full automation layer. It helps teams move from raw failure output to clear, testable hypotheses.

## Why this project exists

Many repositories fail before useful debugging even starts. Environment setup drifts, dependency assumptions are unclear, entry points are hard to locate, and logs are noisy.

That hurts real work: people spend time reconstructing context, and AI tools receive unstructured input. FlowDoctor exists to structure the problem first so debugging can start from evidence instead of guesswork.

## What it does today

- Primary: `flowdoctor diagnose LOG_FILE` reads a log file and writes `failure_bundle.json` in the current working directory.
- Supporting: `flowdoctor diagnose LOG_FILE --repo PATH` enriches the failure bundle with repository context (`repo_context`) for clearer debugging handoff.
- Supporting: `flowdoctor scan [PATH]` writes `repo_profile.json` in the target repository.
- Supporting: `flowdoctor env draft [PATH]` writes a minimal `.devcontainer/devcontainer.json` draft in the target repository.

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

- `failure_bundle.json`: the primary artifact; converts raw log noise into structured failure evidence with classification and next verification steps.
- `repo_profile.json`: supporting context that helps identify repository shape and likely toolchain.
- `.devcontainer/devcontainer.json`: a supporting draft for local setup; not a guarantee of full environment reproduction.

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

Generate a failure bundle with repository context:

```bash
uv run flowdoctor diagnose sample.log --repo .
```

Current `failure_bundle.json` schema includes:
- `schema_version`
- `log_path`
- `exists`
- `line_count`
- `failure_stage`
- `failure_kind`
- `confidence`
- `primary_evidence`
- `supporting_evidence`
- `suspected_root_cause`
- `next_verification_steps`
- `repo_context` (null when `--repo` is not provided; object with `repo_path`, `repo_type`, `has_git`, `has_pyproject` when provided)

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

Any MCP-facing integration is future-facing only and not implemented in the current CLI.

## Roadmap

Priority-ordered roadmap (future work, not implemented yet):

1. Improve failure analysis quality (better heuristics, cleaner evidence selection, and clearer root-cause hypotheses).
2. Strengthen failure handoff context (better linkage between logs and repository metadata).
3. Improve env draft usefulness as a starting point without claiming full reproducibility.
4. Add MCP-facing integration as an export/integration layer after local CLI workflows are stronger.

## Contributing

Contributions are welcome. Open an issue or pull request with a focused, practical proposal.

## License

See [LICENSE](LICENSE).
