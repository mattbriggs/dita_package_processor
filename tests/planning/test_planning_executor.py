"""
Shared execution contract tests.

These tests define the execution contract that ALL executors must obey,
including DryRunExecutor and any future real filesystem executors.

Execution rules:

- Executors must accept raw plan dictionaries.
- Executors must emit an ExecutionReport.
- Executors must preserve action order.
- Executors must never mutate the input plan.
- Executors must be observable via ExecutionReport, not logs.
"""

from __future__ import annotations

import logging
from typing import Type

import pytest

from dita_package_processor.execution.dry_run_executor import DryRunExecutor
from dita_package_processor.execution.models import ExecutionReport


# ---------------------------------------------------------------------------
# Executor implementations under test
# ---------------------------------------------------------------------------


@pytest.fixture(params=[DryRunExecutor])
def executor_cls(request: pytest.FixtureRequest) -> Type[DryRunExecutor]:
    """
    Yield executor classes that must satisfy the shared execution contract.

    Every executor implementation MUST be added here.
    """
    return request.param


# ---------------------------------------------------------------------------
# Plan fixture (raw dictionary, not model objects)
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_plan() -> dict:
    """
    Minimal valid plan structure for execution.
    """
    return {
        "actions": [
            {
                "id": "action-001",
                "type": "noop",
                "target": "index.ditamap",
                "reason": "Dry run only",
            },
            {
                "id": "action-002",
                "type": "noop",
                "target": "topics/a.dita",
                "reason": "Dry run only",
            },
        ]
    }


# ---------------------------------------------------------------------------
# Shared execution contract tests
# ---------------------------------------------------------------------------


def test_executor_executes_without_error(
    executor_cls: Type[DryRunExecutor],
    sample_plan: dict,
) -> None:
    executor = executor_cls()
    report = executor.execute(
        plan=sample_plan,
        execution_id="exec-001",
    )

    assert isinstance(report, ExecutionReport)


def test_executor_returns_execution_report(
    executor_cls: Type[DryRunExecutor],
    sample_plan: dict,
) -> None:
    executor = executor_cls()
    report = executor.execute(
        plan=sample_plan,
        execution_id="exec-002",
    )

    assert report.execution_id == "exec-002"
    assert report.summary["total"] == len(sample_plan["actions"])


def test_executor_preserves_action_order(
    executor_cls: Type[DryRunExecutor],
    sample_plan: dict,
) -> None:
    executor = executor_cls()
    report = executor.execute(
        plan=sample_plan,
        execution_id="exec-003",
    )

    ids = [r.action_id for r in report.results]
    assert ids == ["action-001", "action-002"]


def test_executor_records_all_actions(
    executor_cls: Type[DryRunExecutor],
    sample_plan: dict,
) -> None:
    executor = executor_cls()
    report = executor.execute(
        plan=sample_plan,
        execution_id="exec-004",
    )

    assert len(report.results) == len(sample_plan["actions"])


def test_executor_does_not_mutate_plan(
    executor_cls: Type[DryRunExecutor],
    sample_plan: dict,
) -> None:
    original = {
        "actions": [dict(a) for a in sample_plan["actions"]]
    }

    executor = executor_cls()
    executor.execute(
        plan=sample_plan,
        execution_id="exec-005",
    )

    assert sample_plan == original


def test_executor_is_observable_via_report_not_logs(
    caplog: pytest.LogCaptureFixture,
    executor_cls: Type[DryRunExecutor],
    sample_plan: dict,
) -> None:
    caplog.set_level(logging.INFO)

    executor = executor_cls()
    report = executor.execute(
        plan=sample_plan,
        execution_id="exec-006",
    )

    assert report.summary["total"] == len(sample_plan["actions"])