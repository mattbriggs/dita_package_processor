"""
Planning Action: extract_glossary

Declares the intent to extract glossary references from a definition map.

This action is:

    • declarative only
    • read-only
    • non-mutating
    • filesystem agnostic

Planning emits only normalized JSON-safe parameters.

Execution later performs:
    • file access
    • parsing
    • extraction

Design constraints
-----------------
Planning MUST NOT:
    • read files
    • parse XML
    • guess paths
    • mutate filesystem

Planning ONLY describes intent.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any

from dita_package_processor.planning.models import PlanAction

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Factory
# =============================================================================


def extract_glossary_action(
    *,
    action_id: str,
    definition_map: Path | str,
    definition_navtitle: str,
) -> PlanAction:
    """
    Create an ``extract_glossary`` planning action.

    This action declares that, during execution, the specified definition
    map should be inspected and glossary topic references identified
    beneath the provided navigation title.

    No parsing or filesystem access occurs at planning time.

    Parameters
    ----------
    action_id : str
        Stable unique identifier for this action.

    definition_map : Path | str
        Path to the definition DITA map, relative to the package root.

    definition_navtitle : str
        Navigation title identifying the glossary container node.

    Returns
    -------
    PlanAction
        JSON-serializable planning action.

    Raises
    ------
    ValueError
        If any parameter is missing or empty.
    """

    # -------------------------------------------------------------------------
    # Validate
    # -------------------------------------------------------------------------

    if not action_id:
        raise ValueError("extract_glossary requires a non-empty action_id")

    if not definition_map:
        raise ValueError("extract_glossary requires definition_map")

    if not definition_navtitle:
        raise ValueError("extract_glossary requires definition_navtitle")

    # -------------------------------------------------------------------------
    # Normalize paths to deterministic strings
    # -------------------------------------------------------------------------

    definition_path = Path(definition_map).as_posix()

    LOGGER.debug(
        "Creating extract_glossary action id=%s map=%s navtitle=%s",
        action_id,
        definition_path,
        definition_navtitle,
    )

    parameters: Dict[str, Any] = {
        "definition_map": definition_path,
        "definition_navtitle": definition_navtitle,
    }

    # -------------------------------------------------------------------------
    # Declarative contract only
    # -------------------------------------------------------------------------

    return PlanAction(
        id=action_id,
        type="extract_glossary",
        parameters=parameters,
    )