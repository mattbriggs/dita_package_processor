"""
Filesystem and XML scanner for DITA package discovery.

This module performs *read-only* inspection of a DITA package directory.
It identifies maps, topics, and media assets, extracts shallow structural
signals, extracts explicit structural relationships, and aggregates all
findings into a :class:`DiscoveryInventory`.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path
from typing import Dict, Set

from lxml import etree

from dita_package_processor.dita_xml import read_xml
from dita_package_processor.discovery.classifiers import classify_map, classify_topic
from dita_package_processor.discovery.graph import DependencyGraph
from dita_package_processor.discovery.models import DiscoveryArtifact, DiscoveryInventory
from dita_package_processor.discovery.relationships import RelationshipExtractor
from dita_package_processor.discovery.signatures import has_maprefs, has_topicrefs

LOGGER = logging.getLogger(__name__)


class DiscoveryScanner:
    """
    Scan a DITA package directory and produce a discovery inventory.
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

    def __init__(self, package_dir: Path) -> None:
        self.package_dir = package_dir.resolve()
        LOGGER.debug("Initialized DiscoveryScanner: %s", self.package_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self) -> DiscoveryInventory:
        LOGGER.info("Starting discovery scan: %s", self.package_dir)

        inventory = DiscoveryInventory()
        scanned_files = 0

        # --------------------------------------------------------------
        # Artifact detection + classification
        # --------------------------------------------------------------

        for path in self.package_dir.rglob("*"):
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
                    artifact = classify_map(path=rel_path, metadata=metadata)
                else:
                    artifact = classify_topic(path=rel_path, metadata=metadata)

            except Exception as exc:  # noqa: BLE001
                LOGGER.debug("Classification failed for %s: %s", rel_path, exc)
                artifact = DiscoveryArtifact(
                    path=rel_path,
                    artifact_type=artifact_type,
                    metadata=metadata,
                )

            inventory.add_artifact(artifact)

        LOGGER.info(
            "Discovery scan complete: scanned_files=%d artifacts=%d",
            scanned_files,
            len(inventory.artifacts),
        )

        # ==================================================================
        # MAIN MAP NORMALIZATION
        # ==================================================================

        def _is_main(classification: object) -> bool:
            if classification is None:
                return False
            return str(classification).upper() == "MAIN_MAP"

        maps = [a for a in inventory.artifacts if a.artifact_type == "map"]

        if not maps:
            LOGGER.warning("No maps discovered in package")

        main_maps = [a for a in maps if _is_main(a.classification)]

        # Case 1: exactly one → promote
        if len(maps) == 1 and not main_maps:
            only_map = maps[0]

            LOGGER.info("Promoting single map to MAIN_MAP: %s", only_map.path)

            promoted = replace(
                only_map,
                classification="MAIN_MAP",
                confidence=1.0,
            )

            idx = inventory.artifacts.index(only_map)
            inventory.artifacts[idx] = promoted

        # Case 2: multiple maps, none classified → deterministic fallback
        elif len(maps) > 1 and not main_maps:
            fallback = sorted(maps, key=lambda a: str(a.path))[0]

            LOGGER.warning(
                "No MAIN_MAP detected by patterns; promoting fallback map: %s",
                fallback.path,
            )

            promoted = replace(
                fallback,
                classification="MAIN_MAP",
                confidence=0.2,
            )

            idx = inventory.artifacts.index(fallback)
            inventory.artifacts[idx] = promoted

        # --------------------------------------------------------------
        # Relationship extraction
        # --------------------------------------------------------------

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

        # --------------------------------------------------------------
        # Dependency graph construction
        # --------------------------------------------------------------

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

        inventory.graph = graph

        return inventory

    # ------------------------------------------------------------------
    # Metadata extraction
    # ------------------------------------------------------------------

    def _extract_metadata(
        self,
        *,
        path: Path,
        artifact_type: str,
    ) -> Dict[str, object]:

        metadata: Dict[str, object] = {}

        try:
            doc = read_xml(path)
            root = doc.root

            metadata["root_element"] = etree.QName(root).localname.lower()

            if artifact_type == "map":
                metadata["contains_mapref"] = has_maprefs(root)
                metadata["contains_topicref"] = has_topicrefs(root)

        except Exception as exc:  # noqa: BLE001
            LOGGER.debug("Metadata extraction failed for %s: %s", path, exc)

        return metadata