"""
Unit tests for the ``run`` CLI command.

These tests validate structural correctness and CLI contract behavior
for the pipeline entry point.

They explicitly mock the Pipeline to ensure:
- no filesystem access
- no discovery, planning, or execution occurs
- only CLI wiring and error handling are tested
"""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dita_package_processor.cli_run import register_run


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """
    Build a minimal parser with the ``run`` command registered.

    :return: ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(prog="dita_package_processor")
    subparsers = parser.add_subparsers(dest="command", required=True)
    register_run(subparsers)
    return parser


def _fake_report() -> MagicMock:
    """
    Create a minimal fake ExecutionReport object.
    """
    report = MagicMock()
    report.execution_id = "test-run"
    report.results = []
    report.summary = {"total": 0, "success": 0, "failed": 0, "skipped": 0}
    report.dry_run = True
    return report


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_run_requires_package_and_docx_stem() -> None:
    """
    ``run`` must require both --package and --docx-stem.
    """
    parser = _build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["run"])

    with pytest.raises(SystemExit):
        parser.parse_args(["run", "--package", "/tmp"])

    with pytest.raises(SystemExit):
        parser.parse_args(["run", "--docx-stem", "OutputDoc"])


@patch("dita_package_processor.cli_run.ExecutionReportWriter")
@patch("dita_package_processor.cli_run.Pipeline")
def test_run_accepts_valid_arguments(
    mock_pipeline_cls: MagicMock,
    mock_writer_cls: MagicMock,
    tmp_path: Path,
) -> None:
    """
    ``run`` accepts valid arguments and returns a controlled exit code.

    The Pipeline is mocked to avoid executing real logic.
    """
    parser = _build_parser()

    fake_report = _fake_report()
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = fake_report
    mock_pipeline_cls.return_value = mock_pipeline

    args = parser.parse_args(
        [
            "run",
            "--package",
            str(tmp_path),
            "--docx-stem",
            "OutputDoc",
        ]
    )

    exit_code = args.func(args)

    assert exit_code == 0
    mock_pipeline_cls.assert_called_once()
    mock_pipeline.run.assert_called_once_with(apply=False)

    # No report writing unless --report is passed
    mock_writer_cls.assert_not_called()


@patch("dita_package_processor.cli_run.ExecutionReportWriter")
@patch("dita_package_processor.cli_run.Pipeline")
def test_run_apply_flag_requires_target(
    mock_pipeline_cls: MagicMock,
    mock_writer_cls: MagicMock,
    tmp_path: Path,
) -> None:
    """
    ``--apply`` without ``--target`` must fail at the CLI level
    and must NOT invoke the Pipeline.
    """
    parser = _build_parser()

    args = parser.parse_args(
        [
            "run",
            "--package",
            str(tmp_path),
            "--docx-stem",
            "OutputDoc",
            "--apply",
        ]
    )

    exit_code = args.func(args)

    assert exit_code == 2
    mock_pipeline_cls.assert_not_called()
    mock_writer_cls.assert_not_called()


@patch("dita_package_processor.cli_run.ExecutionReportWriter")
@patch("dita_package_processor.cli_run.Pipeline")
def test_run_apply_flag_is_propagated_when_target_present(
    mock_pipeline_cls: MagicMock,
    mock_writer_cls: MagicMock,
    tmp_path: Path,
) -> None:
    """
    ``--apply`` must be passed through to Pipeline.run()
    when ``--target`` is provided.
    """
    parser = _build_parser()

    fake_report = _fake_report()
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = fake_report
    mock_pipeline_cls.return_value = mock_pipeline

    target = tmp_path / "out"

    args = parser.parse_args(
        [
            "run",
            "--package",
            str(tmp_path),
            "--docx-stem",
            "OutputDoc",
            "--target",
            str(target),
            "--apply",
        ]
    )

    exit_code = args.func(args)

    assert exit_code == 0
    mock_pipeline.run.assert_called_once_with(apply=True)
    mock_writer_cls.assert_not_called()


@patch("dita_package_processor.cli_run.ExecutionReportWriter")
@patch("dita_package_processor.cli_run.Pipeline")
def test_run_report_flag_writes_execution_report(
    mock_pipeline_cls: MagicMock,
    mock_writer_cls: MagicMock,
    tmp_path: Path,
) -> None:
    """
    ``--report`` must cause the ExecutionReport to be written to disk.
    """
    parser = _build_parser()

    fake_report = _fake_report()
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = fake_report
    mock_pipeline_cls.return_value = mock_pipeline

    mock_writer = MagicMock()
    mock_writer_cls.return_value = mock_writer

    report_path = tmp_path / "execution_report.json"

    args = parser.parse_args(
        [
            "run",
            "--package",
            str(tmp_path),
            "--docx-stem",
            "OutputDoc",
            "--report",
            str(report_path),
        ]
    )

    exit_code = args.func(args)

    assert exit_code == 0

    mock_writer_cls.assert_called_once()
    mock_writer.write.assert_called_once_with(
        report=fake_report,
        path=report_path.resolve(),
    )


@patch("dita_package_processor.cli_run.Pipeline")
def test_run_missing_package_path_fails_cleanly(
    mock_pipeline_cls: MagicMock,
    tmp_path: Path,
) -> None:
    """
    ``run`` must fail cleanly when the package path does not exist.

    The Pipeline constructor is forced to raise FileNotFoundError.
    """
    parser = _build_parser()

    mock_pipeline_cls.side_effect = FileNotFoundError("Package not found")

    args = parser.parse_args(
        [
            "run",
            "--package",
            str(tmp_path / "does-not-exist"),
            "--docx-stem",
            "OutputDoc",
        ]
    )

    exit_code = args.func(args)

    assert exit_code == 2