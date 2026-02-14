"""
Relationship extraction for DITA discovery.

This module extracts explicit, syntactic relationships between already-
discovered artifacts by parsing DITA XML files.

It does NOT:
- classify artifacts
- mutate files
- infer semantic intent

It ONLY records factual dependencies expressed in XML:

- map → topic via <topicref>
- map → map via <mapref>
- topic → media via <image>, <object>, <xref>

All emitted relationships conform strictly to the discovery schema:

{
  "source": "<package-relative path>",
  "target": "<package-relative path>",
  "type": "<relationship type>",
  "pattern_id": "<discovery pattern identifier>"
}
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List
from xml.etree import ElementTree as ET

LOGGER = logging.getLogger(__name__)


class RelationshipExtractor:
    """
    Extracts structural relationships between DITA artifacts by parsing XML.

    This extractor is purely syntactic and observational.
    It assumes:
    - Artifacts have already been discovered
    - Paths are package-relative
    - Files are valid XML
    """

    def __init__(self, package_root: Path) -> None:
        """
        :param package_root: Root directory of the DITA package.
        """
        self.package_root = package_root.resolve()
        LOGGER.debug(
            "RelationshipExtractor initialized (package_root=%s)",
            self.package_root,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, artifacts: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Extract relationships from a set of discovered artifacts.

        :param artifacts: List of discovery artifact dictionaries.
        :return: List of relationship dictionaries conforming to schema.
        """
        LOGGER.info(
            "Extracting relationships from %d artifacts",
            len(artifacts),
        )

        relationships: List[Dict[str, str]] = []

        for artifact in artifacts:
            artifact_type = artifact["artifact_type"]
            path = self.package_root / artifact["path"]

            if not path.exists():
                LOGGER.warning(
                    "Artifact path does not exist; skipping: %s",
                    path,
                )
                continue

            if artifact_type == "map":
                relationships.extend(self._extract_from_map(path))
            elif artifact_type == "topic":
                relationships.extend(self._extract_from_topic(path))
            else:
                LOGGER.debug(
                    "Artifact type '%s' has no relationships: %s",
                    artifact_type,
                    path,
                )

        LOGGER.info(
            "Relationship extraction complete: %d relationships found",
            len(relationships),
        )
        return relationships

    # ------------------------------------------------------------------
    # Map parsing
    # ------------------------------------------------------------------

    def _extract_from_map(self, path: Path) -> List[Dict[str, str]]:
        """Extract topicref and mapref relationships from a .ditamap file."""
        LOGGER.debug("Parsing map for relationships: %s", path)

        tree = ET.parse(path)
        root = tree.getroot()

        rels: List[Dict[str, str]] = []

        for elem in root.iter():
            tag = self._strip_ns(elem.tag)

            if tag == "topicref":
                href = elem.attrib.get("href")
                if href:
                    edge = self._make_edge(
                        source=path,
                        target=href,
                        rel_type="topicref",
                        pattern_id="dita_map_topicref",
                    )
                    if edge:
                        rels.append(edge)

            elif tag == "mapref":
                href = elem.attrib.get("href")
                if href:
                    edge = self._make_edge(
                        source=path,
                        target=href,
                        rel_type="mapref",
                        pattern_id="dita_map_mapref",
                    )
                    if edge:
                        rels.append(edge)

        LOGGER.debug(
            "Extracted %d relationships from map %s",
            len(rels),
            path,
        )
        return rels

    # ------------------------------------------------------------------
    # Topic parsing
    # ------------------------------------------------------------------

    def _extract_from_topic(self, path: Path) -> List[Dict[str, str]]:
        """Extract media relationships from a .dita topic file."""
        LOGGER.debug("Parsing topic for relationships: %s", path)

        tree = ET.parse(path)
        root = tree.getroot()

        rels: List[Dict[str, str]] = []

        for elem in root.iter():
            tag = self._strip_ns(elem.tag)

            if tag in {"image", "object", "xref"}:
                href = elem.attrib.get("href")
                if href:
                    edge = self._make_edge(
                        source=path,
                        target=href,
                        rel_type=tag,
                        pattern_id=f"dita_topic_{tag}",
                    )
                    if edge:
                        rels.append(edge)

        LOGGER.debug(
            "Extracted %d relationships from topic %s",
            len(rels),
            path,
        )
        return rels

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _make_edge(
        self,
        *,
        source: Path,
        target: str,
        rel_type: str,
        pattern_id: str,
    ) -> Dict[str, str] | None:
        """
        Normalize and create a relationship edge.

        Rules:
        - Strip fragment identifiers (#id)
        - Ignore same-file fragment-only links
        - Ignore external URLs (http/https/mailto/ftp)
        - Only file-level dependencies belong in discovery graph
        - Skip anything escaping package root
        """

        source_rel = source.relative_to(self.package_root)

        # ------------------------------------------------------
        # Strip fragments
        # ------------------------------------------------------
        target_file = target.split("#", 1)[0]

        # ------------------------------------------------------
        # Skip fragment-only anchors (#foo)
        # ------------------------------------------------------
        if not target_file:
            LOGGER.debug(
                "Skipping intra-file relationship (fragment only): source=%s target=%s",
                source,
                target,
            )
            return None

        # ------------------------------------------------------
        # Skip external URLs
        # ------------------------------------------------------
        lower = target_file.lower()
        if lower.startswith(("http://", "https://", "mailto:", "ftp://")):
            LOGGER.debug(
                "Skipping external relationship target: source=%s target=%s",
                source,
                target,
            )
            return None

        # ------------------------------------------------------
        # Resolve only internal paths
        # ------------------------------------------------------
        try:
            target_path = (source.parent / target_file).resolve()
            target_rel = target_path.relative_to(self.package_root)
        except ValueError:
            LOGGER.debug(
                "Relationship target escapes package root; skipping. "
                "source=%s target=%s",
                source,
                target,
            )
            return None

        edge = {
            "source": source_rel.as_posix(),
            "target": target_rel.as_posix(),
            "type": rel_type,
            "pattern_id": pattern_id,
        }

        LOGGER.debug("Extracted relationship: %s", edge)
        return edge

    @staticmethod
    def _strip_ns(tag: str) -> str:
        """Remove XML namespace from a tag."""
        return tag.split("}")[-1]