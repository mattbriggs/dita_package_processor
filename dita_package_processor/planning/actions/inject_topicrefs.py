"""
Planning Action: inject_topicrefs

Declares the intent to inject multiple <topicref> elements from one DITA map
into another.

This action:

    • is declarative only
    • performs no filesystem access
    • performs no XML parsing
    • performs no mutation
    • emits only JSON-safe data

Execution later performs the actual injection.

Design constraints
-----------------
Planning MUST NOT:
    • read files
    • parse XML
    • mutate content
    • inspect filesystem state

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


def create_inject_topicrefs_action(
    *,
    action_id: str,
    source_map: Path | str,
    target_map: Path | str,
) -> PlanAction:
    """
    Create an ``inject_topicrefs`` planning action.

    Declares that all eligible <topicref> elements from ``source_map`` should
    be injected into ``target_map`` during execution.

    This function performs no filesystem or XML operations. It only
    validates and normalizes parameters into a JSON-safe structure.

    Parameters
    ----------
    action_id : str
        Stable unique identifier for this action.

    source_map : Path | str
        Path to the source DITA map (relative to package root).

    target_map : Path | str
        Path to the target DITA map.

    Returns
    -------
    PlanAction
        JSON-serializable planning action.

    Raises
    ------
    ValueError
        If any parameter is invalid.
    """

    # -------------------------------------------------------------------------
    # Validate
    # -------------------------------------------------------------------------

    if not action_id:
        raise ValueError("inject_topicrefs requires a non-empty action_id")

    if not source_map:
        raise ValueError("inject_topicrefs requires source_map")

    if not target_map:
        raise ValueError("inject_topicrefs requires target_map")

    # -------------------------------------------------------------------------
    # Normalize (planning emits strings only)
    # -------------------------------------------------------------------------

    normalized_source = Path(source_map).as_posix()
    normalized_target = Path(target_map).as_posix()

    LOGGER.debug(
        "Creating inject_topicrefs action id=%s source=%s target=%s",
        action_id,
        normalized_source,
        normalized_target,
    )

    parameters: Dict[str, Any] = {
        "source_map": normalized_source,
        "target_map": normalized_target,
    }

    # -------------------------------------------------------------------------
    # Declarative contract only
    # -------------------------------------------------------------------------

    return PlanAction(
        id=action_id,
        type="inject_topicrefs",
        target=normalized_target,
        parameters=parameters,
    )