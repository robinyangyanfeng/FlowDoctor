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
    assert '"log_path"' in result.stdout
    assert '"exists"' in result.stdout
    assert '"line_count"' in result.stdout
    assert '"error_lines"' in result.stdout
    assert '"suspected_root_cause"' in result.stdout

    output_file = tmp_path / "failure_bundle.json"
    assert output_file.exists()

    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["log_path"] == str(log_file.resolve())
    assert payload["exists"] is True
    assert payload["line_count"] == 4
    assert payload["suspected_root_cause"] == "missing Python dependency"
    assert any("ModuleNotFoundError" in line for line in payload["error_lines"])


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
