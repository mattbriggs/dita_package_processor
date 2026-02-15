"""
Tests for FilesystemExecutor.

Locks the contract:

- FilesystemExecutor builds execution infrastructure
- It delegates execution to ExecutionDispatcher
- It does NOT interpret plan semantics
- It executes full plans, not individual actions
- It does not mutate the plan
- It enforces dry-run semantics via apply flag
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from dita_package_processor.execution.executors.filesystem import (
    FilesystemExecutor,
)
from dita_package_processor.execution.models import ExecutionReport


# =============================================================================
# Dummy Dispatcher
# =============================================================================


class DummyDispatcher:
    """
    Fake dispatcher used to verify delegation behavior.
    """

    def __init__(self) -> None:
        self.called: bool = False
        self.last_execution_id: str | None = None
        self.last_plan: Dict[str, Any] | None = None
        self.last_dry_run: bool | None = None

    def dispatch(
        self,
        *,
        execution_id: str,
        plan: Dict[str, Any],
        dry_run: bool,
    ) -> ExecutionReport:
        self.called = True
        self.last_execution_id = execution_id
        self.last_plan = plan
        self.last_dry_run = dry_run

        return ExecutionReport.create(
            execution_id=execution_id,
            dry_run=dry_run,
            results=[],
        )


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def dummy_dispatcher() -> DummyDispatcher:
    return DummyDispatcher()


# =============================================================================
# Tests
# =============================================================================


def test_filesystem_executor_delegates_to_dispatcher(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dummy_dispatcher: DummyDispatcher,
) -> None:
    executor = FilesystemExecutor(
        source_root=tmp_path,
        sandbox_root=tmp_path,
        apply=True,
    )

    monkeypatch.setattr(executor, "_dispatcher", dummy_dispatcher)

    plan = {
        "actions": [
            {
                "id": "a1",
                "type": "copy_map",
                "target": "x.ditamap",
                "parameters": {},
            }
        ]
    }

    report = executor.run(
        execution_id="exec-001",
        plan=plan,
    )

    assert dummy_dispatcher.called is True
    assert dummy_dispatcher.last_execution_id == "exec-001"
    assert dummy_dispatcher.last_dry_run is False
    assert dummy_dispatcher.last_plan == plan

    assert isinstance(report, ExecutionReport)


def test_filesystem_executor_does_not_modify_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dummy_dispatcher: DummyDispatcher,
) -> None:
    executor = FilesystemExecutor(
        source_root=tmp_path,
        sandbox_root=tmp_path,
        apply=True,
    )

    monkeypatch.setattr(executor, "_dispatcher", dummy_dispatcher)

    original_plan = {
        "actions": [
            {
                "id": "a2",
                "type": "copy_topic",
                "target": "y.dita",
                "parameters": {},
            }
        ]
    }

    plan_copy = {
        "actions": [dict(original_plan["actions"][0])]
    }

    executor.run(
        execution_id="exec-002",
        plan=original_plan,
    )

    assert original_plan == plan_copy
    assert dummy_dispatcher.last_plan == plan_copy


def test_filesystem_executor_apply_false_enforces_dry_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dummy_dispatcher: DummyDispatcher,
) -> None:
    executor = FilesystemExecutor(
        source_root=tmp_path,
        sandbox_root=tmp_path,
        apply=False,
    )

    monkeypatch.setattr(executor, "_dispatcher", dummy_dispatcher)

    plan = {"actions": []}

    executor.run(
        execution_id="exec-003",
        plan=plan,
    )

    assert dummy_dispatcher.last_dry_run is True