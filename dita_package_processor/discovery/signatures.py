"""
Structural signature extraction for DITA discovery.

This module defines *signatures*: normalized, comparable observations
derived from DITA XML structure. Signatures are pure data summaries and
contain no classification logic.

Signatures exist to separate:

- observation (what is present)
- interpretation (what it means)

They are stable, testable, and safe to evolve independently.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set

from lxml import etree

from dita_package_processor.dita_xml import read_xml

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# XML utilities
# ---------------------------------------------------------------------------


def _xpath(root: etree._Element, expr: str):
    """
    Execute an XPath expression with namespace-agnostic matching.

    This allows matching on local-name() so default namespaces
    do not break discovery.
    """
    if expr.startswith(".//"):
        tag = expr.replace(".//", "")
        return root.xpath(f".//*[local-name()='{tag}']")
    return root.xpath(expr)


# ---------------------------------------------------------------------------
# Simple structural predicates
# ---------------------------------------------------------------------------


def has_topicrefs(root: etree._Element) -> bool:
    """
    Return ``True`` if the XML element contains any ``<topicref>`` elements.
    """
    result = bool(_xpath(root, ".//topicref"))
    LOGGER.debug("has_topicrefs=%s", result)
    return result


def has_maprefs(root: etree._Element) -> bool:
    """
    Return ``True`` if the XML element contains any ``<mapref>`` elements.
    """
    result = bool(_xpath(root, ".//mapref"))
    LOGGER.debug("has_maprefs=%s", result)
    return result


def has_title(root: etree._Element) -> bool:
    """
    Return ``True`` if the XML element contains a ``<title>`` element.
    """
    result = bool(_xpath(root, ".//title"))
    LOGGER.debug("has_title=%s", result)
    return result


# ---------------------------------------------------------------------------
# Signature models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MapSignature:
    """
    Structural signature extracted from a DITA map.

    This signature captures *what the map contains*, not what it
    represents or how it should be classified.
    """

    filename: str
    title: Optional[str]

    topicref_count: int
    mapref_count: int
    topicref_with_href_count: int

    referenced_extensions: Set[str]

    references_maps: bool
    references_topics: bool


@dataclass(frozen=True)
class TopicSignature:
    """
    Structural signature extracted from a DITA topic.
    """

    filename: str
    root_element: str
    title: Optional[str]

    has_shortdesc: bool
    has_body: bool
    paragraph_count: int


# ---------------------------------------------------------------------------
# Signature extraction
# ---------------------------------------------------------------------------


def extract_map_signature(map_path: Path) -> MapSignature:
    """
    Extract a structural signature from a DITA map.

    Extraction failures are non-fatal and result in partial signatures.
    """
    LOGGER.debug("Extracting map signature from %s", map_path)

    title: Optional[str] = None
    topicref_count = 0
    mapref_count = 0
    topicref_with_href_count = 0
    referenced_extensions: Set[str] = set()

    try:
        doc = read_xml(map_path)
        root = doc.root

        # Title
        title_nodes = _xpath(root, ".//title")
        if title_nodes:
            text = (title_nodes[0].text or "").strip()
            if text:
                title = text
                LOGGER.debug("Map title detected: %s", title)

        topicrefs = _xpath(root, ".//topicref")
        maprefs = _xpath(root, ".//mapref")

        topicref_count = len(topicrefs)
        mapref_count = len(maprefs)

        LOGGER.debug(
            "Map %s: topicrefs=%d maprefs=%d",
            map_path.name,
            topicref_count,
            mapref_count,
        )

        for ref in topicrefs:
            href = ref.get("href")
            if href:
                topicref_with_href_count += 1
                ext = Path(href).suffix.lower()
                if ext:
                    referenced_extensions.add(ext)

        for ref in maprefs:
            href = ref.get("href")
            if href:
                ext = Path(href).suffix.lower()
                if ext:
                    referenced_extensions.add(ext)

        LOGGER.debug(
            "Map %s referenced extensions: %s",
            map_path.name,
            referenced_extensions,
        )

    except Exception as exc:  # noqa: BLE001
        LOGGER.debug(
            "Failed to fully extract map signature from %s: %s",
            map_path,
            exc,
        )

    signature = MapSignature(
        filename=map_path.name,
        title=title,
        topicref_count=topicref_count,
        mapref_count=mapref_count,
        topicref_with_href_count=topicref_with_href_count,
        referenced_extensions=referenced_extensions,
        references_maps=".ditamap" in referenced_extensions,
        references_topics=".dita" in referenced_extensions,
    )

    LOGGER.debug("MapSignature created: %s", signature)
    return signature


def extract_topic_signature(topic_path: Path) -> TopicSignature:
    """
    Extract a structural signature from a DITA topic.

    Extraction failures are non-fatal and result in partial signatures.
    """
    LOGGER.debug("Extracting topic signature from %s", topic_path)

    title: Optional[str] = None
    root_element = "unknown"
    has_shortdesc = False
    has_body = False
    paragraph_count = 0

    try:
        doc = read_xml(topic_path)
        root = doc.root

        root_element = etree.QName(root).localname.lower()
        LOGGER.debug("Root element detected: %s", root_element)

        title_nodes = _xpath(root, ".//title")
        if title_nodes:
            text = (title_nodes[0].text or "").strip()
            if text:
                title = text
                LOGGER.debug("Topic title detected: %s", title)

        has_shortdesc = bool(_xpath(root, ".//shortdesc"))
        body_nodes = _xpath(root, ".//body")
        has_body = bool(body_nodes)

        if body_nodes:
            paragraph_count = len(_xpath(body_nodes[0], ".//p"))

        LOGGER.debug(
            "Topic %s structure: has_shortdesc=%s, has_body=%s, paragraph_count=%d",
            topic_path.name,
            has_shortdesc,
            has_body,
            paragraph_count,
        )

    except Exception as exc:  # noqa: BLE001
        LOGGER.debug(
            "Failed to fully extract topic signature from %s: %s",
            topic_path,
            exc,
        )

    signature = TopicSignature(
        filename=topic_path.name,
        root_element=root_element,
        title=title,
        has_shortdesc=has_shortdesc,
        has_body=has_body,
        paragraph_count=paragraph_count,
    )

    LOGGER.debug("TopicSignature created: %s", signature)
    return signature