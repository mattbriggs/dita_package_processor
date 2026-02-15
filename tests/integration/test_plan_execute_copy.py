"""
Integration test: FilesystemExecutor copy execution.

Validates:

- FilesystemExecutor.run() emits ExecutionReport
- apply=False enforces dry-run semantics
- All actions produce ExecutionActionResult
- ExecutionReport structure is correct
- No mutation assumptions are made

This test does not require handlers to be implemented.
It verifies executor + dispatcher contract only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from dita_package_processor.execution.executors.filesystem import (
    FilesystemExecutor,
)
from dita_package_processor.execution.models import (
    ExecutionReport,
    ExecutionActionResult,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_dita_package(tmp_path: Path) -> Path:
    """
    Minimal fake DITA package root.
    """
    source = tmp_path / "source"
    source.mkdir()

    (source / "Main.ditamap").write_text("<map/>", encoding="utf-8")

    return source


@pytest.fixture
def execution_target(tmp_path: Path) -> Path:
    """
    Target sandbox root.
    """
    target = tmp_path / "target"
    target.mkdir()
    return target


# =============================================================================
# Helpers
# =============================================================================


def _build_minimal_execution_plan(
    source_root: Path,
    target_root: Path,
) -> Dict[str, Any]:
    """
    Construct minimal execution plan dictionary.

    Uses simple copy-type actions.
    """
    return {
        "actions": [
            {
                "id": "copy-0001",
                "type": "copy_map",
                "target": str(target_root / "Main.ditamap"),
                "parameters": {},
                "reason": "integration-test",
            }
        ]
    }


# =============================================================================
# Tests
# =============================================================================


def test_apply_false_produces_dry_run_report(
    sample_dita_package: Path,
    execution_target: Path,
) -> None:
    """
    apply=False must enforce dry-run semantics.

    Executor must:
        - Emit ExecutionReport
        - Set report.dry_run=True
        - Emit one result per action
        - Mark results dry_run=True
    """
    plan = _build_minimal_execution_plan(
        sample_dita_package,
        execution_target,
    )

    executor = FilesystemExecutor(
        source_root=sample_dita_package,
        sandbox_root=execution_target,
        apply=False,  # hardened: no mutation
    )

    report = executor.run(
        execution_id="apply-test",
        plan=plan,
    )

    # -------------------------------------------------------------------------
    # Structural assertions
    # -------------------------------------------------------------------------

    assert isinstance(report, ExecutionReport)
    assert report.execution_id == "apply-test"
    assert report.dry_run is True

    assert len(report.results) == len(plan["actions"])
    assert report.summary["total"] == len(plan["actions"])

    # -------------------------------------------------------------------------
    # Result semantics
    # -------------------------------------------------------------------------

    for result in report.results:
        assert isinstance(result, ExecutionActionResult)
        assert result.dry_run is True
        assert result.status in {"skipped", "failed"}
        assert result.error_type in {None, "handler_error", "policy_violation", "executor_error"}