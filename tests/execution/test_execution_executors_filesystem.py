"""
Tests for FilesystemExecutor.

Locks the contract:

- FilesystemExecutor builds execution infrastructure
- It delegates execution to ExecutionDispatcher
- It does NOT resolve handlers itself
- It executes full plans, not individual actions
- It does not mutate the plan
- It requires source_root + sandbox_root
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import pytest

from dita_package_processor.execution.executors.filesystem import FilesystemExecutor


# ============================================================================
# Dummy Dispatcher
# ============================================================================


class DummyDispatcher:
    """
    Fake dispatcher used to verify delegation behavior.
    """

    def __init__(self) -> None:
        self.called = False
        self.last_execution_id: str | None = None
        self.last_plan: Dict[str, Any] | None = None
        self.last_dry_run: bool | None = None

    def dispatch(
        self,
        *,
        execution_id: str,
        plan: Dict[str, Any],
        dry_run: bool,
    ):
        self.called = True
        self.last_execution_id = execution_id
        self.last_plan = plan
        self.last_dry_run = dry_run

        class DummyReport:
            results = []

        return DummyReport()


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def dummy_dispatcher(monkeypatch) -> DummyDispatcher:
    """
    Patch FilesystemExecutor so it uses DummyDispatcher.

    We replace the dispatcher instance only.
    Real initialization still runs.
    """
    dispatcher = DummyDispatcher()

    original_init = FilesystemExecutor.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._dispatcher = dispatcher

    monkeypatch.setattr(
        "dita_package_processor.execution.executors.filesystem.FilesystemExecutor.__init__",
        patched_init,
    )

    return dispatcher


# ============================================================================
# Tests
# ============================================================================


def test_filesystem_executor_delegates_to_dispatcher(
    tmp_path: Path,
    dummy_dispatcher: DummyDispatcher,
) -> None:
    """
    Executor must delegate to dispatcher without mutating plan.
    """
    executor = FilesystemExecutor(
        source_root=tmp_path,
        sandbox_root=tmp_path,
        apply=True,
    )

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

    executor.run(
        execution_id="exec-001",
        plan=plan,
    )

    assert dummy_dispatcher.called is True
    assert dummy_dispatcher.last_execution_id == "exec-001"
    assert dummy_dispatcher.last_dry_run is False
    assert dummy_dispatcher.last_plan == plan


def test_filesystem_executor_does_not_modify_plan(
    tmp_path: Path,
    dummy_dispatcher: DummyDispatcher,
) -> None:
    """
    Executor must not mutate plan structure.
    """
    executor = FilesystemExecutor(
        source_root=tmp_path,
        sandbox_root=tmp_path,
        apply=True,
    )

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

    plan_copy = dict(original_plan)

    executor.run(
        execution_id="exec-002",
        plan=original_plan,
    )

    assert dummy_dispatcher.last_plan == plan_copy