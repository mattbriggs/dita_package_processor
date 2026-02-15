"""
CLI contract tests for the DITA Package Processor.

These tests validate command-line interface behavior including:

- help output
- version reporting
- required argument enforcement
- logging level validation

The CLI is a boundary adapter.
It must not leak internal exceptions or stack traces.
"""

from __future__ import annotations

import sys
from typing import List

import pytest

from dita_package_processor.cli import main as cli_main
from dita_package_processor import __version__


# =============================================================================
# Helpers
# =============================================================================


def _run_cli(
    argv: List[str],
    monkeypatch: pytest.MonkeyPatch,
) -> int:
    """
    Invoke CLI entrypoint with patched argv.

    Parameters
    ----------
    argv : List[str]
        Argument vector to simulate.
    monkeypatch : pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Returns
    -------
    int
        Exit code returned by CLI.
    """
    monkeypatch.setattr(sys, "argv", argv)
    return cli_main()


# =============================================================================
# Help + Version
# =============================================================================


def test_help_flag_exits_cleanly(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    --help must print usage and exit with code 0.
    """
    exit_code = _run_cli(
        ["dita_package_processor", "--help"],
        monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "usage:" in captured.out.lower()
    assert "dita" in captured.out.lower()


def test_version_flag_prints_version(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    --version must print installed version and exit 0.
    """
    exit_code = _run_cli(
        ["dita_package_processor", "--version"],
        monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert __version__ in captured.out


# =============================================================================
# Required arguments
# =============================================================================


def test_missing_required_package_argument_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    CLI must reject invocation without required --package.
    """
    exit_code = _run_cli(
        ["dita_package_processor", "run"],
        monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code != 0

    err = captured.err.lower()

    # Must indicate missing required argument
    assert "package" in err
    assert "required" in err or "missing" in err


# =============================================================================
# Logging validation
# =============================================================================


def test_invalid_log_level_rejected(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Invalid log levels must be rejected explicitly.

    Global arguments must precede subcommand invocation.
    """
    exit_code = _run_cli(
        [
            "dita_package_processor",
            "--log-level",
            "NOT_A_LEVEL",
            "run",
            "--package",
            "/tmp/fake",
            "--docx-stem",
            "Doc",
        ],
        monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code != 0

    err = captured.err.lower()

    # Argparse must reject invalid enum choice
    assert "log" in err
    assert "level" in err
    assert "not_a_level" in err or "invalid choice" in err