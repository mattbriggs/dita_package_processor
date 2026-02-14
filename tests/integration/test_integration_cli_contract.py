"""
CLI contract tests for the DITA Package Processor.

These tests validate command-line interface behavior, including
help output, version reporting, and basic argument validation.

The focus is on contract correctness rather than pipeline execution.
"""

from __future__ import annotations

import sys
from typing import List

import pytest

from dita_package_processor.cli import main as cli_main
from dita_package_processor import __version__


def _run_cli(
    argv: List[str],
    monkeypatch,
) -> int:
    """
    Invoke the CLI with patched argv.

    :param argv: Argument vector to simulate.
    :param monkeypatch: Pytest monkeypatch fixture.
    :return: Exit code returned by the CLI.
    """
    monkeypatch.setattr(sys, "argv", argv)
    return cli_main()


def test_help_flag_exits_cleanly(monkeypatch, capsys) -> None:
    """
    Ensure ``-h`` / ``--help`` prints usage information and exits cleanly.
    """
    exit_code = _run_cli(
        ["dita_package_processor", "--help"],
        monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "usage:" in captured.out.lower()
    assert "dita package processor" in captured.out.lower()


def test_version_flag_prints_version(monkeypatch, capsys) -> None:
    """
    Ensure ``-v`` / ``--version`` prints the installed version and exits.
    """
    exit_code = _run_cli(
        ["dita_package_processor", "--version"],
        monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert __version__ in captured.out


def test_missing_required_input_fails(monkeypatch, capsys) -> None:
    """
    Ensure invoking the CLI without required input arguments fails
    with a non-zero exit code and a clear error message.
    """
    exit_code = _run_cli(
        ["dita_package_processor"],
        monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code != 0

    # Contract: error must explicitly mention missing required input
    err = captured.err.lower()
    assert (
        "missing" in err
        or "required" in err
        or "--package" in err
    )


def test_invalid_log_level_rejected(monkeypatch, capsys) -> None:
    """
    Ensure invalid logging levels are rejected with a helpful error.
    """
    exit_code = _run_cli(
        [
            "dita_package_processor",
            "--package",
            "/tmp/does-not-matter",
            "--log-level",
            "NOT_A_LEVEL",
        ],
        monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code != 0

    err = captured.err.lower()
    assert "log" in err
    assert "level" in err
    assert "invalid" in err or "not a valid" in err