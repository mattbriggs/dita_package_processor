"""
Dry-run execution orchestration.

Executes a validated plan in dry-run mode. This executor never mutates
the filesystem and must never perform irreversible actions.

Responsibilities
----------------
- Own a dispatcher
- Implement the executor contract:
      execute(action: dict) -> ExecutionActionResult
- Dispatch plans in dry-run mode
- Produce a complete ExecutionReport

Dry-run answers a single question:

    "What would have happened if this plan were executed?"
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from dita_package_processor.execution.dispatcher import ExecutionDispatcher
from dita_package_processor.execution.models import (
    ExecutionActionResult,
    ExecutionReport,
)

LOGGER = logging.getLogger(__name__)

__all__ = ["DryRunExecutor", "DryRunExecutionError"]


# =============================================================================
# Exceptions
# =============================================================================


class DryRunExecutionError(RuntimeError):
    """
    Raised when dry-run orchestration fails structurally.

    These indicate dispatcher or structural failures,
    not handler or filesystem failures.
    """


# =============================================================================
# Executor
# =============================================================================


class DryRunExecutor:
    """
    Executor that simulates execution without performing mutations.

    Structural twin of FilesystemExecutor:

    - Owns a dispatcher
    - Implements execute(action)
    - Executes full plans via dispatcher
    - Never mutates state
    """

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        """Initialize dry-run executor and dispatcher."""
        self._dispatcher = ExecutionDispatcher(self)

        LOGGER.debug(
            "DryRunExecutor initialized (simulation mode only)"
        )

    # ------------------------------------------------------------------
    # Executor contract
    # ------------------------------------------------------------------

    def execute(self, action: Dict[str, Any]) -> ExecutionActionResult:
        """
        Simulate execution of a single action.

        This method is invoked by ExecutionDispatcher.

        Parameters
        ----------
        action : dict
            Normalized action dictionary.

        Returns
        -------
        ExecutionActionResult
            Deterministic dry-run result with status="skipped".
        """
        action_id = action.get("id", "<unknown>")
        action_type = action.get("type", "<unknown>")

        LOGGER.info(
            "Dry-run simulate action id=%s type=%s",
            action_id,
            action_type,
        )

        return ExecutionActionResult(
            action_id=action_id,
            status="skipped",
            handler=self.__class__.__name__,
            dry_run=True,
            message=(
                f"Dry-run: would execute action type '{action_type}'. "
                "No changes applied."
            ),
        )

    # ------------------------------------------------------------------
    # Plan execution entrypoint
    # ------------------------------------------------------------------

    def run(
        self,
        *,
        execution_id: str,
        plan: Dict[str, Any],
    ) -> ExecutionReport:
        """
        Execute a full plan in dry-run mode.

        Parameters
        ----------
        execution_id : str
            Unique execution identifier.
        plan : dict
            Validated execution plan dictionary.

        Returns
        -------
        ExecutionReport
            Dry-run execution report.
        """
        LOGGER.info(
            "Starting dry-run execution execution_id=%s",
            execution_id,
        )

        report = self._dispatcher.dispatch(
            execution_id=execution_id,
            plan=plan,
            dry_run=True,
        )

        LOGGER.info(
            "Dry-run execution complete execution_id=%s "
            "actions=%d skipped=%d",
            execution_id,
            len(report.results),
            report.summary.get("skipped", 0),
        )

        return report