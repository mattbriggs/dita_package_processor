"""
Tests for the root CLI entry point.

These tests validate ONLY the public dispatch behavior of the root CLI.

They intentionally do NOT test subcommand logic. Each subcommand has its
own dedicated test suite.

Scope
-----
- global flags
- help/version
- implicit pipeline behavior
- subcommand dispatch boundaries

The root CLI must behave as a thin router only.
"""

from __future__ import annotations

import subprocess
import sys
from typing import List


# =============================================================================
# Helpers
# =============================================================================


def _run_cli(args: List[str]) -> subprocess.CompletedProcess[str]:
    """
    Execute the CLI as a subprocess.

    Parameters
    ----------
    args : list[str]
        CLI arguments following the module name.

    Returns
    -------
    subprocess.CompletedProcess[str]
    """
    return subprocess.run(
        [sys.executable, "-m", "dita_package_processor", *args],
        capture_output=True,
        text=True,
    )


# =============================================================================
# Help / version
# =============================================================================


def test_cli_help_exits_zero() -> None:
    """--help prints usage and exits successfully."""
    result = _run_cli(["--help"])

    assert result.returncode == 0
    assert "usage" in result.stdout.lower()


def test_cli_version_exits_zero() -> None:
    """--version prints version and exits successfully."""
    result = _run_cli(["--version"])

    assert result.returncode == 0
    assert "dita_package_processor" in result.stdout.lower()


# =============================================================================
# Implicit run behavior
# =============================================================================


def test_cli_no_arguments_invokes_run_and_fails_loudly() -> None:
    """
    Invoking the CLI with no arguments implicitly invokes ``run``.

    Because ``run`` has required arguments, this must fail with a clear
    argparse error about missing required parameters.
    """
    result = _run_cli([])

    assert result.returncode != 0
    assert "run:" in result.stderr.lower()
    assert "required" in result.stderr.lower()


def test_cli_global_flags_invoke_run_and_fail_loudly() -> None:
    """
    Global flags without an explicit subcommand still trigger implicit ``run``.
    """
    result = _run_cli(["--json"])

    assert result.returncode != 0
    assert "run:" in result.stderr.lower()
    assert "required" in result.stderr.lower()


def test_cli_unknown_token_invokes_run_and_fails() -> None:
    """
    Unknown tokens are interpreted as implicit ``run`` arguments.

    The error must come from the run parser, not "unknown command".
    """
    result = _run_cli(["definitely-not-a-command"])

    assert result.returncode != 0
    assert "run:" in result.stderr.lower()
    assert "required" in result.stderr.lower()


# =============================================================================
# Explicit command dispatch
# =============================================================================


def test_cli_recognizes_normalize_as_real_command() -> None:
    """
    ``normalize`` must be treated as a first-class subcommand.

    It must NOT fall through to implicit run.
    Missing required flags should produce normalize's own usage,
    not run's usage.
    """
    result = _run_cli(["normalize"])

    assert result.returncode != 0

    # Critical: ensure this is NOT run's parser
    assert "run:" not in result.stderr.lower()

    # Should show normalize usage/help instead
    assert "normalize" in result.stderr.lower() or "usage" in result.stderr.lower()