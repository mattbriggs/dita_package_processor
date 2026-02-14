"""
Execution dispatcher.

The dispatcher is responsible for:

- Receiving a validated plan
- Executing actions in order through an Executor
- Collecting ExecutionActionResult objects
- Emitting an ExecutionReport

It performs:
    NO planning
    NO handler resolution
    NO filesystem logic
    NO registry inspection

It is intentionally dumb.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Protocol

from dita_package_processor.execution.models import (
    ExecutionActionResult,
    ExecutionReport,
)

LOGGER = logging.getLogger(__name__)

__all__ = [
    "ExecutionDispatchError",
    "ExecutionDispatcher",
]


# ============================================================================
# Exceptions
# ============================================================================


class ExecutionDispatchError(RuntimeError):
    """Raised when execution dispatch fails structurally."""


# ============================================================================
# Protocol
# ============================================================================


class ExecutorProtocol(Protocol):
    """
    Minimal protocol for executors consumed by ExecutionDispatcher.
    """

    def execute(self, action: Dict[str, Any]) -> ExecutionActionResult:
        ...


# ============================================================================
# Dispatcher
# ============================================================================


class ExecutionDispatcher:
    """
    Deterministic action sequencer.

    Responsibilities
    ----------------
    - Call executor.execute(action)
    - Collect results
    - Produce ExecutionReport

    That is literally all it does.
    """

    def __init__(self, executor: ExecutorProtocol) -> None:
        if not hasattr(executor, "execute"):
            raise TypeError(
                "executor must implement execute(action: dict)"
            )

        self._executor = executor

        LOGGER.debug(
            "ExecutionDispatcher initialized executor=%s",
            executor.__class__.__name__,
        )

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def dispatch(
        self,
        *,
        execution_id: str,
        plan: Dict[str, Any],
        dry_run: bool,
    ) -> ExecutionReport:
        """
        Execute all actions sequentially.

        Parameters
        ----------
        execution_id : str
        plan : dict
        dry_run : bool

        Returns
        -------
        ExecutionReport
        """
        LOGGER.info(
            "Starting execution dispatch execution_id=%s dry_run=%s",
            execution_id,
            dry_run,
        )

        actions = plan.get("actions")
        if not isinstance(actions, list):
            raise ExecutionDispatchError(
                "Plan must contain an 'actions' list"
            )

        results: List[ExecutionActionResult] = []

        for idx, action in enumerate(actions):
            if not isinstance(action, dict):
                raise ExecutionDispatchError(
                    f"Action[{idx}] must be a dictionary"
                )

            action_id = action.get("id", "<unknown>")
            action_type = action.get("type")

            LOGGER.info(
                "Dispatching action id=%s type=%s",
                action_id,
                action_type,
            )

            try:
                result = self._executor.execute(action)

            except Exception as exc:  # noqa: BLE001
                LOGGER.exception(
                    "Executor crashed id=%s",
                    action_id,
                )

                result = ExecutionActionResult(
                    action_id=action_id,
                    status="failed",
                    handler=self._executor.__class__.__name__,
                    dry_run=dry_run,
                    message="Executor crashed",
                    error=str(exc),
                    metadata={"failure_type": "executor_crash"},
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
            "Execution dispatch complete execution_id=%s actions=%d",
            execution_id,
            len(results),
        )

        return report