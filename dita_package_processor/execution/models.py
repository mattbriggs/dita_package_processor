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

# ----------------------------------------------------------------------
# Core execution semantics
# ----------------------------------------------------------------------

ExecutionStatus = Literal["success", "failed", "skipped"]

ExecutionFailureType = Literal[
    "policy_violation",
    "sandbox_violation",
    "handler_error",
    "filesystem_error",
    "validation_error",
]


# ----------------------------------------------------------------------
# Action-level results
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutionActionResult:
    """
    Result of executing a single planned action.

    Fields:
        action_id:
            ID of the action from the plan.
        status:
            One of: success | failed | skipped.
        handler:
            Name of the handler class used.
        dry_run:
            Whether execution was a dry-run.
        message:
            Human-readable description of outcome.
        error:
            Error message if failure occurred.
        failure_type:
            Structured classification of why a failure occurred.
            Only meaningful when status == "failed".
        metadata:
            Optional structured execution metadata.
    """

    action_id: str
    status: ExecutionStatus
    handler: str
    dry_run: bool
    message: str
    error: Optional[str] = None
    failure_type: Optional[ExecutionFailureType] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize action execution result.

        :return: JSON-safe dictionary.
        """
        LOGGER.debug(
            "Serializing ExecutionActionResult for action_id=%s status=%s",
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
            "failure_type": self.failure_type,
            "metadata": dict(self.metadata),
        }


# ----------------------------------------------------------------------
# Execution report
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutionReport:
    """
    Root execution report.

    Captures a complete run of an execution pipeline.

    Fields:
        execution_id:
            Unique identifier for this execution run.
        generated_at:
            ISO timestamp of report creation.
        dry_run:
            Whether execution was simulated.
        results:
            List of per-action execution results.
        summary:
            Aggregated statistics for quick inspection.
    """

    execution_id: str
    generated_at: str
    dry_run: bool
    results: List[ExecutionActionResult]
    summary: Dict[str, int]

    @classmethod
    def create(
        cls,
        *,
        execution_id: str,
        dry_run: bool,
        results: List[ExecutionActionResult],
    ) -> ExecutionReport:
        """
        Factory method that computes summary automatically.

        :param execution_id: Execution identifier.
        :param dry_run: Dry-run flag.
        :param results: Execution results.
        :return: ExecutionReport instance.
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

        for r in results:
            if r.status not in summary:
                LOGGER.error(
                    "Invalid execution status encountered: %s for action_id=%s",
                    r.status,
                    r.action_id,
                )
                raise ValueError(f"Invalid execution status: {r.status}")

            summary[r.status] += 1

        return cls(
            execution_id=execution_id,
            generated_at=datetime.now(UTC).isoformat(),
            dry_run=dry_run,
            results=results,
            summary=summary,
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize execution report.

        :return: JSON-safe dictionary.
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