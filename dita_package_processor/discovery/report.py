"""
Reporting utilities for DITA package discovery.

This module converts a fully populated DiscoveryInventory into a stable,
JSON-serializable discovery contract defined by discovery.schema.json.

It performs no classification, parsing, or filesystem access.
It only serializes already-discovered data into a schema-valid structure.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List

from dita_package_processor.discovery.models import DiscoveryArtifact, DiscoveryInventory
from dita_package_processor.discovery.patterns import Evidence

LOGGER = logging.getLogger(__name__)


@dataclass
class DiscoveryReport:
    """
    Materialized discovery report summarizing a DiscoveryInventory.

    This is a pure reporting layer that emits a schema-locked discovery contract.
    """

    inventory: DiscoveryInventory

    # ------------------------------------------------------------------
    # Summary helpers
    # ------------------------------------------------------------------

    def summary(self) -> dict[str, int]:
        """
        Return a simple artifact type histogram.

        Contract:
            {
                "map": <int>,
                "topic": <int>,
                "media": <int>,
            }
        """
        counts: dict[str, int] = {}

        for artifact in self.inventory.artifacts:
            counts.setdefault(artifact.artifact_type, 0)
            counts[artifact.artifact_type] += 1

        LOGGER.debug("Discovery summary: %s", counts)
        return counts

    # ------------------------------------------------------------------
    # Stable contract serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the discovery report into a schema-valid structure:

        {
          "artifacts": [...],
          "relationships": [...],
          "summary": {...}
        }

        Note:
        - Graph internals (source/target) are normalized into discovery contract
          fields (from/to) here.
        - The graph itself is not exposed.
        """
        LOGGER.info(
            "Serializing discovery report: %d artifacts, %d relationships",
            len(self.inventory.artifacts),
            len(self.inventory.graph.edges),
        )

        artifacts: List[Dict[str, Any]] = [
            self._serialize_artifact(artifact)
            for artifact in self.inventory.artifacts
        ]

        relationships: List[Dict[str, Any]] = [
            {
                "source": edge.source,
                "target": edge.target,
                "type": edge.edge_type,
                "pattern_id": edge.pattern_id,
            }
            for edge in self.inventory.graph.edges
        ]

        data: Dict[str, Any] = {
            "artifacts": artifacts,
            "relationships": relationships,
            "summary": self.summary(),
        }

        LOGGER.debug(
            "DiscoveryReport serialized: artifacts=%d relationships=%d",
            len(artifacts),
            len(relationships),
        )
        return data

    # ------------------------------------------------------------------
    # Artifact serialization
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_artifact(artifact: DiscoveryArtifact) -> Dict[str, Any]:
        """
        Serialize a discovery artifact according to discovery.schema.json.
        """
        LOGGER.debug(
            "Serializing artifact: path=%s type=%s",
            artifact.path,
            artifact.artifact_type,
        )

        data: Dict[str, Any] = {
            "path": str(artifact.path),
            "artifact_type": artifact.artifact_type,
            "classification": None,
            "confidence": None,
            "metadata": dict(artifact.metadata or {}),
            "notes": list(artifact.notes or []),
            "evidence": [],
        }

        # Media artifacts are inventory-only
        if artifact.artifact_type == "media":
            LOGGER.debug("Serialized media artifact: %s", artifact.path)
            return data

        # DITA artifacts (map, topic)
        if artifact.classification is not None:
            data["classification"] = (
                artifact.classification.name
                if hasattr(artifact.classification, "name")
                else str(artifact.classification)
            )

        if artifact.confidence is not None:
            data["confidence"] = artifact.confidence

        data["evidence"] = [
            DiscoveryReport._serialize_evidence(ev)
            for ev in artifact.evidence or []
        ]

        LOGGER.debug(
            "Serialized DITA artifact %s with %d evidence records",
            artifact.path,
            len(data["evidence"]),
        )
        return data

    @staticmethod
    def _serialize_evidence(ev: Evidence) -> Dict[str, Any]:
        """
        Serialize a single Evidence record.
        """
        LOGGER.debug(
            "Serializing evidence: pattern_id=%s role=%s confidence=%s",
            ev.pattern_id,
            ev.asserted_role,
            ev.confidence,
        )

        return {
            "pattern_id": ev.pattern_id,
            "asserted_role": ev.asserted_role,
            "confidence": ev.confidence,
            "rationale": list(ev.rationale),
        }