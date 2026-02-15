"""
Shared action-executor contract tests.

These tests define the execution contract that ALL action executors must obey.

Execution rules
---------------

- Executors must accept a single action dictionary.
- Executors must return an ExecutionActionResult.
- Executors must not mutate the input action.
- Observability must come from ExecutionActionResult, not logging.
- Result surface must remain stable.
"""

from __future__ import annotations

import logging
from typing import Type

import pytest

from dita_package_processor.execution.dry_run_executor import DryRunExecutor
from dita_package_processor.execution.models import ExecutionActionResult


# =============================================================================
# Executor implementations under test
# =============================================================================


@pytest.fixture(params=[DryRunExecutor])
def executor_cls(request: pytest.FixtureRequest) -> Type[DryRunExecutor]:
    """
    Yield executor classes that must satisfy the shared execution contract.

    Any new executor implementation must be added here.
    """
    return request.param


# =============================================================================
# Action fixture
# =============================================================================


@pytest.fixture
def sample_action() -> dict:
    """
    Minimal valid action structure.

    The executor contract does not validate planning semantics —
    it only executes what it is given.
    """
    return {
        "id": "action-001",
        "type": "noop",
        "target": "index.ditamap",
        "reason": "Dry run only",
    }


# =============================================================================
# Shared execution contract tests
# =============================================================================


def test_executor_returns_execution_action_result(
    executor_cls: Type[DryRunExecutor],
    sample_action: dict,
) -> None:
    """
    Executor must return an ExecutionActionResult without raising.
    """
    executor = executor_cls()
    result = executor.execute(sample_action)

    assert isinstance(result, ExecutionActionResult)


def test_executor_preserves_action_id(
    executor_cls: Type[DryRunExecutor],
    sample_action: dict,
) -> None:
    """
    Result must reference the original action ID.
    """
    executor = executor_cls()
    result = executor.execute(sample_action)

    assert result.action_id == sample_action["id"]


def test_executor_does_not_mutate_action(
    executor_cls: Type[DryRunExecutor],
    sample_action: dict,
) -> None:
    """
    Executors must not mutate the input action dictionary.
    """
    original = dict(sample_action)

    executor = executor_cls()
    executor.execute(sample_action)

    assert sample_action == original


def test_executor_result_surface_is_explicit(
    executor_cls: Type[DryRunExecutor],
    sample_action: dict,
) -> None:
    """
    The result surface must remain stable and explicit.

    This locks the public execution contract.
    """
    executor = executor_cls()
    result = executor.execute(sample_action)

    # Required fields
    assert result.action_id == "action-001"
    assert result.handler == executor.__class__.__name__
    assert result.dry_run is True
    assert result.status in {"success", "failed", "skipped"}

    # Structured error classification must exist on surface
    assert hasattr(result, "error")
    assert hasattr(result, "error_type")

    # Dry-run semantics
    if isinstance(executor, DryRunExecutor):
        assert result.status == "skipped"
        assert result.error is None
        assert result.error_type is None


def test_executor_is_observable_via_result_not_logs(
    caplog: pytest.LogCaptureFixture,
    executor_cls: Type[DryRunExecutor],
    sample_action: dict,
) -> None:
    """
    Observability must come from ExecutionActionResult,
    not logging side effects.
    """
    caplog.set_level(logging.INFO)

    executor = executor_cls()
    result = executor.execute(sample_action)

    assert result.action_id == sample_action["id"]