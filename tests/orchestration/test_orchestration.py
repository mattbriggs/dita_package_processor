"""
Unit tests for orchestration helpers.

These tests validate ONLY the orchestration layer:

- Executor resolution
- Constructor wiring
- No policy construction
- No semantic logic
- Correct executor types

Discovery and planning are tested elsewhere.

No filesystem mutation or execution occurs here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dita_package_processor.orchestration import get_executor


# =============================================================================
# Executor resolution
# =============================================================================


def test_get_executor_returns_filesystem_executor(tmp_path: Path) -> None:
    """
    "filesystem" must resolve to FilesystemExecutor.

    Orchestration must:
    - pass constructor arguments explicitly
    - resolve paths before passing
    - not mutate apply flag
    """
    source_root = tmp_path / "src"
    sandbox_root = tmp_path / "out"

    source_root.mkdir()
    sandbox_root.mkdir()

    executor = get_executor(
        "filesystem",
        apply=True,
        source_root=source_root,
        sandbox_root=sandbox_root,
    )

    from dita_package_processor.execution.executors.filesystem import (
        FilesystemExecutor,
    )

    assert isinstance(executor, FilesystemExecutor)

    # We only verify orchestration-level guarantees:
    # The resolved source_root and apply flag.
    assert executor.source_root == source_root.resolve()
    assert executor.apply is True


def test_get_executor_returns_dry_run_executor_for_noop(
    tmp_path: Path,
) -> None:
    """
    "noop" must resolve to DryRunExecutor.

    Orchestration must not inspect or adapt signatures.
    """
    executor = get_executor(
        "noop",
        apply=False,
        source_root=tmp_path,
        sandbox_root=tmp_path,
    )

    from dita_package_processor.execution.dry_run_executor import (
        DryRunExecutor,
    )

    assert isinstance(executor, DryRunExecutor)


def test_get_executor_rejects_unknown_executor(tmp_path: Path) -> None:
    """
    Unknown executor names must raise ValueError.
    """
    with pytest.raises(ValueError, match="Unknown executor"):
        get_executor(
            "not-a-real-executor",
            apply=False,
            source_root=tmp_path,
            sandbox_root=tmp_path,
        )