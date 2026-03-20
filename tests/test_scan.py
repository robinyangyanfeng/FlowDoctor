import json
from pathlib import Path

from typer.testing import CliRunner

from flowdoctor import app


def test_scan_prints_json_and_writes_repo_profile(tmp_path: Path) -> None:
    runner = CliRunner()
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()
    (repo_dir / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")

    result = runner.invoke(app, ["scan", str(repo_dir)])

    assert result.exit_code == 0
    assert '"path"' in result.stdout
    assert '"has_git"' in result.stdout
    assert '"has_pyproject"' in result.stdout

    output_file = repo_dir / "repo_profile.json"
    assert output_file.exists()

    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["path"] == str(repo_dir.resolve())
    assert payload["repo_type"] == "python"
    assert "has_git" in payload
    assert "has_pyproject" in payload


def test_scan_detects_node_repo_type(tmp_path: Path) -> None:
    runner = CliRunner()
    repo_dir = tmp_path / "node-repo"
    repo_dir.mkdir()
    (repo_dir / "package.json").write_text('{"name":"x"}\n', encoding="utf-8")

    result = runner.invoke(app, ["scan", str(repo_dir)])

    assert result.exit_code == 0
    payload = json.loads((repo_dir / "repo_profile.json").read_text(encoding="utf-8"))
    assert payload["repo_type"] == "node"


def test_scan_detects_rust_repo_type(tmp_path: Path) -> None:
    runner = CliRunner()
    repo_dir = tmp_path / "rust-repo"
    repo_dir.mkdir()
    (repo_dir / "Cargo.toml").write_text("[package]\nname = 'x'\n", encoding="utf-8")

    result = runner.invoke(app, ["scan", str(repo_dir)])

    assert result.exit_code == 0
    payload = json.loads((repo_dir / "repo_profile.json").read_text(encoding="utf-8"))
    assert payload["repo_type"] == "rust"


def test_scan_detects_unknown_repo_type(tmp_path: Path) -> None:
    runner = CliRunner()
    repo_dir = tmp_path / "unknown-repo"
    repo_dir.mkdir()

    result = runner.invoke(app, ["scan", str(repo_dir)])

    assert result.exit_code == 0
    payload = json.loads((repo_dir / "repo_profile.json").read_text(encoding="utf-8"))
    assert payload["repo_type"] == "unknown"
