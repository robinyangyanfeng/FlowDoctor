import json
import typer
from pathlib import Path
from pydantic import BaseModel

app = typer.Typer(no_args_is_help=True)
env_app = typer.Typer(no_args_is_help=True)
app.add_typer(env_app, name="env")


class RepoProfile(BaseModel):
    path: str
    repo_type: str = "unknown"
    has_git: bool = False
    has_pyproject: bool = False


class FailureBundle(BaseModel):
    log_path: str
    exists: bool
    line_count: int
    error_lines: list[str]
    suspected_root_cause: str


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


@app.command()
def scan(path: str = typer.Argument(".")) -> None:
    repo = Path(path).resolve()
    profile = RepoProfile(
        path=str(repo),
        repo_type=infer_repo_type(repo),
        has_git=(repo / ".git").exists(),
        has_pyproject=(repo / "pyproject.toml").exists(),
    )
    profile_json = profile.model_dump_json(indent=2)
    typer.echo(profile_json)

    output_path = repo / "repo_profile.json"
    output_path.write_text(profile_json, encoding="utf-8")
    typer.echo(f"Wrote repo profile to {output_path}")


@app.command()
def diagnose(log_file: str = typer.Argument(...)) -> None:
    log_path = Path(log_file).resolve()
    if not log_path.exists():
        typer.echo(f"Log file does not exist: {log_path}", err=True)
        raise typer.Exit(code=1)

    text = log_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    keywords = ("error", "exception", "failed", "traceback", "fatal")
    error_lines = [line for line in lines if any(k in line.lower() for k in keywords)][:10]

    suspected_root_cause = "unknown"
    if any("modulenotfounderror" in line.lower() for line in error_lines):
        suspected_root_cause = "missing Python dependency"
    elif any("no such file or directory" in line.lower() for line in error_lines):
        suspected_root_cause = "missing file or path issue"
    elif any("permission denied" in line.lower() for line in error_lines):
        suspected_root_cause = "permission issue"

    bundle = FailureBundle(
        log_path=str(log_path),
        exists=True,
        line_count=len(lines),
        error_lines=error_lines,
        suspected_root_cause=suspected_root_cause,
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
