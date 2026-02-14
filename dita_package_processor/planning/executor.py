"""
Planning execution adapter.

Planning never executes actions.
It delegates execution to the execution layer.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from dita_package_processor.execution.dry_run_executor import DryRunExecutor
from dita_package_processor.execution.models import ExecutionReport

LOGGER = logging.getLogger(__name__)


def _normalize_plan_object(plan_obj: Any) -> Dict[str, Any]:
    """
    Normalize a loaded plan object into a pure dictionary.

    The execution layer only accepts raw dictionaries.
    """
    # Native dict
    if isinstance(plan_obj, dict):
        LOGGER.debug("Plan already a dictionary")
        return plan_obj

    # Explicit adapter methods
    for attr in ("to_dict", "dict", "model_dump"):
        method = getattr(plan_obj, attr, None)
        if callable(method):
            LOGGER.debug("Normalizing plan via %s()", attr)
            return method()

    # Fallback: attribute extraction
    if hasattr(plan_obj, "__dict__"):
        LOGGER.debug("Normalizing plan via __dict__")
        return dict(plan_obj.__dict__)

    raise TypeError(
        f"Unsupported plan object type: {type(plan_obj).__name__}. "
        "Expected dict or object with to_dict(), dict(), model_dump(), or __dict__."
    )


class PlanningExecutor:
    """
    Adapter that hands execution off to the execution layer.

    This class exists only for backwards compatibility with code
    that still calls into the planning namespace expecting execution.
    """

    def execute(self, plan: Any, *, execution_id: str) -> ExecutionReport:
        """
        Delegate execution to the execution layer.

        :param plan: Plan object or dictionary.
        :param execution_id: Unique execution identifier.
        :return: ExecutionReport
        """
        LOGGER.info(
            "PlanningExecutor delegating execution execution_id=%s",
            execution_id,
        )

        normalized_plan = _normalize_plan_object(plan)

        executor = DryRunExecutor()
        return executor.execute(
            plan=normalized_plan,
            execution_id=execution_id,
        )