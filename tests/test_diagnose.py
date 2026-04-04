import json
from pathlib import Path

from typer.testing import CliRunner

from flowdoctor import app


def test_diagnose_prints_json_and_writes_failure_bundle(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    log_file = tmp_path / "sample.log"
    log_file.write_text(
        "INFO starting\n"
        "Traceback (most recent call last):\n"
        "ModuleNotFoundError: No module named 'requests'\n"
        "Build failed\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["diagnose", str(log_file)])

    assert result.exit_code == 0
    assert '"schema_version"' in result.stdout
    assert '"log_path"' in result.stdout
    assert '"exists"' in result.stdout
    assert '"line_count"' in result.stdout
    assert '"failure_stage"' in result.stdout
    assert '"failure_kind"' in result.stdout
    assert '"confidence"' in result.stdout
    assert '"primary_evidence"' in result.stdout
    assert '"supporting_evidence"' in result.stdout
    assert '"suspected_root_cause"' in result.stdout
    assert '"next_verification_steps"' in result.stdout
    assert '"repo_context"' in result.stdout

    output_file = tmp_path / "failure_bundle.json"
    assert output_file.exists()

    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "2.0"
    assert payload["log_path"] == str(log_file.resolve())
    assert payload["exists"] is True
    assert payload["line_count"] == 4
    assert payload["failure_stage"] == "build"
    assert payload["failure_kind"] == "missing_dependency"
    assert payload["confidence"] >= 0.9
    assert payload["suspected_root_cause"] == "missing Python dependency"
    assert payload["repo_context"] is None
    assert isinstance(payload["primary_evidence"], list)
    assert isinstance(payload["supporting_evidence"], list)
    assert isinstance(payload["next_verification_steps"], list)
    assert any("ModuleNotFoundError" in line for line in payload["primary_evidence"])
    assert any("uv sync" in step for step in payload["next_verification_steps"])


def test_diagnose_classifies_missing_file_and_keeps_artifact_location(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    log_file = tmp_path / "missing-file.log"
    log_file.write_text(
        "running task\n"
        "fatal: open config.yaml: No such file or directory\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["diagnose", str(log_file)])

    assert result.exit_code == 0

    output_file = tmp_path / "failure_bundle.json"
    assert output_file.exists()

    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["failure_kind"] == "missing_file"
    assert payload["suspected_root_cause"] == "missing file or path issue"
    assert payload["line_count"] == 2
    assert any("No such file or directory" in line for line in payload["primary_evidence"])


def test_diagnose_includes_repo_context_when_repo_option_is_provided(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()
    (repo_dir / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")

    log_file = tmp_path / "repo-context.log"
    log_file.write_text("ModuleNotFoundError: No module named 'requests'\n", encoding="utf-8")

    result = runner.invoke(app, ["diagnose", str(log_file), "--repo", str(repo_dir)])

    assert result.exit_code == 0

    payload = json.loads((tmp_path / "failure_bundle.json").read_text(encoding="utf-8"))
    repo_context = payload["repo_context"]

    assert repo_context is not None
    assert repo_context["repo_path"] == str(repo_dir.resolve())
    assert repo_context["repo_type"] == "python"
    assert repo_context["has_git"] is True
    assert repo_context["has_pyproject"] is True


def test_diagnose_missing_log_exits_nonzero_and_no_traceback(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    missing_log = tmp_path / "missing.log"
    result = runner.invoke(app, ["diagnose", str(missing_log)])

    combined_output = result.stdout
    if hasattr(result, "stderr"):
        combined_output += result.stderr

    assert result.exit_code != 0
    assert "Log file does not exist" in combined_output
    assert "Traceback (most recent call last)" not in combined_output
