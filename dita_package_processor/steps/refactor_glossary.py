"""
Step to refactor definition topics into glossentry topics.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

from lxml import etree

from dita_package_processor.context import ProcessingContext
from dita_package_processor.dita_xml import (
    XmlDocument,
    read_xml,
    transform_to_glossentry,
    write_xml,
)
from dita_package_processor.steps.base import ProcessingStep


class RefactorGlossaryStep(ProcessingStep):
    """
    Refactor definition topics into DITA ``glossentry`` topics.

    This step locates a configured definition map, finds a ``topicref``
    node matching a given navtitle, and transforms each referenced topic
    into a ``<glossentry>`` in place.

    All failures in this step are **non-fatal by contract**. Missing or
    malformed inputs result in warnings and early return.
    """

    #: Canonical step name used for registration.
    name = "refactor-glossary"

    def _find_definition_node(
        self,
        map_root: etree._Element,
        navtitle: str,
    ) -> Optional[etree._Element]:
        """
        Locate the definition ``topicref`` node by navtitle.

        The navtitle may be specified either as a ``<topicmeta><navtitle>``
        element or as a ``@navtitle`` attribute.

        Matching is case-insensitive.

        :param map_root: Root element of the definition map.
        :param navtitle: Navtitle value to match.
        :return: Matching ``topicref`` element, or ``None``.
        """
        wanted = navtitle.strip().lower()

        for node in map_root.xpath(".//topicref"):
            nav_text = ""

            nav_el = node.find("./topicmeta/navtitle")
            if nav_el is not None and nav_el.text:
                nav_text = nav_el.text.strip()
            elif node.get("navtitle"):
                nav_text = node.get("navtitle", "").strip()

            if nav_text.lower() == wanted:
                return node

        return None

    def run(self, context: ProcessingContext, logger: logging.Logger) -> None:
        """
        Execute glossary refactoring.

        This method never raises exceptions. All error conditions are
        logged and treated as non-fatal.
        """
        # ------------------------------------------------------------------
        # Configuration checks
        # ------------------------------------------------------------------
        if not context.definition_map_name:
            logger.info(
                "No definition map configured; skipping glossary refactor."
            )
            return

        def_map_path = context.package_dir / context.definition_map_name
        if not def_map_path.exists():
            message = (
                "Definition map not found; skipping glossary refactor: "
                f"{def_map_path.name}"
            )
            logger.warning(message)
            print(message, file=sys.stderr)
            return

        # ------------------------------------------------------------------
        # Load definition map
        # ------------------------------------------------------------------
        try:
            def_map_doc = read_xml(def_map_path)
            map_root = def_map_doc.root
        except Exception as exc:  # noqa: BLE001
            message = (
                "Failed to read definition map; skipping glossary refactor: "
                f"{def_map_path.name} ({exc})"
            )
            logger.warning(message)
            print(message, file=sys.stderr)
            return

        # ------------------------------------------------------------------
        # Locate definition node
        # ------------------------------------------------------------------
        def_node = self._find_definition_node(
            map_root,
            context.definition_navtitle,
        )

        if def_node is None:
            message = (
                "Definition navtitle not found in "
                f"{def_map_path.name}: {context.definition_navtitle}"
            )
            logger.warning(message)
            print(message, file=sys.stderr)
            return

        # ------------------------------------------------------------------
        # Process child topicrefs
        # ------------------------------------------------------------------
        topicrefs = def_node.xpath("./topicref[@href]")
        logger.info(
            "Found %d definition topicrefs.",
            len(topicrefs),
        )

        for topicref in topicrefs:
            href = topicref.get("href")
            if not href:
                continue

            topic_path = (context.package_dir / href).resolve()
            if not topic_path.exists():
                logger.warning(
                    "Definition topic missing; skipping: %s",
                    topic_path,
                )
                continue

            try:
                topic_doc = read_xml(topic_path)
                gloss_doc = transform_to_glossentry(topic_doc)
                assert isinstance(gloss_doc, XmlDocument)
                write_xml(gloss_doc, topic_path)

                logger.info(
                    "Refactored definition topic to glossentry: %s",
                    topic_path.name,
                )

            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to refactor definition topic %s: %s",
                    topic_path.name,
                    exc,
                )
                continue