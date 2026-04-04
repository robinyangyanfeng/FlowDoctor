import json
from pathlib import Path

import typer
from pydantic import BaseModel

app = typer.Typer(no_args_is_help=True)
env_app = typer.Typer(no_args_is_help=True)
app.add_typer(env_app, name="env")


class RepoProfile(BaseModel):
    path: str
    repo_type: str = "unknown"
    has_git: bool = False
    has_pyproject: bool = False


class RepoContext(BaseModel):
    repo_path: str
    repo_type: str = "unknown"
    has_git: bool = False
    has_pyproject: bool = False


class FailureBundle(BaseModel):
    schema_version: str = "2.0"
    log_path: str
    exists: bool
    line_count: int
    failure_stage: str
    failure_kind: str
    confidence: float
    primary_evidence: list[str]
    supporting_evidence: list[str]
    suspected_root_cause: str
    next_verification_steps: list[str]
    repo_context: RepoContext | None = None


@app.callback()
def callback() -> None:
    """FlowDoctor CLI."""
    pass


def infer_repo_type(repo: Path) -> str:
    if (repo / "pyproject.toml").exists():
        return "python"
    if (repo / "requirements.txt").exists():
        return "python"
    if (repo / "package.json").exists():
        return "node"
    if (repo / "Cargo.toml").exists():
        return "rust"
    if (repo / "go.mod").exists():
        return "go"
    if (repo / "CMakeLists.txt").exists():
        return "cpp"
    if (repo / "Makefile").exists():
        return "generic-make"
    return "unknown"


def build_repo_profile(repo: Path) -> RepoProfile:
    return RepoProfile(
        path=str(repo),
        repo_type=infer_repo_type(repo),
        has_git=(repo / ".git").exists(),
        has_pyproject=(repo / "pyproject.toml").exists(),
    )


def build_repo_context(repo: Path) -> RepoContext:
    profile = build_repo_profile(repo)
    return RepoContext(
        repo_path=profile.path,
        repo_type=profile.repo_type,
        has_git=profile.has_git,
        has_pyproject=profile.has_pyproject,
    )


def read_log(log_path: Path) -> list[str]:
    """Read a log file from disk and split it into lines."""
    text = log_path.read_text(encoding="utf-8")
    return text.splitlines()


def extract_evidence(lines: list[str], limit: int = 12) -> tuple[list[str], list[str]]:
    """Extract likely failure evidence lines from a log."""
    keywords = (
        "error",
        "exception",
        "failed",
        "traceback",
        "fatal",
        "notfound",
        "permission denied",
        "no such file",
        "assertionerror",
    )

    evidence_lines = [line.strip() for line in lines if any(key in line.lower() for key in keywords)]
    if not evidence_lines and lines:
        evidence_lines = [lines[-1].strip()]

    clipped = evidence_lines[:limit]
    primary = clipped[:3]
    supporting = clipped[3:]
    return primary, supporting


def detect_failure_stage(lines: list[str]) -> str:
    """Detect the lifecycle stage where the failure likely happened."""
    haystack = "\n".join(lines).lower()

    test_markers = ("pytest", "test session starts", "=== failures ===", "assertionerror")
    build_markers = ("build failed", "compilation", "linker", "cmake", "make[", "cargo build")
    env_markers = (
        "modulenotfounderror",
        "no module named",
        "command not found",
        "could not find a version",
        "dependency",
    )
    runtime_markers = ("traceback", "exception", "fatal", "panic", "segmentation fault")

    if any(marker in haystack for marker in test_markers):
        return "test"
    if any(marker in haystack for marker in build_markers):
        return "build"
    if any(marker in haystack for marker in env_markers):
        return "environment_setup"
    if any(marker in haystack for marker in runtime_markers):
        return "runtime"
    return "unknown"


def classify_failure_kind(primary_evidence: list[str], supporting_evidence: list[str]) -> tuple[str, str, float]:
    """Classify failure kind and provide a root-cause hypothesis."""
    evidence_text = "\n".join(primary_evidence + supporting_evidence).lower()

    if "modulenotfounderror" in evidence_text or "no module named" in evidence_text:
        return "missing_dependency", "missing Python dependency", 0.95
    if "no such file or directory" in evidence_text or "file not found" in evidence_text:
        return "missing_file", "missing file or path issue", 0.9
    if "permission denied" in evidence_text:
        return "permission_denied", "permission issue", 0.92
    if "assertionerror" in evidence_text or "test failed" in evidence_text:
        return "test_failure", "failing test assertion", 0.85
    if "syntaxerror" in evidence_text or "compilation" in evidence_text or "linker" in evidence_text:
        return "compile_error", "build or compile error", 0.8
    if "traceback" in evidence_text or "exception" in evidence_text or "fatal" in evidence_text:
        return "runtime_exception", "runtime exception", 0.7
    return "unknown", "unknown", 0.3


