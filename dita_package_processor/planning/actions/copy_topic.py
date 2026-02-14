"""
copy_topic action definition.

Defines the PlanAction factory for copying a DITA topic from a source
location to a target location during execution.

IMPORTANT DESIGN RULE
---------------------
Planning must emit fully-qualified (absolute) source paths.

Execution must NEVER:
    - infer discovery roots
    - depend on cwd
    - guess filesystem context

Actions are declarative contracts only. They contain everything required
for execution to succeed without additional knowledge.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

from dita_package_processor.planning.models import PlanAction

logger = logging.getLogger(__name__)


# =============================================================================
# Factory
# =============================================================================


def create_copy_topic_action(
    *,
    action_id: str,
    source_path: Union[str, Path],
    target_path: Union[str, Path],
    source_root: Union[str, Path],
) -> PlanAction:
    """
    Create a PlanAction describing the intent to copy a DITA topic.

    The resulting action contains:
        • absolute source path (fully resolved)
        • target path relative to execution output root

    Execution therefore requires ZERO implicit context.

    Parameters
    ----------
    action_id : str
        Unique identifier for this action.

    source_path : str | Path
        Path to topic relative to discovery root.

    target_path : str | Path
        Output-relative path where file should be copied.

    source_root : str | Path
        Discovery root directory. Used to resolve absolute source.

    Returns
    -------
    PlanAction
        Schema-valid PlanAction of type ``copy_topic``.

    Raises
    ------
    ValueError
        If required values are missing.

    Examples
    --------
    source_root = "/repo/content"
    source_path = "topics/a.dita"

    -> stored source becomes:
       "/repo/content/topics/a.dita"
    """

    # -------------------------------------------------------------------------
    # Validate inputs
    # -------------------------------------------------------------------------

    if not action_id:
        raise ValueError("copy_topic action requires action_id")

    if not source_path:
        raise ValueError("copy_topic action requires source_path")

    if not target_path:
        raise ValueError("copy_topic action requires target_path")

    if not source_root:
        raise ValueError("copy_topic action requires source_root")

    # -------------------------------------------------------------------------
    # Normalize paths
    # -------------------------------------------------------------------------

    source_root = Path(source_root)
    source_abs = (source_root / Path(source_path)).resolve()

    target_rel = Path(target_path)

    logger.debug(
        "Creating copy_topic action id=%s source=%s target=%s",
        action_id,
        source_abs,
        target_rel,
    )

    # -------------------------------------------------------------------------
    # Return declarative action
    # -------------------------------------------------------------------------

    return PlanAction(
        id=action_id,
        type="copy_topic",
        parameters={
            # execution gets zero ambiguity
            "source_path": str(source_abs),
            "target_path": str(target_rel),
        },
    )