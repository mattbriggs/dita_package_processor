"""
Planning Action: rename_map

Declares the intent to rename a DITA map from one path to another.

This action:

    • is declarative only
    • performs no filesystem mutation
    • performs no existence checks
    • performs no directory creation
    • emits JSON-safe parameters only

Actual filesystem behavior is handled later by the execution layer.

Design constraints
-----------------
Planning MUST NOT:
    • read filesystem state
    • mutate files
    • create directories
    • guess intent

Planning ONLY records intent.
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


def create_rename_map_action(
    *,
    action_id: str,
    source_path: Path | str,
    target_path: Path | str,
) -> PlanAction:
    """
    Create a ``rename_map`` planning action.

    Declares that a DITA map located at ``source_path`` should be renamed
    to ``target_path`` during execution.

    No filesystem inspection or mutation occurs here.

    Parameters
    ----------
    action_id : str
        Stable unique identifier for this action.

    source_path : Path | str
        Existing map path (relative to package root).

    target_path : Path | str
        Desired new map path.

    Returns
    -------
    PlanAction
        JSON-serializable planning action.

    Raises
    ------
    ValueError
        If parameters are missing or invalid.
    """

    # -------------------------------------------------------------------------
    # Validate
    # -------------------------------------------------------------------------

    if not action_id:
        raise ValueError("rename_map requires a non-empty action_id")

    if not source_path:
        raise ValueError("rename_map requires source_path")

    if not target_path:
        raise ValueError("rename_map requires target_path")

    # -------------------------------------------------------------------------
    # Normalize (planning emits strings only)
    # -------------------------------------------------------------------------

    normalized_source = Path(source_path).as_posix()
    normalized_target = Path(target_path).as_posix()

    LOGGER.debug(
        "Creating rename_map action id=%s source=%s target=%s",
        action_id,
        normalized_source,
        normalized_target,
    )

    parameters: Dict[str, Any] = {
        "source_path": normalized_source,
        "target_path": normalized_target,
    }

    # -------------------------------------------------------------------------
    # Declarative contract only
    # -------------------------------------------------------------------------

    return PlanAction(
        id=action_id,
        type="rename_map",
        target=normalized_target,
        parameters=parameters,
    )