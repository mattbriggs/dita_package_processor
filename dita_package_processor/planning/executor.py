"""
Planning execution adapter.

Planning never performs execution directly.
It delegates execution to the execution layer.

This adapter exists for backward compatibility with callers that still
invoke execution through the planning namespace.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from dita_package_processor.execution.dry_run_executor import DryRunExecutor
from dita_package_processor.execution.models import ExecutionReport

LOGGER = logging.getLogger(__name__)

__all__ = ["PlanningExecutor"]


# =============================================================================
# Helpers
# =============================================================================


def _normalize_plan_object(plan_obj: Any) -> Dict[str, Any]:
    """
    Normalize a plan object into a dictionary.

    The execution layer requires a raw dictionary containing
    an ``actions`` list.

    Supported inputs:
    - dict
    - object exposing ``to_dict()``
    - object exposing ``model_dump()``

    Parameters
    ----------
    plan_obj : Any
        Plan object or dictionary.

    Returns
    -------
    Dict[str, Any]
        Normalized plan dictionary.

    Raises
    ------
    TypeError
        If the object cannot be normalized.
    """
    if isinstance(plan_obj, dict):
        LOGGER.debug("Plan normalization: already dictionary")
        return plan_obj

    for attr in ("to_dict", "model_dump"):
        method = getattr(plan_obj, attr, None)
        if callable(method):
            LOGGER.debug("Plan normalization via %s()", attr)
            result = method()
            if not isinstance(result, dict):
                raise TypeError(
                    f"{attr}() did not return a dictionary"
                )
            return result

    raise TypeError(
        f"Unsupported plan object type: {type(plan_obj).__name__}. "
        "Expected dict or object exposing to_dict() or model_dump()."
    )


# =============================================================================
# Adapter
# =============================================================================


class PlanningExecutor:
    """
    Backwards-compatible execution adapter.

    This class does not perform execution itself. It delegates
    to ``DryRunExecutor`` in accordance with the execution contract.

    Responsibilities
    ----------------
    - Normalize incoming plan objects
    - Delegate to execution layer
    - Emit ExecutionReport
    """

    # ------------------------------------------------------------------
    # Execution entrypoint
    # ------------------------------------------------------------------

    def execute(
        self,
        plan: Any,
        *,
        execution_id: str,
    ) -> ExecutionReport:
        """
        Execute a plan in dry-run mode.

        Parameters
        ----------
        plan : Any
            Plan object or dictionary.
        execution_id : str
            Unique execution identifier.

        Returns
        -------
        ExecutionReport
        """
        LOGGER.info(
            "PlanningExecutor delegating to DryRunExecutor "
            "execution_id=%s",
            execution_id,
        )

        normalized_plan = _normalize_plan_object(plan)

        LOGGER.debug(
            "Normalized plan contains %d actions",
            len(normalized_plan.get("actions", [])),
        )

        executor = DryRunExecutor()

        report = executor.run(
            execution_id=execution_id,
            plan=normalized_plan,
        )

        LOGGER.info(
            "PlanningExecutor completed delegation "
            "execution_id=%s total=%d",
            execution_id,
            report.summary.get("total", 0),
        )

        return report