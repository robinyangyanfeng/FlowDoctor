import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from flowdoctor import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SCHEMA_FIELDS = {
    "schema_version",
    "log_path",
    "exists",
    "line_count",
    "failure_stage",
    "failure_kind",
    "confidence",
    "primary_evidence",
    "supporting_evidence",
    "suspected_root_cause",
    "next_verification_steps",
    "repo_context",
}


def run_diagnose_for_fixture(tmp_path: Path, monkeypatch, fixture_name: str) -> tuple[dict, str]:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    log_file = (FIXTURES_DIR / fixture_name).resolve()
    result = runner.invoke(app, ["diagnose", str(log_file)])
    assert result.exit_code == 0, result.output

    payload = json.loads((tmp_path / "failure_bundle.json").read_text(encoding="utf-8"))
    return payload, result.output


@pytest.mark.parametrize(
    ("fixture_name", "expected_kind", "evidence_hint"),
    [
        ("missing_python_dependency.log", "missing_dependency", "modulenotfounderror"),
        ("missing_file_path.log", "missing_file", "no such file or directory"),
        ("permission_denied.log", "permission_denied", "permission denied"),
        ("build_configuration_failure.log", "compile_error", "linker"),
        ("test_runtime_failure.log", "test_failure", "assertionerror"),
        ("unknown_failure.log", "unknown", "exit status 17"),
    ],
)
def test_diagnose_fixture_corpus_outputs_expected_bundle(
    tmp_path: Path,
    monkeypatch,
    fixture_name: str,
    expected_kind: str,
    evidence_hint: str,
) -> None:
    payload, output = run_diagnose_for_fixture(tmp_path, monkeypatch, fixture_name)

    assert SCHEMA_FIELDS.issubset(payload.keys())
    assert payload["failure_kind"] == expected_kind
    assert payload["primary_evidence"]
    assert any(evidence_hint in line.lower() for line in payload["primary_evidence"])
    assert payload["next_verification_steps"]
    assert isinstance(payload["next_verification_steps"], list)
    assert payload["repo_context"] is None
    assert 0.0 <= payload["confidence"] <= 1.0
    assert '"failure_kind"' in output


def test_regression_known_failure_patterns_do_not_collapse_to_unknown(tmp_path: Path, monkeypatch) -> None:
    known_fixtures = [
        "missing_python_dependency.log",
        "missing_file_path.log",
        "permission_denied.log",
        "build_configuration_failure.log",
        "test_runtime_failure.log",
    ]

    observed_kinds: set[str] = set()
    for fixture_name in known_fixtures:
        payload, _ = run_diagnose_for_fixture(tmp_path, monkeypatch, fixture_name)
        observed_kinds.add(payload["failure_kind"])

    assert "unknown" not in observed_kinds
    assert len(observed_kinds) >= 4
