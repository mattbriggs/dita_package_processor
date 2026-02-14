"""
Canonical DITA map and topic classification types.

This module defines the authoritative set of classifications used by the
DITA Package Processor during discovery, reporting, validation, and
transformation.

These types represent *observed structural intent*, not correctness.
Classification is descriptive, never prescriptive.

No parsing, inference, or transformation logic belongs in this module.
"""

from __future__ import annotations

from enum import Enum
from typing import Set


class ArtifactCategory(str, Enum):
    """
    High-level artifact categories recognized by the processor.

    Categories distinguish maps from topics and other filesystem
    artifacts during discovery and inventory construction.
    """

    MAP = "map"
    TOPIC = "topic"


class MapType(str, Enum):
    """
    Canonical DITA map classifications.

    MapType values are assigned during the Discovery phase based on
    observed structural patterns and explicit rules.

    A map may match multiple patterns during discovery, but must resolve
    to exactly one MapType before transformation.
    """

    #: The primary entry-point map for the package.
    MAIN = "main"

    #: A map providing abstract or overview content.
    ABSTRACT = "abstract"

    #: A map containing glossary or definition material.
    GLOSSARY = "glossary"

    #: A structural container map with no semantic content.
    CONTAINER = "container"

    #: A standard content-bearing map.
    CONTENT = "content"

    #: A map whose purpose could not be determined.
    UNKNOWN = "unknown"


class TopicType(str, Enum):
    """
    Canonical DITA topic classifications.

    TopicType values are derived from root element inspection and
    contextual usage within maps.
    """

    #: A glossary entry topic (<glossentry>).
    GLOSSARY = "glossary"

    #: A standard content topic (concept, task, reference, etc.).
    CONTENT = "content"

    #: A topic whose purpose could not be determined.
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Convenience sets
# ---------------------------------------------------------------------------

#: All recognized map types.
ALL_MAP_TYPES: Set[MapType] = set(MapType)

#: Map types that may legally appear more than once in a package.
MULTIPLE_ALLOWED_MAP_TYPES: Set[MapType] = {
    MapType.CONTENT,
    MapType.CONTAINER,
    MapType.UNKNOWN,
}

#: Map types that should be unique within a package.
UNIQUE_MAP_TYPES: Set[MapType] = {
    MapType.MAIN,
    MapType.ABSTRACT,
    MapType.GLOSSARY,
}

#: Map types that are considered non-fatal if missing.
OPTIONAL_MAP_TYPES: Set[MapType] = {
    MapType.ABSTRACT,
    MapType.GLOSSARY,
}

#: Map types that typically drive transformation logic.
EXECUTABLE_MAP_TYPES: Set[MapType] = {
    MapType.MAIN,
    MapType.CONTENT,
    MapType.ABSTRACT,
}