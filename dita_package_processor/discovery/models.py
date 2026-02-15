"""
Discovery data models.

These models represent strictly observational records of what was found
during DITA package discovery.

Design Principles
-----------------
- No inference
- No transformation
- No mutation of semantic meaning
- Deterministic structure
- Explicit invariants

Discovery records facts.
Planning interprets them.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Literal, Union

from dita_package_processor.knowledge.map_types import MapType
from dita_package_processor.knowledge.topic_types import TopicType

if TYPE_CHECKING:
    from dita_package_processor.discovery.patterns import Evidence

LOGGER = logging.getLogger(__name__)

ArtifactType = Literal["map", "topic", "media"]

ClassificationType = Union[MapType, TopicType, str]


# =============================================================================
# Core Artifact Model
# =============================================================================


@dataclass
class DiscoveryArtifact:
    """
    Observational record of a discovered filesystem artifact.

    Rules
    -----
    - Media artifacts are structural only.
    - classification requires confidence.
    - evidence requires classification.
    - No semantic inference is performed here.
    """

    path: Path
    artifact_type: ArtifactType

    classification: Optional[ClassificationType] = None
    confidence: Optional[float] = None

    metadata: Dict[str, Any] = field(default_factory=dict)
    evidence: List["Evidence"] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def __post_init__(self) -> None:
        LOGGER.debug(
            "DiscoveryArtifact initialized path=%s type=%s",
            self.path,
            self.artifact_type,
        )

        if not isinstance(self.path, Path):
            raise TypeError("path must be pathlib.Path")

        if self.artifact_type not in ("map", "topic", "media"):
            raise ValueError(f"Invalid artifact_type: {self.artifact_type}")

        self._enforce_invariants()

    # -------------------------------------------------------------------------

    def _enforce_invariants(self) -> None:
        """
        Enforce structural invariants.
        """

        if self.artifact_type == "media":
            if (
                self.classification is not None
                or self.confidence is not None
                or self.evidence
            ):
                LOGGER.warning(
                    "Media artifact %s cannot carry semantic data; clearing",
                    self.path,
                )
                self.classification = None
                self.confidence = None
                self.evidence.clear()
            return

        if self.classification is None:
            if self.confidence is not None:
                LOGGER.warning(
                    "Artifact %s has confidence without classification; clearing",
                    self.path,
                )
                self.confidence = None

            if self.evidence:
                LOGGER.warning(
                    "Artifact %s has evidence without classification; clearing",
                    self.path,
                )
                self.evidence.clear()

        if self.classification is not None and self.confidence is None:
            LOGGER.warning(
                "Artifact %s has classification but no confidence; defaulting to 1.0",
                self.path,
            )
            self.confidence = 1.0

    # -------------------------------------------------------------------------
    # Semantic helpers
    # -------------------------------------------------------------------------

    def classification_label(self) -> Optional[str]:
        """
        Return normalized string label for classification.

        Returns
        -------
        Optional[str]
        """
        if self.classification is None:
            return None

        if isinstance(self.classification, (MapType, TopicType)):
            return self.classification.value

        return str(self.classification)

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize artifact for contract transfer.
        """
        return {
            "path": str(self.path),
            "artifact_type": self.artifact_type,
            "classification": self.classification_label(),
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
            "evidence": [
                {
                    "pattern_id": e.pattern_id,
                    "asserted_role": e.asserted_role,
                    "confidence": e.confidence,
                    "rationale": getattr(e, "rationale", []),
                }
                for e in self.evidence
            ],
            "notes": list(self.notes),
        }


# =============================================================================
# Discovery Inventory
# =============================================================================


@dataclass
class DiscoveryInventory:
    """
    Aggregational container of discovered artifacts.

    Mutable during discovery.
    """

    artifacts: List[DiscoveryArtifact] = field(default_factory=list)

    # -------------------------------------------------------------------------
    # Mutation
    # -------------------------------------------------------------------------

    def add_artifact(
        self,
        artifact: DiscoveryArtifact | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Add a discovered artifact.
        """
        if artifact is not None and kwargs:
            raise TypeError(
                "Provide either artifact or keyword arguments, not both"
            )

        if artifact is None:
            artifact = DiscoveryArtifact(**kwargs)

        LOGGER.debug(
            "Adding artifact path=%s type=%s",
            artifact.path,
            artifact.artifact_type,
        )

        self.artifacts.append(artifact)

    # -------------------------------------------------------------------------
    # Query Helpers
    # -------------------------------------------------------------------------

    def by_type(self, artifact_type: ArtifactType) -> List[DiscoveryArtifact]:
        results = [
            artifact
            for artifact in self.artifacts
            if artifact.artifact_type == artifact_type
        ]

        LOGGER.debug(
            "Filtered %d artifacts of type=%s",
            len(results),
            artifact_type,
        )

        return results

    def maps(self) -> List[DiscoveryArtifact]:
        return self.by_type("map")

    def topics(self) -> List[DiscoveryArtifact]:
        return self.by_type("topic")

    def media(self) -> List[DiscoveryArtifact]:
        return self.by_type("media")

    # -------------------------------------------------------------------------
    # MAIN map resolution
    # -------------------------------------------------------------------------

    def resolve_main_map(self) -> Path:
        """
        Resolve the single MAIN map.

        Returns
        -------
        Path

        Raises
        ------
        ValueError
        """
        main_maps = [
            artifact
            for artifact in self.maps()
            if artifact.classification == MapType.MAIN
        ]

        if not main_maps:
            raise ValueError("No MAIN map detected; contract violation")

        if len(main_maps) > 1:
            raise ValueError("Multiple MAIN maps detected; contract violation")

        LOGGER.info("Resolved MAIN map: %s", main_maps[0].path)
        return main_maps[0].path

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_count": len(self.artifacts),
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
        }


# =============================================================================
# Discovery Summary
# =============================================================================


@dataclass(frozen=True)
class DiscoverySummary:
    """
    High-level summary of discovery.
    """

    map_count: int
    topic_count: int
    media_count: int

    def to_dict(self) -> Dict[str, int]:
        return {
            "map_count": self.map_count,
            "topic_count": self.topic_count,
            "media_count": self.media_count,
        }


@dataclass(frozen=True)
class DiscoveryResult:
    """
    Immutable result of discovery.
    """

    inventory: DiscoveryInventory
    summary: DiscoverySummary

    def main_map(self) -> Path:
        """
        Return resolved MAIN map.
        """
        return self.inventory.resolve_main_map()