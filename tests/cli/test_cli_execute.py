from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


# =============================================================================
# Helpers
# =============================================================================


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    """
    Invoke exactly how a real user would:

        python -m dita_package_processor execute ...

    No mocks. Real subprocess only.
    """
    return subprocess.run(
        [sys.executable, "-m", "dita_package_processor", *args],
        capture_output=True,
        text=True,
    )


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def minimal_plan_file(tmp_path: Path) -> Path:
    """
    Smallest VALID hydrated plan.
    """
    plan = {
        "plan_version": 1,
        "generated_at": "2026-01-01T00:00:00+00:00",
        "source_discovery": {
            "path": "discovery.json",
            "schema_version": 1,
            "artifact_count": 0,
        },
        "intent": {
            "target": "analysis_only",
            "description": "test",
        },
        "actions": [],
        "invariants": [],
    }

    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    return path


@pytest.fixture
def source_root(tmp_path: Path) -> Path:
    """
    Minimal source directory required by CLI.
    """
    src = tmp_path / "src"
    src.mkdir()
    return src


# =============================================================================
# Tests
# =============================================================================


def test_execute_requires_plan(tmp_path: Path, source_root: Path) -> None:
    result = _run_cli(
        [
            "execute",
            "--output",
            str(tmp_path / "out"),
            "--source-root",
            str(source_root),
        ]
    )
    assert result.returncode != 0


def test_execute_requires_output(minimal_plan_file: Path, source_root: Path) -> None:
    result = _run_cli(
        [
            "execute",
            "--plan",
            str(minimal_plan_file),
            "--source-root",
            str(source_root),
        ]
    )
    assert result.returncode != 0


def test_execute_requires_source_root(minimal_plan_file: Path, tmp_path: Path) -> None:
    result = _run_cli(
        [
            "execute",
            "--plan",
            str(minimal_plan_file),
            "--output",
            str(tmp_path / "out"),
        ]
    )
    assert result.returncode != 0


def test_execute_missing_plan_file_fails(tmp_path: Path, source_root: Path) -> None:
    result = _run_cli(
        [
            "execute",
            "--plan",
            str(tmp_path / "missing.json"),
            "--output",
            str(tmp_path / "out"),
            "--source-root",
            str(source_root),
        ]
    )
    assert result.returncode != 0


def test_execute_invalid_source_root_fails(minimal_plan_file: Path, tmp_path: Path) -> None:
    result = _run_cli(
        [
            "execute",
            "--plan",
            str(minimal_plan_file),
            "--output",
            str(tmp_path / "out"),
            "--source-root",
            str(tmp_path / "does-not-exist"),
        ]
    )
    assert result.returncode != 0


# -----------------------------------------------------------------------------
# Success paths
# -----------------------------------------------------------------------------


def test_execute_creates_output_directory(
    minimal_plan_file: Path,
    tmp_path: Path,
    source_root: Path,
) -> None:
    out = tmp_path / "out"

    result = _run_cli(
        [
            "execute",
            "--plan",
            str(minimal_plan_file),
            "--output",
            str(out),
            "--source-root",
            str(source_root),
        ]
    )

    assert result.returncode == 0
    assert out.exists()
    assert out.is_dir()


def test_execute_writes_report(
    minimal_plan_file: Path,
    tmp_path: Path,
    source_root: Path,
) -> None:
    out = tmp_path / "out"
    report_path = tmp_path / "report.json"

    result = _run_cli(
        [
            "execute",
            "--plan",
            str(minimal_plan_file),
            "--output",
            str(out),
            "--report",
            str(report_path),
            "--source-root",
            str(source_root),
        ]
    )

    assert result.returncode == 0
    assert report_path.exists()

    data = json.loads(report_path.read_text())

    # Only verify CLI contract, not executor internals
    assert isinstance(data, dict)
    assert "execution_id" in data


def test_execute_json_stdout(
    minimal_plan_file: Path,
    tmp_path: Path,
    source_root: Path,
) -> None:
    out = tmp_path / "out"

    result = _run_cli(
        [
            "execute",
            "--json",
            "--plan",
            str(minimal_plan_file),
            "--output",
            str(out),
            "--source-root",
            str(source_root),
        ]
    )

    assert result.returncode == 0

    payload = json.loads(result.stdout)

    assert "execution_report" in payload


def test_execute_apply_flag_succeeds(
    minimal_plan_file: Path,
    tmp_path: Path,
    source_root: Path,
) -> None:
    out = tmp_path / "out"

    result = _run_cli(
        [
            "execute",
            "--plan",
            str(minimal_plan_file),
            "--output",
            str(out),
            "--source-root",
            str(source_root),
            "--apply",
        ]
    )

    assert result.returncode == 0
    assert out.exists()