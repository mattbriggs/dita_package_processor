"""
DITA XML helper utilities built on top of lxml.

This module provides a small, opinionated set of helpers for reading,
writing, and transforming DITA XML safely and consistently.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

from lxml import etree


#: Shared XML parser configuration for all DITA XML operations.
XML_PARSER = etree.XMLParser(
    remove_blank_text=False,
    resolve_entities=False,
    no_network=True,
    recover=True,
)


@dataclass
class XmlDocument:
    """
    Representation of an XML document on disk.

    This class couples an ``lxml`` ElementTree with its filesystem path
    and provides convenience access to the document root.
    """

    #: Path to the XML file on disk.
    path: Path

    #: Parsed XML tree.
    tree: etree._ElementTree

    @property
    def root(self) -> etree._Element:
        """
        Return the root XML element.

        :return: Root element of the document.
        """
        return self.tree.getroot()


def read_xml(path: Path) -> XmlDocument:
    """
    Read and parse an XML file from disk.

    :param path: Path to the XML file.
    :return: Parsed ``XmlDocument`` instance.
    """
    tree = etree.parse(str(path), parser=XML_PARSER)
    return XmlDocument(path=path, tree=tree)


def write_xml(doc: XmlDocument, path: Optional[Path] = None) -> None:
    """
    Write an XML document back to disk.

    :param doc: ``XmlDocument`` to write.
    :param path: Optional destination path. Defaults to ``doc.path``.
    """
    output_path = path if path is not None else doc.path

    doc.tree.write(
        str(output_path),
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=True,
    )


def first_href_to_map(doc: XmlDocument) -> Optional[str]:
    """
    Find the first ``href`` pointing to a ``.ditamap`` file.

    Intended for resolving the main map referenced by ``index.ditamap``.

    :param doc: Index map document.
    :return: ``href`` value if found, otherwise ``None``.
    """
    for node in doc.root.xpath(".//*[@href]"):
        href = node.get("href", "")
        if href.lower().endswith(".ditamap"):
            return href

    return None


def get_map_title(doc: XmlDocument) -> str:
    """
    Extract a human-readable map title.

    Title resolution order:
    1. ``<title>``
    2. ``<topicmeta><navtitle>``

    :param doc: Map XML document.
    :return: Title text, or an empty string if not found.
    """
    title_el = doc.root.find(".//title")
    if title_el is not None and (title_el.text or "").strip():
        return (title_el.text or "").strip()

    nav_el = doc.root.find(".//topicmeta/navtitle")
    if nav_el is not None and (nav_el.text or "").strip():
        return (nav_el.text or "").strip()

    return ""


def get_top_level_topicrefs(
    doc: XmlDocument,
) -> List[etree._Element]:
    """
    Return direct child ``topicref`` or ``mapref`` elements of a map.

    :param doc: Map XML document.
    :return: List of top-level topicref/mapref elements.
    """
    results: List[etree._Element] = []

    for child in doc.root:
        tag_name = etree.QName(child).localname
        if tag_name in {"topicref", "mapref"}:
            results.append(child)

    return results


def find_first_topicref_href(doc: XmlDocument) -> Optional[str]:
    """
    Find the first ``topicref`` element with an ``href`` attribute.

    :param doc: Map XML document.
    :return: ``href`` value if found, otherwise ``None``.
    """
    node = doc.root.find(".//topicref[@href]")
    if node is None:
        return None

    return node.get("href")


def create_concept_topic_xml(
    path: Path,
    topic_id: str,
    title: str,
) -> XmlDocument:
    """
    Create a minimal DITA ``concept`` topic XML document.

    :param path: Destination file path for the topic.
    :param topic_id: Value for the ``id`` attribute.
    :param title: Topic title text.
    :return: New ``XmlDocument`` instance.
    """
    concept = etree.Element("concept", id=topic_id)

    title_el = etree.SubElement(concept, "title")
    title_el.text = title

    conbody = etree.SubElement(concept, "conbody")
    paragraph = etree.SubElement(conbody, "p")
    paragraph.text = ""

    tree = etree.ElementTree(concept)
    return XmlDocument(path=path, tree=tree)


def transform_to_glossentry(doc: XmlDocument) -> XmlDocument:
    """
    Transform a topic into a minimal ``glossentry`` topic in place.

    Heuristic mapping rules:
    - ``glossentry/@id``: existing topic ``@id`` (fallback: ``gloss``)
    - ``glossterm``: existing ``<title>``
    - ``glossdef/p``: derived from ``<shortdesc>`` or body text

    :param doc: Topic XML document to transform.
    :return: Updated ``XmlDocument`` instance.
    """
    root = doc.root

    topic_id = root.get("id") or "gloss"

    title_el = root.find(".//title")
    title_text = (
        (title_el.text or "").strip()
        if title_el is not None
        else "Term"
    )

    # Derive definition content
    shortdesc = root.find(".//shortdesc")
    body = root.find(".//conbody")
    if body is None:
        body = root.find(".//body")

    content_text = ""

    if shortdesc is not None and (shortdesc.text or "").strip():
        content_text = (shortdesc.text or "").strip()
    elif body is not None:
        content_text = " ".join(
            text.strip()
            for text in body.itertext()
            if text.strip()
        )[:1000]

    glossentry = etree.Element("glossentry", id=topic_id)

    glossterm = etree.SubElement(glossentry, "glossterm")
    glossterm.text = title_text

    glossdef = etree.SubElement(glossentry, "glossdef")
    paragraph = etree.SubElement(glossdef, "p")
    paragraph.text = content_text

    doc.tree = etree.ElementTree(glossentry)
    return doc