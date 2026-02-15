"""
Execution domain models.

These models describe what *actually happened* during execution.
They are forensic records, not intentions.

Execution models must never be reused by planning.
They exist solely to capture observable outcomes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Literal

LOGGER = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Core execution semantics
# -----------------------------------------------------------------------------

ExecutionStatus = Literal["success", "failed", "skipped"]

ExecutionErrorType = Literal[
    "handler_error",
    "policy_violation",
    "executor_error",
]


# -----------------------------------------------------------------------------
# Action-level results
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutionActionResult:
    """
    Result of executing a single planned action.

    Parameters
    ----------
    action_id : str
        ID of the action from the plan.
    status : ExecutionStatus
        One of: "success", "failed", "skipped".
    handler : str
        Name of the handler or executor class used.
    dry_run : bool
        Whether execution was a dry-run.
    message : str
        Human-readable description of outcome.
    error : Optional[str]
        Raw error message if failure occurred.
    error_type : Optional[ExecutionErrorType]
        Structured classification of failure.

        Only meaningful when status == "failed".

        Canonical taxonomy:
            - "handler_error"
            - "policy_violation"
            - "executor_error"
    metadata : Dict[str, Any]
        Optional structured execution metadata.
    """

    action_id: str
    status: ExecutionStatus
    handler: str
    dry_run: bool
    message: str
    error: Optional[str] = None
    error_type: Optional[ExecutionErrorType] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize action execution result.

        Returns
        -------
        Dict[str, Any]
            JSON-safe dictionary representation.
        """
        LOGGER.debug(
            "Serializing ExecutionActionResult action_id=%s status=%s",
            self.action_id,
            self.status,
        )

        return {
            "action_id": self.action_id,
            "status": self.status,
            "handler": self.handler,
            "dry_run": self.dry_run,
            "message": self.message,
            "error": self.error,
            "error_type": self.error_type,
            "metadata": dict(self.metadata),
        }


# -----------------------------------------------------------------------------
# Execution report
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutionReport:
    """
    Root execution report.

    Captures a complete run of an execution pipeline.

    Parameters
    ----------
    execution_id : str
        Unique identifier for this execution run.
    generated_at : str
        ISO timestamp of report creation.
    dry_run : bool
        Whether execution was simulated.
    results : List[ExecutionActionResult]
        List of per-action execution results.
    summary : Dict[str, int]
        Aggregated statistics for quick inspection.
    """

    execution_id: str
    generated_at: str
    dry_run: bool
    results: List[ExecutionActionResult]
    summary: Dict[str, int]

    # -------------------------------------------------------------------------
    # Factory
    # -------------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        *,
        execution_id: str,
        dry_run: bool,
        results: List[ExecutionActionResult],
    ) -> ExecutionReport:
        """
        Create execution report and compute summary.

        Parameters
        ----------
        execution_id : str
            Execution identifier.
        dry_run : bool
            Dry-run flag.
        results : List[ExecutionActionResult]
            Execution results.

        Returns
        -------
        ExecutionReport
        """
        LOGGER.info(
            "Creating ExecutionReport execution_id=%s dry_run=%s results=%d",
            execution_id,
            dry_run,
            len(results),
        )

        summary = {
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "total": len(results),
        }

        for result in results:
            if result.status not in summary:
                LOGGER.error(
                    "Invalid execution status=%s action_id=%s",
                    result.status,
                    result.action_id,
                )
                raise ValueError(
                    f"Invalid execution status: {result.status}"
                )

            summary[result.status] += 1

        return cls(
            execution_id=execution_id,
            generated_at=datetime.now(UTC).isoformat(),
            dry_run=dry_run,
            results=results,
            summary=summary,
        )

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize execution report.

        Returns
        -------
        Dict[str, Any]
            JSON-safe dictionary representation.
        """
        LOGGER.debug(
            "Serializing ExecutionReport execution_id=%s results=%d",
            self.execution_id,
            len(self.results),
        )

        return {
            "execution_id": self.execution_id,
            "generated_at": self.generated_at,
            "dry_run": self.dry_run,
            "results": [r.to_dict() for r in self.results],
            "summary": dict(self.summary),
        }