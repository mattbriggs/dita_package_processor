"""
Planning Action: inject_glossary

Declares the intent to inject glossary content into a target DITA topic.

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
    • touch filesystem
    • read XML
    • infer structure
    • mutate content

Planning ONLY describes intent.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List

from dita_package_processor.planning.models import PlanAction

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Factory
# =============================================================================


def inject_glossary_action(
    *,
    action_id: str,
    target_topic: Path | str,
    glossary_hrefs: Iterable[Path | str],
) -> PlanAction:
    """
    Create an ``inject_glossary`` planning action.

    Declares that glossary topic references should be injected into a
    target topic during execution.

    This function only records intent. It performs no I/O.

    Parameters
    ----------
    action_id : str
        Stable unique identifier for this action.

    target_topic : Path | str
        Path to the topic where glossary content will be injected.
        Must be relative to the package root.

    glossary_hrefs : Iterable[Path | str]
        Collection of glossary topic references to inject.

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
        raise ValueError("inject_glossary requires a non-empty action_id")

    if not target_topic:
        raise ValueError("inject_glossary requires target_topic")

    if glossary_hrefs is None:
        raise ValueError("inject_glossary requires glossary_hrefs")

    hrefs = list(glossary_hrefs)

    if not hrefs:
        raise ValueError("inject_glossary requires at least one glossary href")

    # -------------------------------------------------------------------------
    # Normalize
    # (planning must emit strings only)
    # -------------------------------------------------------------------------

    normalized_target = Path(target_topic).as_posix()

    normalized_hrefs: List[str] = []
    for href in hrefs:
        if not href:
            raise ValueError("Invalid glossary href: empty value")

        normalized_hrefs.append(Path(href).as_posix())

    LOGGER.debug(
        "Creating inject_glossary action id=%s target=%s glossary_count=%d",
        action_id,
        normalized_target,
        len(normalized_hrefs),
    )

    # -------------------------------------------------------------------------
    # Declarative contract only
    # -------------------------------------------------------------------------

    parameters: Dict[str, Any] = {
        "target_topic": normalized_target,
        "glossary_hrefs": normalized_hrefs,
    }

    return PlanAction(
        id=action_id,
        type="inject_glossary",
        target=normalized_target,
        parameters=parameters,
    )