"""
Topic reference extractor.

This module extracts dependency edges from DITA topic files (.dita).
It records only explicit structural relationships and performs no
interpretation or inference.

Handled elements:
- <xref href="...">
- <image href="...">
- <object data="...">

Single responsibility:
    Input:  path to a .dita topic file
    Output: list of DependencyEdge objects

This module does not modify XML, infer intent, or decide execution behavior.
It only records observed dependencies.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List

from dita_package_processor.discovery.graph import DependencyEdge

LOGGER = logging.getLogger(__name__)

XREF_TAGS = {"xref"}
IMAGE_TAGS = {"image"}
OBJECT_TAGS = {"object"}


def extract_topic_references(
    topic_path: Path,
    *,
    pattern_id_xref: str = "dita_topic_xref",
    pattern_id_image: str = "dita_topic_image",
    pattern_id_object: str = "dita_topic_object",
) -> List[DependencyEdge]:
    """
    Extract dependency edges from a DITA topic file.

    :param topic_path: Path to a .dita topic file.
    :param pattern_id_xref: Pattern ID used for <xref> edges.
    :param pattern_id_image: Pattern ID used for <image> edges.
    :param pattern_id_object: Pattern ID used for <object> edges.
    :return: List of DependencyEdge objects.
    :raises FileNotFoundError: If the topic file does not exist.
    :raises ValueError: If the XML cannot be parsed.
    """
    LOGGER.info("Starting topic reference extraction: %s", topic_path)

    if not topic_path.exists():
        LOGGER.error("Topic file does not exist: %s", topic_path)
        raise FileNotFoundError(f"Topic file not found: {topic_path}")

    try:
        tree = ET.parse(topic_path)
    except ET.ParseError as exc:
        LOGGER.error("Failed to parse XML in topic file: %s", topic_path)
        raise ValueError(f"Invalid XML in topic file: {topic_path}") from exc

    root = tree.getroot()
    edges: List[DependencyEdge] = []

    source = topic_path.as_posix()

    for elem in root.iter():
        tag = _strip_namespace(elem.tag)

        # -------------------- XREF --------------------
        if tag in XREF_TAGS:
            href = elem.attrib.get("href")
            if href:
                edges.append(
                    DependencyEdge(
                        source=source,
                        target=href,
                        edge_type="xref",
                        pattern_id=pattern_id_xref,
                    )
                )

        # -------------------- IMAGE --------------------
        elif tag in IMAGE_TAGS:
            href = elem.attrib.get("href")
            if href:
                edges.append(
                    DependencyEdge(
                        source=source,
                        target=href,
                        edge_type="image",
                        pattern_id=pattern_id_image,
                    )
                )

        # -------------------- OBJECT --------------------
        elif tag in OBJECT_TAGS:
            data = elem.attrib.get("data")
            if data:
                edges.append(
                    DependencyEdge(
                        source=source,
                        target=data,
                        edge_type="object",
                        pattern_id=pattern_id_object,
                    )
                )

    LOGGER.info(
        "Completed topic reference extraction for %s: %d edges found",
        topic_path,
        len(edges),
    )

    return edges


def _strip_namespace(tag: str) -> str:
    """
    Remove XML namespace from a tag if present.

    Example:
        "{http://dita.oasis-open.org/architecture/2005/}xref"
        -> "xref"

    :param tag: Raw XML tag name.
    :return: Tag name without namespace.
    """
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag