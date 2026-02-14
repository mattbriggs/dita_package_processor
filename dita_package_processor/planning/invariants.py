"""
Invariant enforcement for DITA execution plans.

This module defines and enforces *global execution invariants* that must
hold for a plan to be considered logically safe to execute.

Invariants differ from schema validation:

- Validation ensures structural correctness.
- Invariants ensure semantic and operational safety.

Any invariant violation is fatal and must halt execution.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

LOGGER = logging.getLogger(__name__)


class InvariantViolationError(ValueError):
    """
    Raised when an execution invariant is violated.

    This signals that a plan is unsafe to execute regardless of
    syntactic correctness.
    """


def validate_invariants(plan: Dict[str, Any]) -> None:
    """
    Validate all execution invariants for a plan.

    This function is the single public entry point for invariant
    enforcement. It must be called after schema validation and before
    execution.

    :param plan: Execution plan dictionary.
    :raises InvariantViolationError: If any invariant is violated.
    """
    LOGGER.debug("Starting invariant validation")

    actions: List[Dict[str, Any]] = plan.get("actions", [])

    LOGGER.debug("Plan contains %d actions", len(actions))

    _enforce_single_main_map_selection(actions)

    LOGGER.info("All plan invariants validated successfully")


def _enforce_single_main_map_selection(actions: List[Dict[str, Any]]) -> None:
    """
    Ensure that at most one MAIN map selection exists.

    A plan may select zero or one MAIN map. Selecting more than one
    introduces ambiguity and is unsafe.

    :param actions: List of plan actions.
    :raises InvariantViolationError: If violated.
    """
    main_selections = [
        action
        for action in actions
        if action.get("type") == "select_main_map"
    ]

    LOGGER.debug(
        "Detected %d main map selection actions",
        len(main_selections),
    )

    if len(main_selections) > 1:
        ids = [a.get("id", "<unknown>") for a in main_selections]
        LOGGER.error(
            "Invariant violated: multiple MAIN map selections: %s",
            ids,
        )
        raise InvariantViolationError(
            "Invariant violated: multiple MAIN map selections detected."
        )