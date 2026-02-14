"""
Execution-time validation utilities.

These checks validate action parameters before execution.
They do not perform filesystem writes or mutate any state.

This module exists to enforce the executor contract:
- Plans may be structurally valid
- Actions may be syntactically correct
- But execution must still fail fast if parameters are unsafe
"""

from __future__ import annotations

import logging
from pathlib import Path

from dita_package_processor.planning.models import PlanAction

LOGGER = logging.getLogger(__name__)


class ActionValidationError(ValueError):
    """
    Raised when action parameters are invalid or unsafe for execution.
    """


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_action(action: PlanAction) -> None:
    """
    Validate a PlanAction based on its type.

    This is the main entry point used by executors. It dispatches to the
    appropriate validator based on ``action.type``.

    :param action: PlanAction to validate.
    :raises ActionValidationError: If validation fails.
    """
    LOGGER.debug(
        "Validating action id=%s type=%s target=%s",
        action.id,
        action.type,
        action.target,
    )

    if action.type == "copy_map":
        validate_copy_map_parameters(action)
        return

    # Future validators go here:
    # if action.type == "copy_topic":
    #     validate_copy_topic_parameters(action)
    #     return

    # if action.type == "copy_media":
    #     validate_copy_media_parameters(action)
    #     return

    LOGGER.warning(
        "No explicit validator registered for action type '%s'. "
        "Action will be considered valid by default.",
        action.type,
    )


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def validate_copy_map_parameters(action: PlanAction) -> None:
    """
    Validate parameters for the ``copy_map`` action.

    Required parameters:
    - source_path
    - target_path

    Validation rules:
    - source_path must exist
    - target_path must NOT already exist

    :param action: PlanAction to validate.
    :raises ActionValidationError: If validation fails.
    """
    LOGGER.debug("Validating copy_map parameters for action id=%s", action.id)

    params = action.parameters

    if not isinstance(params, dict):
        LOGGER.error("Action parameters must be a dictionary")
        raise ActionValidationError("Action parameters must be a dictionary")

    if "source_path" not in params:
        LOGGER.error("Missing parameter: source_path")
        raise ActionValidationError("Missing parameter: source_path")

    if "target_path" not in params:
        LOGGER.error("Missing parameter: target_path")
        raise ActionValidationError("Missing parameter: target_path")

    source = Path(params["source_path"])
    target = Path(params["target_path"])

    LOGGER.debug("Resolved source_path=%s target_path=%s", source, target)

    if not source.exists():
        LOGGER.error("Source path does not exist: %s", source)
        raise ActionValidationError(f"Source does not exist: {source}")

    if target.exists():
        LOGGER.error("Target path already exists: %s", target)
        raise ActionValidationError(f"Target already exists: {target}")

    LOGGER.info(
        "copy_map action '%s' validated successfully",
        action.id,
    )