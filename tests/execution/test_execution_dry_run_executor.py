"""
Tests for DryRunExecutor.

Locks dry-run behavior:

- Executor owns its own dispatcher.
- Full plans are executed through dispatcher via run().
- Executor.execute(action) is called once per action.
- All results are skipped with dry_run=True.
- ExecutionReport is emitted.
- Caller plan is never mutated.
"""

from __future__ import annotations

from typing import Dict, Any

import pytest

from dita_package_processor.execution.dry_run_executor import DryRunExecutor
from dita_package_processor.execution.models import ExecutionActionResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def dry_run_executor() -> DryRunExecutor:
    """
    DryRunExecutor owns its own dispatcher and has no external wiring.
    """
    return DryRunExecutor()


@pytest.fixture
def simple_plan() -> Dict[str, Any]:
    """
    Minimal valid plan for execution.
    """
    return {
        "actions": [
            {"id": "copy-0001", "type": "copy_dummy"},
            {"id": "copy-0002", "type": "copy_dummy"},
        ]
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_dry_run_executor_produces_execution_report(
    dry_run_executor: DryRunExecutor,
    simple_plan: Dict[str, Any],
) -> None:
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


def test_dry_run_executor_produces_dry_run_results(
    dry_run_executor: DryRunExecutor,
    simple_plan: Dict[str, Any],
) -> None:
    report = dry_run_executor.run(
        execution_id="exec-dry-002",
        plan=simple_plan,
    )

    for result in report.results:
        assert isinstance(result, ExecutionActionResult)
        assert result.dry_run is True
        assert result.status == "skipped"
        assert result.handler == "DryRunExecutor"
        assert "would execute" in result.message.lower()

        # Safety semantics:
        # Dry-run never fails and never produces violations
        assert result.error is None
        if "failure_type" in result.metadata:
            assert result.metadata["failure_type"] is None


def test_dry_run_executor_does_not_mutate_original_plan(
    dry_run_executor: DryRunExecutor,
    simple_plan: Dict[str, Any],
) -> None:
    original = {
        "actions": [dict(a) for a in simple_plan["actions"]],
    }

    dry_run_executor.run(
        execution_id="exec-dry-003",
        plan=simple_plan,
    )

    assert simple_plan == original


def test_dry_run_executor_execute_is_called_per_action(
    dry_run_executor: DryRunExecutor,
    simple_plan: Dict[str, Any],
    monkeypatch,
) -> None:
    """
    Dispatcher must invoke executor.execute(action) once per action.
    """
    calls = []

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