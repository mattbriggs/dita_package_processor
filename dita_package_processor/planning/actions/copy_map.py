"""
Planning Action: copy_map

Declares the intent to copy a DITA map from a source location to a target
location during execution.

DESIGN RULE
-----------
Planning must emit fully-qualified (absolute) source paths.

Execution must NEVER:
    - infer discovery roots
    - depend on cwd
    - guess filesystem context

Maps are treated as transport artifacts only. No parsing occurs here.
This module is side-effect free.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

from dita_package_processor.planning.models import PlanAction

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Factory
# =============================================================================


def create_copy_map_action(
    *,
    action_id: str,
    source_path: Union[str, Path],
    target_path: Union[str, Path],
    source_root: Union[str, Path],
) -> PlanAction:
    """
    Create a ``copy_map`` PlanAction.

    Produces a declarative action containing:
        • absolute source path
        • output-relative target path

    This guarantees execution can run without implicit filesystem context.

    Parameters
    ----------
    action_id : str
        Unique identifier for the action.

    source_path : str | Path
        Map path relative to discovery root.

    target_path : str | Path
        Destination path relative to execution output root.

    source_root : str | Path
        Discovery root directory used to resolve the absolute source.

    Returns
    -------
    PlanAction
        Schema-valid ``copy_map`` action.

    Raises
    ------
    ValueError
        If required values are missing.
    """

    # -------------------------------------------------------------------------
    # Validate
    # -------------------------------------------------------------------------

    if not action_id:
        raise ValueError("copy_map action requires action_id")

    if not source_path:
        raise ValueError("copy_map action requires source_path")

    if not target_path:
        raise ValueError("copy_map action requires target_path")

    if not source_root:
        raise ValueError("copy_map action requires source_root")

    # -------------------------------------------------------------------------
    # Normalize paths
    # -------------------------------------------------------------------------

    source_root = Path(source_root)

    source_abs = (source_root / Path(source_path)).resolve()
    target_rel = Path(target_path)

    LOGGER.debug(
        "Creating copy_map action id=%s source=%s target=%s",
        action_id,
        source_abs,
        target_rel,
    )

    # -------------------------------------------------------------------------
    # Declarative contract only
    # -------------------------------------------------------------------------

    return PlanAction(
        id=action_id,
        type="copy_map",
        parameters={
            "source_path": str(source_abs),
            "target_path": str(target_rel),
        },
    )