import json
from pathlib import Path

from typer.testing import CliRunner

from flowdoctor import app


def test_env_draft_writes_python_oriented_devcontainer(tmp_path: Path) -> None:
    runner = CliRunner()
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")

    result = runner.invoke(app, ["env", "draft", str(repo_dir)])

    assert result.exit_code == 0
    assert '"name"' in result.stdout
    assert '"image"' in result.stdout
    assert '"customizations"' in result.stdout
    assert '"postCreateCommand"' in result.stdout

    output_file = repo_dir / ".devcontainer" / "devcontainer.json"
    assert output_file.exists()

    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["name"] == "FlowDoctor Python Dev"
    assert payload["image"] == "mcr.microsoft.com/devcontainers/python:1-3.12-bullseye"
    assert payload["postCreateCommand"] == "uv sync"
    assert "customizations" in payload
