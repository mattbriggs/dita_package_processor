"""
Tests for ExecutionDispatcher.

Locks the dispatcher contract:

- Actions are dispatched in order.
- The executor is called for each action.
- ExecutionActionResult objects are collected.
- An ExecutionReport is emitted.
- Structural failures raise ExecutionDispatchError.
- Handler crashes are converted into classified failures:
    status="failed"
    metadata["failure_type"] == "handler_error"
"""

from __future__ import annotations

import pytest

from dita_package_processor.execution.dispatcher import (
    ExecutionDispatcher,
    ExecutionDispatchError,
)
from dita_package_processor.execution.models import ExecutionActionResult


# ---------------------------------------------------------------------------
# Fake executor
# ---------------------------------------------------------------------------


class FakeExecutor:
    """
    Minimal executor stub used for dispatcher testing.

    Records all executed actions and returns deterministic results.
    """

    def __init__(self) -> None:
        self.executed_actions: list[dict] = []

    def execute(self, action: dict) -> ExecutionActionResult:
        """
        Match the dispatcher contract: executor must expose execute(action).
        """
        self.executed_actions.append(action)

        return ExecutionActionResult(
            action_id=action["id"],
            status="success",
            handler="FakeExecutor",
            dry_run=False,
            message=f"Executed {action['type']}",
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def executor() -> FakeExecutor:
    return FakeExecutor()


@pytest.fixture
def dispatcher(executor: FakeExecutor) -> ExecutionDispatcher:
    return ExecutionDispatcher(executor)


@pytest.fixture
def simple_plan() -> dict:
    return {
        "actions": [
            {"id": "copy-0001", "type": "copy_map"},
            {"id": "copy-0002", "type": "copy_topic"},
        ]
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_dispatch_produces_execution_report(
    dispatcher: ExecutionDispatcher,
    simple_plan: dict,
) -> None:
    report = dispatcher.dispatch(
        execution_id="exec-001",
        plan=simple_plan,
        dry_run=False,
    )

    assert report.execution_id == "exec-001"
    assert len(report.results) == 2
    assert report.summary["total"] == 2


def test_dispatch_executes_in_order(
    dispatcher: ExecutionDispatcher,
    executor: FakeExecutor,
    simple_plan: dict,
) -> None:
    dispatcher.dispatch(
        execution_id="exec-002",
        plan=simple_plan,
        dry_run=False,
    )

    ids = [a["id"] for a in executor.executed_actions]
    assert ids == ["copy-0001", "copy-0002"]


def test_dispatch_calls_executor_for_each_action(
    dispatcher: ExecutionDispatcher,
    executor: FakeExecutor,
    simple_plan: dict,
) -> None:
    dispatcher.dispatch(
        execution_id="exec-003",
        plan=simple_plan,
        dry_run=False,
    )

    assert len(executor.executed_actions) == 2


def test_dispatch_results_contain_action_ids(
    dispatcher: ExecutionDispatcher,
    simple_plan: dict,
) -> None:
    report = dispatcher.dispatch(
        execution_id="exec-004",
        plan=simple_plan,
        dry_run=False,
    )

    ids = [r.action_id for r in report.results]
    assert ids == ["copy-0001", "copy-0002"]


def test_dispatch_rejects_plan_without_actions(
    dispatcher: ExecutionDispatcher,
) -> None:
    with pytest.raises(
        ExecutionDispatchError,
        match="Plan must contain an 'actions' list",
    ):
        dispatcher.dispatch(
            execution_id="exec-005",
            plan={"not_actions": []},
            dry_run=False,
        )


def test_dispatch_rejects_non_dict_action(
    dispatcher: ExecutionDispatcher,
) -> None:
    plan = {"actions": ["not-a-dict"]}

    with pytest.raises(
        ExecutionDispatchError,
        match=r"Action\[0\] must be a dictionary",
    ):
        dispatcher.dispatch(
            execution_id="exec-006",
            plan=plan,
            dry_run=False,
        )


def test_dispatch_rejects_missing_action_type(
    dispatcher: ExecutionDispatcher,
) -> None:
    plan = {"actions": [{"id": "broken"}]}

    with pytest.raises(
        ExecutionDispatchError,
        match="missing valid 'type'",
    ):
        dispatcher.dispatch(
            execution_id="exec-007",
            plan=plan,
            dry_run=False,
        )


def test_dispatch_records_executor_failure_as_handler_error() -> None:
    """
    Handler crashes must not raise ExecutionDispatchError.
    They must be recorded as:
        status="failed"
        metadata["failure_type"] == "handler_error"
    and execution must stop.
    """

    class ExplodingExecutor:
        def execute(self, action: dict):
            raise RuntimeError("boom")

    dispatcher = ExecutionDispatcher(ExplodingExecutor())

    plan = {
        "actions": [
            {"id": "a1", "type": "copy_map"},
            {"id": "a2", "type": "copy_topic"},  # must never run
        ]
    }

    report = dispatcher.dispatch(
        execution_id="exec-008",
        plan=plan,
        dry_run=False,
    )

    # Only the first action is recorded
    assert len(report.results) == 1

    result = report.results[0]
    assert result.action_id == "a1"
    assert result.status == "failed"
    assert result.metadata["failure_type"] == "handler_error"
    assert "boom" in result.error