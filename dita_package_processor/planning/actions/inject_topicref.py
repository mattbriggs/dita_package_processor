"""
Planning Action: inject_topicref

Declares the intent to inject a single <topicref> element into a DITA map.

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
    • infer structure

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


def inject_topicref_action(
    *,
    action_id: str,
    target_map: Path | str,
    href: Path | str,
) -> PlanAction:
    """
    Create an ``inject_topicref`` planning action.

    Declares that a <topicref> should be injected into a target DITA map
    during execution.

    This function performs no filesystem or XML operations. It only
    validates and normalizes parameters into a JSON-safe structure.

    Parameters
    ----------
    action_id : str
        Stable unique identifier for this action.

    target_map : Path | str
        Path to the DITA map that will receive the topicref.
        Must be relative to the package root.

    href : Path | str
        HREF value for the <topicref> element.

    Returns
    -------
    PlanAction
        JSON-serializable planning action.

    Raises
    ------
    ValueError
        If any parameter is invalid or empty.
    """

    # -------------------------------------------------------------------------
    # Validate
    # -------------------------------------------------------------------------

    if not action_id:
        raise ValueError("inject_topicref requires a non-empty action_id")

    if not target_map:
        raise ValueError("inject_topicref requires target_map")

    if not href:
        raise ValueError("inject_topicref requires href")

    # -------------------------------------------------------------------------
    # Normalize (planning emits strings only)
    # -------------------------------------------------------------------------

    normalized_target = Path(target_map).as_posix()
    normalized_href = Path(href).as_posix()

    LOGGER.debug(
        "Creating inject_topicref action id=%s target=%s href=%s",
        action_id,
        normalized_target,
        normalized_href,
    )

    # -------------------------------------------------------------------------
    # Declarative contract only
    # -------------------------------------------------------------------------

    parameters: Dict[str, Any] = {
        "href": normalized_href,
    }

    return PlanAction(
        id=action_id,
        type="inject_topicref",
        target=normalized_target,
        parameters=parameters,
    )