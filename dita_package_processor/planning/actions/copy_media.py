"""
Planning Action: copy_media

Declares the intent to copy a binary/media artifact from a source
location to a target location during execution.

DESIGN RULE
-----------
Planning resolves paths.
Execution executes.

Planning MUST emit:
    • absolute source paths
    • output-relative target paths

Execution MUST NOT:
    • infer discovery roots
    • depend on cwd
    • guess filesystem context

Media actions are intentionally dumb: they describe transport only.
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


def create_copy_media_action(
    *,
    action_id: str,
    source_path: Union[str, Path],
    target_path: Union[str, Path],
    source_root: Union[str, Path],
) -> PlanAction:
    """
    Create a ``copy_media`` PlanAction.

    Produces a declarative action containing:
        • absolute source path (fully resolved)
        • target path relative to execution output root

    This guarantees the execution layer can run with zero implicit
    filesystem assumptions.

    Parameters
    ----------
    action_id : str
        Unique identifier for the action.

    source_path : str | Path
        Media file path relative to discovery root.

    target_path : str | Path
        Destination path relative to execution output root.

    source_root : str | Path
        Discovery root directory used to resolve absolute source paths.

    Returns
    -------
    PlanAction
        Schema-valid ``copy_media`` action.

    Raises
    ------
    ValueError
        If required parameters are missing.
    """

    # -------------------------------------------------------------------------
    # Validate
    # -------------------------------------------------------------------------

    if not action_id:
        raise ValueError("copy_media action requires action_id")

    if not source_path:
        raise ValueError("copy_media action requires source_path")

    if not target_path:
        raise ValueError("copy_media action requires target_path")

    if not source_root:
        raise ValueError("copy_media action requires source_root")

    # -------------------------------------------------------------------------
    # Normalize paths
    # -------------------------------------------------------------------------

    source_root = Path(source_root)

    source_abs = (source_root / Path(source_path)).resolve()
    target_rel = Path(target_path)

    LOGGER.debug(
        "Creating copy_media action id=%s source=%s target=%s",
        action_id,
        source_abs,
        target_rel,
    )

    # -------------------------------------------------------------------------
    # Declarative contract only
    # -------------------------------------------------------------------------

    return PlanAction(
        id=action_id,
        type="copy_media",
        parameters={
            "source_path": str(source_abs),
            "target_path": str(target_rel),
        },
    )