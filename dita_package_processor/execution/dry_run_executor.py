"""
Dry-run execution orchestration.

This module executes a validated plan in *dry-run* mode. It does not mutate
the filesystem and must never perform irreversible actions.

Responsibilities:
- Own a dispatcher
- Implement the executor contract: execute(action) -> ExecutionActionResult
- Dispatch plans in dry-run mode
- Produce a complete ExecutionReport that mirrors real execution

This answers one question:

    "What *would* have happened if this plan were executed?"
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from dita_package_processor.execution.dispatcher import ExecutionDispatcher
from dita_package_processor.execution.models import (
    ExecutionActionResult,
    ExecutionReport,
)

LOGGER = logging.getLogger(__name__)


class DryRunExecutionError(RuntimeError):
    """
    Raised when a dry-run execution cannot be completed.

    These indicate orchestration or structural failures, not handler failures.
    """


class DryRunExecutor:
    """
    Executor that simulates execution without performing any mutations.

    Structural twin of FilesystemExecutor:
    - Owns a dispatcher
    - Implements execute(action)
    - Executes full plans through dispatcher
    """

    def __init__(self) -> None:
        """
        Initialize the dry-run executor.
        """
        self._dispatcher = ExecutionDispatcher(self)
        LOGGER.debug("DryRunExecutor initialized")

    # ------------------------------------------------------------------
    # Executor contract
    # ------------------------------------------------------------------

    def execute(self, action: Dict[str, Any]) -> ExecutionActionResult:
        """
        Simulate execution of a single action.

        This method is called by ExecutionDispatcher.

        Parameters
        ----------
        action:
            Normalized action dictionary.

        Returns
        -------
        ExecutionActionResult
            Deterministic dry-run result.
        """
        action_id = action.get("id", "<unknown>")
        action_type = action.get("type", "<unknown>")

        LOGGER.info(
            "Dry-run executing action id=%s type=%s",
            action_id,
            action_type,
        )

        # Dry-run semantics:
        # - Nothing fails
        # - Nothing mutates
        # - Nothing is permitted or denied
        # - All actions are skipped because they were not executed
        return ExecutionActionResult(
            action_id=action_id,
            status="skipped",
            handler=self.__class__.__name__,
            dry_run=True,
            message=f"Dry-run: would execute action type '{action_type}', skipped",
            metadata={
                "failure_type": None
            },
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

        Mirrors FilesystemExecutor.execute(...), but never mutates anything.

        Parameters
        ----------
        execution_id:
            Unique execution identifier.
        plan:
            Normalized execution plan dictionary.

        Returns
        -------
        ExecutionReport
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
            "Dry-run execution completed execution_id=%s total_actions=%d",
            execution_id,
            len(report.results),
        )

        return report