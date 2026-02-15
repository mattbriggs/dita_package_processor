"""
Canonical DITA artifact classification types.

This module defines the authoritative classification enums used during
discovery and planning.

Design Principles
-----------------
- Deterministic
- Explicit
- Stable string values
- No inference logic
- No transformation logic
- No mutation

These types represent observed structural intent only.
They do not imply correctness.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Set

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Artifact Category
# =============================================================================


class ArtifactCategory(str, Enum):
    """
    High-level artifact categories recognized by the processor.

    Categories distinguish maps, topics, and other structural artifacts
    during discovery and inventory construction.
    """

    MAP = "map"
    TOPIC = "topic"

    def __str__(self) -> str:
        """Return stable string value."""
        return self.value


# =============================================================================
# Map Classification
# =============================================================================


class MapType(str, Enum):
    """
    Canonical DITA map classifications.

    MapType values are assigned during discovery based on
    observed structural patterns.

    A map may match multiple patterns during discovery,
    but must resolve to exactly one MapType.
    """

    #: Primary entry-point map for the package.
    MAIN = "main"

    #: Overview or abstract map.
    ABSTRACT = "abstract"

    #: Glossary or definition map.
    GLOSSARY = "glossary"

    #: Structural container map.
    CONTAINER = "container"

    #: Standard content-bearing map.
    CONTENT = "content"

    #: Map whose purpose could not be determined.
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        """Return stable string value."""
        return self.value


# =============================================================================
# Topic Classification
# =============================================================================


class TopicType(str, Enum):
    """
    Canonical DITA topic classifications.

    TopicType values are derived from root element inspection
    and contextual usage.
    """

    #: Glossary entry topic.
    GLOSSARY = "glossary"

    #: Standard content topic.
    CONTENT = "content"

    #: Topic whose purpose could not be determined.
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        """Return stable string value."""
        return self.value


# =============================================================================
# Convenience Sets
# =============================================================================


#: All recognized map types.
ALL_MAP_TYPES: Set[MapType] = set(MapType)

#: Map types that may legally appear more than once.
MULTIPLE_ALLOWED_MAP_TYPES: Set[MapType] = {
    MapType.CONTENT,
    MapType.CONTAINER,
    MapType.UNKNOWN,
}

#: Map types that must be unique within a package.
UNIQUE_MAP_TYPES: Set[MapType] = {
    MapType.MAIN,
    MapType.ABSTRACT,
    MapType.GLOSSARY,
}

#: Map types that are optional.
OPTIONAL_MAP_TYPES: Set[MapType] = {
    MapType.ABSTRACT,
    MapType.GLOSSARY,
}

#: Map types that typically drive transformation.
EXECUTABLE_MAP_TYPES: Set[MapType] = {
    MapType.MAIN,
    MapType.CONTENT,
    MapType.ABSTRACT,
}