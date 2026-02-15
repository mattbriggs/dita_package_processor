"""
Filesystem and XML scanner for DITA package discovery.

This module performs strictly read-only inspection of a DITA package
directory and produces a DiscoveryInventory.

Responsibilities
----------------
- Identify maps, topics, and media artifacts
- Extract shallow metadata
- Perform classification via classifier modules
- Extract relationships
- Build dependency graph
- Annotate structural weight (node_count)
- Resolve a single deterministic MAIN map

This module does NOT:
- Infer intent beyond structural evidence
- Modify files
- Perform planning
"""

from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path
from typing import Dict, Set

from lxml import etree

from dita_package_processor.dita_xml import read_xml
from dita_package_processor.discovery.classifiers import (
    classify_map,
    classify_topic,
)
from dita_package_processor.discovery.graph import DependencyGraph
from dita_package_processor.discovery.models import (
    DiscoveryArtifact,
    DiscoveryInventory,
)
from dita_package_processor.discovery.relationships import (
    RelationshipExtractor,
)
from dita_package_processor.discovery.signatures import (
    has_maprefs,
    has_topicrefs,
)
from dita_package_processor.knowledge.map_types import MapType

LOGGER = logging.getLogger(__name__)


class DiscoveryScanner:
    """
    Scan a DITA package directory and produce a DiscoveryInventory.

    Guarantees:
    - Exactly one MAIN map is selected deterministically.
    - node_count metadata is annotated for all maps.
    """

    DITA_XML_SUFFIXES: Set[str] = {".dita", ".ditamap"}

    MEDIA_SUFFIXES: Set[str] = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".webp",
        ".tif",
        ".tiff",
        ".bmp",
        ".pdf",
    }

    # ======================================================================
    # Construction
    # ======================================================================

    def __init__(self, package_dir: Path) -> None:
        """
        Initialize scanner.

        Parameters
        ----------
        package_dir : Path
            Root directory of DITA package.
        """
        self.package_dir = Path(package_dir).resolve()

        if not self.package_dir.exists():
            raise FileNotFoundError(self.package_dir)

        if not self.package_dir.is_dir():
            raise ValueError(f"Not a directory: {self.package_dir}")

        LOGGER.debug("DiscoveryScanner initialized: %s", self.package_dir)

    # ======================================================================
    # Public API
    # ======================================================================

    def scan(self) -> DiscoveryInventory:
        """
        Perform full discovery scan.

        Returns
        -------
        DiscoveryInventory
        """
        LOGGER.info("Starting discovery scan: %s", self.package_dir)

        inventory = DiscoveryInventory()
        scanned_files = 0

        # -------------------------------------------------------------
        # Artifact detection + classification
        # -------------------------------------------------------------

        for path in sorted(self.package_dir.rglob("*")):
            if not path.is_file():
                continue

            suffix = path.suffix.lower()
            rel_path = path.relative_to(self.package_dir)

            # ---------------- Media ----------------

            if suffix in self.MEDIA_SUFFIXES:
                scanned_files += 1

                artifact = DiscoveryArtifact(
                    path=rel_path,
                    artifact_type="media",
                    metadata={
                        "size_bytes": path.stat().st_size,
                        "extension": suffix,
                    },
                )

                inventory.add_artifact(artifact)
                continue

            # ---------------- Non-DITA ----------------

            if suffix not in self.DITA_XML_SUFFIXES:
                continue

            scanned_files += 1
            artifact_type = "map" if suffix == ".ditamap" else "topic"

            metadata = self._extract_metadata(
                path=path,
                artifact_type=artifact_type,
            )

            try:
                if artifact_type == "map":
                    artifact = classify_map(
                        path=rel_path,
                        metadata=metadata,
                    )
                else:
                    artifact = classify_topic(
                        path=rel_path,
                        metadata=metadata,
                    )

            except Exception as exc:  # noqa: BLE001
                LOGGER.debug(
                    "Classification failed path=%s error=%s",
                    rel_path,
                    exc,
                )
                artifact = DiscoveryArtifact(
                    path=rel_path,
                    artifact_type=artifact_type,
                    metadata=metadata,
                )

            inventory.add_artifact(artifact)

        LOGGER.info(
            "Discovery scan complete scanned_files=%d artifacts=%d",
            scanned_files,
            len(inventory.artifacts),
        )

        # -------------------------------------------------------------
        # Relationship extraction
        # -------------------------------------------------------------

        extractor = RelationshipExtractor(self.package_dir)

        relationships = extractor.extract(
            [
                {
                    "path": str(a.path),
                    "artifact_type": a.artifact_type,
                }
                for a in inventory.artifacts
                if a.artifact_type in {"map", "topic"}
            ]
        )

        # -------------------------------------------------------------
        # Dependency graph
        # -------------------------------------------------------------

        artifact_dicts = [
            {
                "path": str(a.path),
                "artifact_type": a.artifact_type,
            }
            for a in inventory.artifacts
        ]

        graph = DependencyGraph.from_discovery(
            artifacts=artifact_dicts,
            relationships=[rel for rel in relationships if rel],
        )

        inventory.graph = graph  # type: ignore[attr-defined]

        # -------------------------------------------------------------
        # Structural annotation
        # -------------------------------------------------------------

        self._annotate_node_counts(inventory)

        # -------------------------------------------------------------
        # MAIN resolution
        # -------------------------------------------------------------

        self._normalize_main_map(inventory)

        return inventory

    # ======================================================================
    # MAIN Resolution
    # ======================================================================

    def _normalize_main_map(
        self,
        inventory: DiscoveryInventory,
    ) -> None:
        """
        Resolve exactly one MAIN map deterministically.

        Strategy
        --------
        1. If MAIN candidates exist:
           - Highest confidence wins
           - Tie → highest node_count
           - Tie → alphabetical path
        2. If none:
           - Single map → promote
           - Multiple → highest node_count
        """

        maps = inventory.maps()

        if not maps:
            LOGGER.warning("No maps discovered")
            return

        main_candidates = [
            a for a in maps if a.classification == MapType.MAIN
        ]

        # -------------------------------------------------------------
        # Pattern-emitted MAIN candidates
        # -------------------------------------------------------------

        if main_candidates:
            sorted_candidates = sorted(
                main_candidates,
                key=lambda a: (
                    a.confidence or 0.0,
                    a.metadata.get("node_count", 0),
                    str(a.path),
                ),
                reverse=True,
            )

            winner = sorted_candidates[0]

            LOGGER.info("Resolved MAIN via evidence: %s", winner.path)

            for loser in sorted_candidates[1:]:
                demoted = replace(
                    loser,
                    classification=MapType.CONTENT,
                )
                self._replace_artifact(inventory, loser, demoted)

            return

        # -------------------------------------------------------------
        # No MAIN candidates
        # -------------------------------------------------------------

        if len(maps) == 1:
            only_map = maps[0]

            promoted = replace(
                only_map,
                classification=MapType.MAIN,
                confidence=1.0,
            )

            self._replace_artifact(inventory, only_map, promoted)

            LOGGER.info("Promoted single map to MAIN: %s", only_map.path)
            return

        sorted_maps = sorted(
            maps,
            key=lambda a: (
                a.metadata.get("node_count", 0),
                str(a.path),
            ),
            reverse=True,
        )

        winner = sorted_maps[0]

        promoted = replace(
            winner,
            classification=MapType.MAIN,
            confidence=0.5,
        )

        self._replace_artifact(inventory, winner, promoted)

        LOGGER.warning(
            "No MAIN classified; structural winner selected: %s",
            winner.path,
        )

    # ======================================================================
    # Structural Weight
    # ======================================================================

    def _annotate_node_counts(
        self,
        inventory: DiscoveryInventory,
    ) -> None:
        """
        Annotate map artifacts with reachable node_count.
        """

        graph = getattr(inventory, "graph", None)

        if graph is None:
            return

        for artifact in inventory.maps():
            start = str(artifact.path)

            visited = set()
            stack = [start]

            while stack:
                current = stack.pop()

                if current in visited:
                    continue

                visited.add(current)

                outgoing = [
                    edge.target
                    for edge in graph.edges
                    if edge.source == current
                ]

                stack.extend(outgoing)

            artifact.metadata["node_count"] = len(visited)

            LOGGER.debug(
                "Annotated node_count=%d for %s",
                len(visited),
                artifact.path,
            )

    # ======================================================================
    # Metadata Extraction
    # ======================================================================

    def _extract_metadata(
        self,
        *,
        path: Path,
        artifact_type: str,
    ) -> Dict[str, object]:
        """
        Extract shallow structural metadata from XML.
        """

        metadata: Dict[str, object] = {}

        try:
            doc = read_xml(path)
            root = doc.root

            metadata["root_element"] = (
                etree.QName(root).localname.lower()
            )

            if artifact_type == "map":
                metadata["contains_mapref"] = has_maprefs(root)
                metadata["contains_topicref"] = has_topicrefs(root)

        except Exception as exc:  # noqa: BLE001
            LOGGER.debug(
                "Metadata extraction failed path=%s error=%s",
                path,
                exc,
            )

        return metadata

    # ======================================================================
    # Utility
    # ======================================================================

    @staticmethod
    def _replace_artifact(
        inventory: DiscoveryInventory,
        original: DiscoveryArtifact,
        replacement: DiscoveryArtifact,
    ) -> None:
        idx = inventory.artifacts.index(original)
        inventory.artifacts[idx] = replacement