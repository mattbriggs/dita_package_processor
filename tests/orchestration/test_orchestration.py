"""
Unit tests for orchestration helpers.

These tests validate ONLY the orchestration layer:

- executor resolution
- constructor wiring
- no policy construction here
- correct executor types

Discovery and planning are tested elsewhere.

No filesystem mutation or execution occurs here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dita_package_processor.orchestration import get_executor


# ----------------------------------------------------------------------
# Executor resolution
# ----------------------------------------------------------------------


def test_get_executor_returns_filesystem_executor(tmp_path: Path) -> None:
    """
    filesystem executor should be returned when name='filesystem'.

    Orchestration only wires constructor args. It must not create policies
    or inspect executor internals.
    """
    executor = get_executor(
        "filesystem",
        apply=True,
        source_root=tmp_path,
        sandbox_root=tmp_path,
    )

    from dita_package_processor.execution.executors.filesystem import (
        FilesystemExecutor,
    )

    assert isinstance(executor, FilesystemExecutor)

    # Only verify wiring
    assert executor.source_root == tmp_path.resolve()
    assert executor.sandbox.root == tmp_path.resolve()
    assert executor.apply is True


def test_get_executor_returns_dry_run_executor_for_noop(tmp_path: Path) -> None:
    """
    noop should resolve to DryRunExecutor.
    """
    executor = get_executor(
        "noop",
        apply=False,
        source_root=tmp_path,
        sandbox_root=tmp_path,
    )

    from dita_package_processor.execution.dry_run_executor import DryRunExecutor

    assert isinstance(executor, DryRunExecutor)


def test_get_executor_rejects_unknown_executor(tmp_path: Path) -> None:
    """
    Unknown executor names must fail loudly.
    """
    with pytest.raises(ValueError):
        get_executor(
            "not-a-real-executor",
            apply=False,
            source_root=tmp_path,
            sandbox_root=tmp_path,
        )