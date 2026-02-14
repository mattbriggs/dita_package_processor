"""
Planning Action: assert_invariant

Declares a runtime invariant that MUST hold true during execution.

This action:

    • is declarative only
    • performs no filesystem access
    • performs no validation at planning time
    • records an explicit contract to be checked later

Execution handlers are responsible for enforcing the invariant and
failing loudly if violated.

Design constraints
-----------------
Planning MUST NOT:
    • inspect filesystem
    • inspect XML
    • evaluate conditions
    • mutate state

Planning ONLY records intent.

Invariants exist to:
    • make assumptions explicit
    • prevent silent corruption
    • fail early and deterministically
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from dita_package_processor.planning.models import PlanAction

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Factory
# =============================================================================


def create_assert_invariant_action(
    *,
    action_id: str,
    invariant_type: str,
    parameters: Dict[str, Any] | None = None,
    description: str | None = None,
) -> PlanAction:
    """
    Create an ``assert_invariant`` planning action.

    This action declares that execution MUST verify some condition
    before or during mutation.

    Examples
    --------
    path exists:

        create_assert_invariant_action(
            action_id="inv-001",
            invariant_type="path_exists",
            parameters={"path": "topics/overview.dita"},
        )

    no duplicate targets:

        create_assert_invariant_action(
            action_id="inv-002",
            invariant_type="no_duplicate_targets",
        )

    Parameters
    ----------
    action_id : str
        Stable unique identifier.

    invariant_type : str
        Name of invariant to enforce.
        Must be a simple string understood by the execution layer.

    parameters : dict, optional
        JSON-serializable parameters for the invariant.

    description : str, optional
        Human-readable explanation for logs and reports.

    Returns
    -------
    PlanAction
        JSON-safe declarative invariant action.

    Raises
    ------
    ValueError
        If required fields are missing or invalid.
    """

    # -------------------------------------------------------------------------
    # Validate
    # -------------------------------------------------------------------------

    if not action_id:
        raise ValueError("assert_invariant requires non-empty action_id")

    if not invariant_type or not isinstance(invariant_type, str):
        raise ValueError("assert_invariant requires invariant_type string")

    parameters = parameters or {}

    if not isinstance(parameters, dict):
        raise ValueError("assert_invariant parameters must be a dict")

    # normalize any Paths → strings (planning must be JSON-safe)
    normalized_params: Dict[str, Any] = {}
    for key, value in parameters.items():
        if isinstance(value, Path):
            normalized_params[key] = value.as_posix()
        else:
            normalized_params[key] = value

    LOGGER.debug(
        "Creating assert_invariant action id=%s type=%s",
        action_id,
        invariant_type,
    )

    payload: Dict[str, Any] = {
        "invariant_type": invariant_type,
        "parameters": normalized_params,
    }

    if description:
        payload["description"] = description

    # -------------------------------------------------------------------------
    # Declarative contract only
    # -------------------------------------------------------------------------

    return PlanAction(
        id=action_id,
        type="assert_invariant",
        parameters=payload,
    )