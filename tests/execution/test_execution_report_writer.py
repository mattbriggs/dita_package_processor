"""
Tests for ExecutionReportWriter.

These tests lock the deterministic serialization contract:

- JSON output is valid.
- Keys are sorted.
- Formatting is stable.
- The filesystem is written correctly.
- Errors are raised on write failures.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dita_package_processor.execution.models import (
    ExecutionActionResult,
    ExecutionReport,
)
from dita_package_processor.execution.report_writer import (
    ExecutionReportWriter,
    ExecutionReportWriteError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def execution_report() -> ExecutionReport:
    results = [
        ExecutionActionResult(
            action_id="copy-0002",
            status="skipped",
            handler="DummyHandler",
            dry_run=True,
            message="Skipped",
        ),
        ExecutionActionResult(
            action_id="copy-0001",
            status="success",
            handler="DummyHandler",
            dry_run=False,
            message="Success",
        ),
    ]

    return ExecutionReport.create(
        execution_id="exec-test-001",
        dry_run=True,
        results=results,
    )


@pytest.fixture
def writer() -> ExecutionReportWriter:
    return ExecutionReportWriter()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_report_writer_creates_json_file(
    tmp_path: Path,
    execution_report: ExecutionReport,
    writer: ExecutionReportWriter,
) -> None:
    path = tmp_path / "execution_report.json"

    writer.write(report=execution_report, path=path)

    assert path.exists()
    assert path.is_file()


def test_report_writer_outputs_valid_json(
    tmp_path: Path,
    execution_report: ExecutionReport,
    writer: ExecutionReportWriter,
) -> None:
    path = tmp_path / "execution_report.json"

    writer.write(report=execution_report, path=path)

    content = path.read_text(encoding="utf-8")
    parsed = json.loads(content)

    assert isinstance(parsed, dict)
    assert parsed["execution_id"] == "exec-test-001"
    assert "results" in parsed
    assert "summary" in parsed


def test_report_writer_sorts_keys_deterministically(
    tmp_path: Path,
    execution_report: ExecutionReport,
    writer: ExecutionReportWriter,
) -> None:
    path = tmp_path / "execution_report.json"

    writer.write(report=execution_report, path=path)

    content = path.read_text(encoding="utf-8")
    parsed = json.loads(content)

    # JSON object keys must be sorted lexicographically
    keys = list(parsed.keys())
    assert keys == sorted(keys)

    # And ensure the expected keys exist
    assert keys == [
        "dry_run",
        "execution_id",
        "generated_at",
        "results",
        "summary",
    ]


def test_report_writer_is_deterministic(
    tmp_path: Path,
    execution_report: ExecutionReport,
    writer: ExecutionReportWriter,
) -> None:
    path1 = tmp_path / "report1.json"
    path2 = tmp_path / "report2.json"

    writer.write(report=execution_report, path=path1)
    writer.write(report=execution_report, path=path2)

    content1 = path1.read_text(encoding="utf-8")
    content2 = path2.read_text(encoding="utf-8")

    assert content1 == content2


def test_report_writer_raises_on_invalid_path(
    execution_report: ExecutionReport,
    writer: ExecutionReportWriter,
) -> None:
    # Attempt to write to an invalid path (directory as file)
    with pytest.raises(ExecutionReportWriteError):
        writer.write(
            report=execution_report,
            path=Path("/"),
        )