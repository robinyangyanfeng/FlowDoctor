from pathlib import Path

import typer
from pydantic import BaseModel

app = typer.Typer(no_args_is_help=True, help="FlowDoctor CLI")


class RepoProfile(BaseModel):
    path: str
    repo_type: str = "unknown"
    has_git: bool = False
    has_pyproject: bool = False


@app.callback()
def callback() -> None:
    """Turn hard-to-run repos into AI-ready workspaces."""
    pass


@app.command()
def scan(path: str = ".") -> None:
    repo = Path(path).resolve()

    profile = RepoProfile(
        path=str(repo),
        has_git=(repo / ".git").exists(),
        has_pyproject=(repo / "pyproject.toml").exists(),
    )

    typer.echo(profile.model_dump_json(indent=2))


def main() -> None:
    app()