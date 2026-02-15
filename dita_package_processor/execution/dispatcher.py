"""
Execution dispatcher.

The dispatcher is responsible for:

- Receiving a validated plan dictionary
- Executing actions in deterministic order via an Executor
- Collecting ExecutionActionResult objects
- Emitting an ExecutionReport

It performs:
    - NO planning
    - NO handler resolution
    - NO filesystem logic
    - NO registry inspection

The dispatcher owns plan iteration and structural validation.

The executor owns single-action execution.

This module is intentionally minimal and deterministic.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Protocol

from dita_package_processor.execution.models import (
    ExecutionActionResult,
    ExecutionReport,
)

LOGGER = logging.getLogger(__name__)

__all__ = [
    "ExecutionDispatchError",
    "ExecutionDispatcher",
]


# =============================================================================
# Exceptions
# =============================================================================


class ExecutionDispatchError(RuntimeError):
    """
    Raised when the execution plan is structurally invalid.

    This indicates a contract violation between planning and execution.
    """


# =============================================================================
# Executor Protocol
# =============================================================================


class ExecutorProtocol(Protocol):
    """
    Minimal protocol for executors consumed by ExecutionDispatcher.

    Executors must implement:

        execute(action: Dict[str, Any]) -> ExecutionActionResult
    """

    def execute(self, action: Dict[str, Any]) -> ExecutionActionResult:
        ...


# =============================================================================
# Dispatcher
# =============================================================================


class ExecutionDispatcher:
    """
    Deterministic plan dispatcher.
    """

    def __init__(self, executor: ExecutorProtocol) -> None:
        """
        Initialize dispatcher with executor.
        """
        if not callable(getattr(executor, "execute", None)):
            raise TypeError(
                "executor must implement execute(action: dict)"
            )

        self._executor = executor

        LOGGER.debug(
            "ExecutionDispatcher initialized executor=%s",
            executor.__class__.__name__,
        )

    def dispatch(
        self,
        *,
        execution_id: str,
        plan: Dict[str, Any],
        dry_run: bool,
    ) -> ExecutionReport:
        """
        Execute all actions sequentially.
        """
        LOGGER.info(
            "Dispatch start execution_id=%s dry_run=%s",
            execution_id,
            dry_run,
        )

        actions = plan.get("actions")

        if not isinstance(actions, list):
            LOGGER.error("Plan missing 'actions' list")
            raise ExecutionDispatchError(
                "Plan must contain an 'actions' list"
            )

        results: List[ExecutionActionResult] = []

        for index, action in enumerate(actions):
            if not isinstance(action, dict):
                LOGGER.error("Action[%d] is not a dictionary", index)
                raise ExecutionDispatchError(
                    f"Action[{index}] must be a dictionary"
                )

            action_id = str(action.get("id", "<unknown>"))

            LOGGER.debug(
                "Dispatching action index=%d id=%s",
                index,
                action_id,
            )

            try:
                result = self._executor.execute(action)

                if not isinstance(result, ExecutionActionResult):
                    raise ExecutionDispatchError(
                        f"Executor returned invalid result type "
                        f"for action_id={action_id}"
                    )

            except Exception as exc:  # noqa: BLE001
                LOGGER.exception(
                    "Executor failure id=%s",
                    action_id,
                )

                result = ExecutionActionResult(
                    action_id=action_id,
                    status="failed",
                    handler=self._executor.__class__.__name__,
                    dry_run=dry_run,
                    message="Executor crashed during action execution",
                    error=str(exc),
                    error_type="executor_error",
                )

                results.append(result)
                break

            results.append(result)

        report = ExecutionReport.create(
            execution_id=execution_id,
            dry_run=dry_run,
            results=results,
        )

        LOGGER.info(
            "Dispatch complete execution_id=%s total=%d",
            execution_id,
            len(results),
        )

        return report