def plan_next_verification_steps(
    failure_stage: str,
    failure_kind: str,
    primary_evidence: list[str],
) -> list[str]:
    """Generate concrete, local verification steps for the current hypothesis."""
    steps = ["Re-run the same local command that produced this log to confirm the failure is reproducible."]

    if failure_kind == "missing_dependency":
        steps.append("Check dependency declarations and local environment lock state (e.g., pyproject.toml, uv.lock).")
        steps.append("Run `uv sync` and retry the command.")
    elif failure_kind == "missing_file":
        steps.append("Verify the referenced path exists and is accessible from the current working directory.")
        steps.append("Confirm relative paths are resolved from the expected execution directory.")
    elif failure_kind == "permission_denied":
        steps.append("Inspect file and directory permissions for the failing path.")
        steps.append("Retry with the same user context after adjusting local permissions.")
    elif failure_kind == "test_failure":
        steps.append("Run the failing test target in isolation to confirm deterministic reproduction.")
        steps.append("Inspect assertion inputs around the failing test case.")
    elif failure_kind == "compile_error":
        steps.append("Re-run the build command with verbose output and inspect the first compiler/linker error.")
        steps.append("Check toolchain and dependency versions used in this workspace.")
    elif failure_kind == "runtime_exception":
        steps.append("Inspect the first traceback frame in `primary_evidence` and verify inputs to that code path.")
        steps.append("Narrow the reproducer to the smallest local command that still fails.")
    else:
        steps.append("Inspect the earliest error-like line in the log and tag it with a concrete hypothesis.")
        steps.append("Capture a fresh log with more verbosity if available.")

    if failure_stage == "environment_setup":
        steps.append("Verify local tool versions and environment variables used by the command.")
    elif failure_stage == "build":
        steps.append("Confirm the build entrypoint and dependency graph are valid for this repository.")
    elif failure_stage == "test":
        steps.append("Confirm fixture/test data setup is complete before test execution.")

    if not primary_evidence:
        steps.append("No strong evidence lines were found; capture a complete log from command start to failure.")

    return steps


@app.command()
def scan(path: str = typer.Argument(".")) -> None:
    repo = Path(path).resolve()
    profile = build_repo_profile(repo)
    profile_json = profile.model_dump_json(indent=2)
    typer.echo(profile_json)

    output_path = repo / "repo_profile.json"
    output_path.write_text(profile_json, encoding="utf-8")
    typer.echo(f"Wrote repo profile to {output_path}")


@app.command()
def diagnose(
    log_file: str = typer.Argument(...),
    repo: str | None = typer.Option(
        None,
        "--repo",
        "-r",
        help="Optional repository path used to enrich failure bundle context.",
    ),
) -> None:
    log_path = Path(log_file).resolve()
    if not log_path.exists():
        typer.echo(f"Log file does not exist: {log_path}", err=True)
        raise typer.Exit(code=1)

    repo_context: RepoContext | None = None
    if repo is not None:
        repo_path = Path(repo).resolve()
        if not repo_path.is_dir():
            typer.echo(f"Repo path is not a directory: {repo_path}", err=True)
            raise typer.Exit(code=1)
        repo_context = build_repo_context(repo_path)

    lines = read_log(log_path)
    primary_evidence, supporting_evidence = extract_evidence(lines)
    failure_stage = detect_failure_stage(lines)
    failure_kind, suspected_root_cause, confidence = classify_failure_kind(
        primary_evidence,
        supporting_evidence,
    )
    next_verification_steps = plan_next_verification_steps(
        failure_stage,
        failure_kind,
        primary_evidence,
    )

    bundle = FailureBundle(
        log_path=str(log_path),
        exists=True,
        line_count=len(lines),
        failure_stage=failure_stage,
        failure_kind=failure_kind,
        confidence=confidence,
        primary_evidence=primary_evidence,
        supporting_evidence=supporting_evidence,
        suspected_root_cause=suspected_root_cause,
        next_verification_steps=next_verification_steps,
        repo_context=repo_context,
    )
    bundle_json = bundle.model_dump_json(indent=2)
    typer.echo(bundle_json)

    output_path = Path.cwd() / "failure_bundle.json"
    output_path.write_text(bundle_json, encoding="utf-8")
    typer.echo(f"Wrote failure bundle to {output_path}")


@env_app.command("draft")
def env_draft(path: str = typer.Argument(".")) -> None:
    repo = Path(path).resolve()
    if not repo.is_dir():
        typer.echo(f"Path is not a directory: {repo}", err=True)
        raise typer.Exit(code=1)

    has_pyproject = (repo / "pyproject.toml").exists()
    if has_pyproject:
        config = {
            "name": "FlowDoctor Python Dev",
            "image": "mcr.microsoft.com/devcontainers/python:1-3.12-bullseye",
            "customizations": {
                "vscode": {
                    "extensions": [
                        "ms-python.python",
                        "charliermarsh.ruff",
                    ]
                }
            },
            "postCreateCommand": "uv sync",
        }
    else:
        config = {
            "name": "FlowDoctor Dev",
            "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
            "customizations": {"vscode": {"extensions": ["ms-vscode.vscode-json"]}},
            "postCreateCommand": "echo 'Dev container ready'",
        }

    config_json = json.dumps(config, indent=2)
    typer.echo(config_json)

    devcontainer_dir = repo / ".devcontainer"
    devcontainer_dir.mkdir(parents=True, exist_ok=True)
    output_path = devcontainer_dir / "devcontainer.json"
    output_path.write_text(config_json, encoding="utf-8")
    typer.echo(f"Wrote dev container config to {output_path}")


def main() -> None:
    app()
