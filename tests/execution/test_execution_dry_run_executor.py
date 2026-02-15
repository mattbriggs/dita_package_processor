"""
Tests for DryRunExecutor.

Locks dry-run behavior:

- Executor owns its own dispatcher.
- Full plans are executed through dispatcher via run().
- Executor.execute(action) is called once per action.
- All results are skipped with dry_run=True.
- ExecutionReport is emitted.
- Caller plan is never mutated.
- No artificial failure metadata is injected.
"""

from __future__ import annotations

from typing import Any, Dict

import pytest

from dita_package_processor.execution.dry_run_executor import DryRunExecutor
from dita_package_processor.execution.models import ExecutionActionResult


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def dry_run_executor() -> DryRunExecutor:
    """
    Provide a DryRunExecutor instance.

    The executor owns its dispatcher and requires no external wiring.
    """
    return DryRunExecutor()


@pytest.fixture
def simple_plan() -> Dict[str, Any]:
    """
    Minimal valid execution plan.

    Returns
    -------
    dict
        Plan with two actions.
    """
    return {
        "actions": [
            {"id": "copy-0001", "type": "copy_dummy"},
            {"id": "copy-0002", "type": "copy_dummy"},
        ]
    }


# =============================================================================
# Tests
# =============================================================================


def test_dry_run_executor_produces_execution_report(
    dry_run_executor: DryRunExecutor,
    simple_plan: Dict[str, Any],
) -> None:
    """
    Running a dry-run plan must emit a valid ExecutionReport.
    """
    report = dry_run_executor.run(
        execution_id="exec-dry-001",
        plan=simple_plan,
    )

    assert report.execution_id == "exec-dry-001"
    assert report.dry_run is True
    assert len(report.results) == 2

    assert report.summary["total"] == 2
    assert report.summary["skipped"] == 2
    assert report.summary["success"] == 0
    assert report.summary["failed"] == 0


def test_dry_run_executor_produces_skipped_results(
    dry_run_executor: DryRunExecutor,
    simple_plan: Dict[str, Any],
) -> None:
    """
    Every action must produce a skipped dry-run result.
    """
    report = dry_run_executor.run(
        execution_id="exec-dry-002",
        plan=simple_plan,
    )

    for result in report.results:
        assert isinstance(result, ExecutionActionResult)
        assert result.dry_run is True
        assert result.status == "skipped"
        assert result.handler == "DryRunExecutor"

        # Must provide a human-readable message
        assert result.message

        # Dry-run must not produce errors or classifications
        assert result.error is None
        assert result.error_type is None


def test_dry_run_executor_does_not_mutate_original_plan(
    dry_run_executor: DryRunExecutor,
    simple_plan: Dict[str, Any],
) -> None:
    """
    Executing a dry-run must not mutate the caller's plan.
    """
    original = {
        "actions": [dict(a) for a in simple_plan["actions"]],
    }

    dry_run_executor.run(
        execution_id="exec-dry-003",
        plan=simple_plan,
    )

    assert simple_plan == original


def test_dry_run_executor_execute_called_once_per_action(
    dry_run_executor: DryRunExecutor,
    simple_plan: Dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Dispatcher must invoke executor.execute(action) exactly once per action.
    """
    calls: list[str] = []

    original_execute = dry_run_executor.execute

    def wrapped_execute(action: Dict[str, Any]) -> ExecutionActionResult:
        calls.append(action["id"])
        return original_execute(action)

    monkeypatch.setattr(dry_run_executor, "execute", wrapped_execute)

    dry_run_executor.run(
        execution_id="exec-dry-004",
        plan=simple_plan,
    )

    assert calls == ["copy-0001", "copy-0002"]