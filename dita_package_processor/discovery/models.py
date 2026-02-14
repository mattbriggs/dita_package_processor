"""
Data models for DITA package discovery.

These models are strictly observational records describing what was found
during discovery. They do not:

- infer intent
- transform content
- execute logic

They exist to support:
- schema validation
- deterministic planning
- traceable automation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Literal

from dita_package_processor.knowledge.map_types import MapType, TopicType

if TYPE_CHECKING:
    from dita_package_processor.discovery.patterns import Evidence

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Core discovery models
# ---------------------------------------------------------------------------

ArtifactType = Literal["map", "topic", "media"]


@dataclass
class DiscoveryArtifact:
    """
    Observational record of a discovered filesystem artifact.

    Rules:

    - classification is None unless a pattern asserts it
    - confidence is None unless classification exists
    - evidence is empty unless patterns assert something
    - media artifacts never have classification, confidence, or evidence
    """

    path: Path
    artifact_type: ArtifactType

    classification: MapType | TopicType | None = None
    confidence: Optional[float] = None

    metadata: Dict[str, Any] = field(default_factory=dict)
    evidence: List["Evidence"] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        logger.debug(
            "Initialized DiscoveryArtifact(path=%s, type=%s)",
            self.path,
            self.artifact_type,
        )

        # Media is structural only, never semantic
        if self.artifact_type == "media":
            if self.classification is not None:
                logger.warning(
                    "Media artifact %s had classification; clearing",
                    self.path,
                )
                self.classification = None

            if self.confidence is not None:
                logger.warning(
                    "Media artifact %s had confidence; clearing",
                    self.path,
                )
                self.confidence = None

            if self.evidence:
                logger.warning(
                    "Media artifact %s had evidence; clearing",
                    self.path,
                )
                self.evidence.clear()

        # Non-media invariants
        else:
            if self.classification is None:
                if self.confidence is not None:
                    logger.warning(
                        "Artifact %s has confidence without classification; clearing",
                        self.path,
                    )
                    self.confidence = None

                if self.evidence:
                    logger.warning(
                        "Artifact %s has evidence without classification; clearing",
                        self.path,
                    )
                    self.evidence.clear()


# ---------------------------------------------------------------------------
# Inventory container
# ---------------------------------------------------------------------------


@dataclass
class DiscoveryInventory:
    """
    Container for all discovered artifacts.

    This structure is purely aggregational and mutation-safe.
    """

    artifacts: List[DiscoveryArtifact] = field(default_factory=list)

    def add_artifact(
        self,
        artifact: DiscoveryArtifact | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Add a discovered artifact.

        Either pass a DiscoveryArtifact or keyword arguments to construct one.
        """
        if artifact is not None and kwargs:
            raise TypeError(
                "Provide either a DiscoveryArtifact instance or keyword arguments, not both"
            )

        if artifact is None:
            artifact = DiscoveryArtifact(**kwargs)

        logger.debug(
            "Adding artifact: %s (%s)",
            artifact.path,
            artifact.artifact_type,
        )

        self.artifacts.append(artifact)

    def by_type(self, artifact_type: ArtifactType) -> List[DiscoveryArtifact]:
        """
        Return artifacts filtered by type.
        """
        results = [
            artifact
            for artifact in self.artifacts
            if artifact.artifact_type == artifact_type
        ]

        logger.debug(
            "Retrieved %d artifacts of type '%s'",
            len(results),
            artifact_type,
        )
        return results

    def maps(self) -> List[DiscoveryArtifact]:
        """Return discovered maps."""
        return self.by_type("map")

    def topics(self) -> List[DiscoveryArtifact]:
        """Return discovered topics."""
        return self.by_type("topic")

    def media(self) -> List[DiscoveryArtifact]:
        """Return discovered media artifacts."""
        return self.by_type("media")


# ---------------------------------------------------------------------------
# Aggregated discovery result models (DITA-only)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DiscoveredMap:
    """Resolved semantic view of a discovered map."""

    classification: MapType
    referenced_topics: List[Path] = field(default_factory=list)
    referenced_maps: List[Path] = field(default_factory=list)


@dataclass(frozen=True)
class DiscoveredTopic:
    """Resolved semantic view of a discovered topic."""

    classification: TopicType
    referenced_by_maps: List[Path] = field(default_factory=list)


@dataclass(frozen=True)
class DiscoverySummary:
    """High-level summary of discovery."""

    map_counts: Dict[str, int]
    topic_counts: Dict[str, int]
    media_count: int


@dataclass(frozen=True)
class DiscoveryResult:
    """
    Immutable result of discovery.

    This is what planning consumes.
    """

    maps: Dict[Path, DiscoveredMap]
    topics: Dict[Path, DiscoveredTopic]
    media: List[Path]
    summary: DiscoverySummary

    def get_main_map(self) -> Optional[DiscoveredMap]:
        """
        Return the main map if one exists.

        Classification is authoritative.
        """
        logger.debug("Searching for main map")

        for path, discovered in self.maps.items():
            kind = getattr(discovered.classification, "kind", None)
            logger.debug("Map %s has classification kind=%s", path, kind)

            if kind == "main":
                logger.info("Main map found: %s", path)
                return discovered

        logger.info("No main map found")
        return None