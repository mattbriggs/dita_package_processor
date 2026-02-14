"""
Map reference extractor.

This module extracts structural dependency edges from DITA map files
(`.ditamap`). It performs no interpretation and no inference. It records
only explicit, syntactic references found in XML.

Handled elements:
- <mapref href="...">   → map → map
- <topicref href="..."> → map → topic

Single responsibility:
    Input:  Path to a .ditamap file
    Output: List of DependencyEdge objects

This module is deterministic, read-only, and schema-bound.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List

from dita_package_processor.discovery.graph import DependencyEdge

LOGGER = logging.getLogger(__name__)

MAPREF_TAGS = {"mapref"}
TOPICREF_TAGS = {"topicref"}


def extract_map_references(
    map_path: Path,
    *,
    pattern_id_mapref: str = "dita_map_mapref",
    pattern_id_topicref: str = "dita_map_topicref",
) -> List[DependencyEdge]:
    """
    Extract dependency edges from a DITA map file.

    Each discovered reference produces a schema-valid DependencyEdge with:
    - source
    - target
    - edge_type
    - pattern_id

    :param map_path: Path to the `.ditamap` file.
    :param pattern_id_mapref: Pattern ID used for `<mapref>` edges.
    :param pattern_id_topicref: Pattern ID used for `<topicref>` edges.
    :return: List of DependencyEdge objects.
    :raises FileNotFoundError: If the map file does not exist.
    :raises ValueError: If the XML cannot be parsed.
    """
    LOGGER.info("Starting map reference extraction: %s", map_path)

    if not map_path.exists():
        LOGGER.error("Map file does not exist: %s", map_path)
        raise FileNotFoundError(f"Map file not found: {map_path}")

    try:
        tree = ET.parse(map_path)
    except ET.ParseError as exc:
        LOGGER.error("Failed to parse XML in map file: %s", map_path)
        raise ValueError(f"Invalid XML in map file: {map_path}") from exc

    root = tree.getroot()
    edges: List[DependencyEdge] = []

    source = map_path.as_posix()

    for elem in root.iter():
        tag = _strip_namespace(elem.tag)
        href = elem.attrib.get("href")

        if not href:
            continue

        if tag in MAPREF_TAGS:
            edge = DependencyEdge(
                source=source,
                target=href,
                edge_type="mapref",
                pattern_id=pattern_id_mapref,
            )
            edges.append(edge)
            LOGGER.debug("Extracted mapref edge: %s", edge)

        elif tag in TOPICREF_TAGS:
            edge = DependencyEdge(
                source=source,
                target=href,
                edge_type="topicref",
                pattern_id=pattern_id_topicref,
            )
            edges.append(edge)
            LOGGER.debug("Extracted topicref edge: %s", edge)

    LOGGER.info(
        "Completed map reference extraction for %s: %d edges found",
        map_path,
        len(edges),
    )

    return edges


def _strip_namespace(tag: str) -> str:
    """
    Remove XML namespace from a tag if present.

    Example:
        "{http://dita.oasis-open.org/architecture/2005/}mapref"
        → "mapref"

    :param tag: Raw XML tag name.
    :return: Tag name without namespace.
    """
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag