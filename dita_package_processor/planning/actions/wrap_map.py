"""
Planning Action: wrap_map

Declares the intent to wrap all top-level <topicref> elements of a DITA map
under a generated wrapper topic.

This action:

    • is declarative only
    • performs no filesystem mutation
    • performs no XML parsing
    • performs no directory creation
    • performs no idempotency checks
    • emits JSON-safe parameters only

All structural work happens later in the execution layer.

Design constraints
-----------------
Planning MUST NOT:
    • inspect filesystem
    • parse XML
    • create topics
    • rewrite maps
    • mutate anything

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


def create_wrap_map_action(
    *,
    action_id: str,
    source_map: Path | str,
    wrapper_topic_path: Path | str,
    title: str,
) -> PlanAction:
    """
    Create a ``wrap_map`` planning action.

    Declares that during execution:

        1. A wrapper topic should be created (if needed)
        2. All top-level topicrefs in the map should be nested beneath it

    This function performs zero filesystem or XML operations.

    Parameters
    ----------
    action_id : str
        Stable unique identifier.

    source_map : Path | str
        Path to the DITA map to wrap (relative to package root).

    wrapper_topic_path : Path | str
        Path where the wrapper topic will be created.

    title : str
        Title text for the wrapper topic.

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
        raise ValueError("wrap_map requires a non-empty action_id")

    if not source_map:
        raise ValueError("wrap_map requires source_map")

    if not wrapper_topic_path:
        raise ValueError("wrap_map requires wrapper_topic_path")

    if not isinstance(title, str) or not title.strip():
        raise ValueError("wrap_map requires non-empty title")

    # -------------------------------------------------------------------------
    # Normalize (planning emits strings only)
    # -------------------------------------------------------------------------

    normalized_source = Path(source_map).as_posix()
    normalized_wrapper = Path(wrapper_topic_path).as_posix()

    LOGGER.debug(
        "Creating wrap_map action id=%s source=%s wrapper=%s",
        action_id,
        normalized_source,
        normalized_wrapper,
    )

    parameters: Dict[str, Any] = {
        "source_map": normalized_source,
        "wrapper_topic_path": normalized_wrapper,
        "title": title,
    }

    # -------------------------------------------------------------------------
    # Declarative contract only
    # -------------------------------------------------------------------------

    return PlanAction(
        id=action_id,
        type="wrap_map",
        target=normalized_source,
        parameters=parameters,
    )