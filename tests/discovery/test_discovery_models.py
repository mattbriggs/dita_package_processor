"""
Tests for discovery data models.

These tests validate the behavior of discovery-phase data structures.
Discovery models are intentionally lightweight and contain no
classification or inference logic.
"""

from pathlib import Path

from dita_package_processor.discovery.models import (
    DiscoveryArtifact,
    DiscoveryInventory,
)


def test_discovery_artifact_defaults() -> None:
    """
    DiscoveryArtifact should initialize with minimal required state
    and stable default values.

    No inference is allowed at construction time.
    """
    artifact = DiscoveryArtifact(
        path=Path("Map1.ditamap"),
        artifact_type="map",
    )

    assert artifact.path == Path("Map1.ditamap")
    assert artifact.artifact_type == "map"

    # Contract-locked defaults
    assert artifact.metadata == {}
    assert artifact.classification is None
    assert artifact.confidence is None
    assert artifact.evidence == []
    assert artifact.notes == []


def test_discovery_media_artifact_invariants() -> None:
    """
    Media artifacts must never have classification, confidence, or evidence.
    All such values must be forcibly cleared on creation.
    """
    artifact = DiscoveryArtifact(
        path=Path("images/logo.png"),
        artifact_type="media",
        classification="not-allowed",  # should be cleared
        confidence=0.5,                # should be cleared
        evidence=["also-not-allowed"],  # should be cleared
    )

    assert artifact.artifact_type == "media"
    assert artifact.classification is None
    assert artifact.confidence is None
    assert artifact.evidence == []


def test_discovery_artifact_invariant_confidence_without_classification() -> None:
    """
    Confidence cannot exist without classification.
    """
    artifact = DiscoveryArtifact(
        path=Path("Map1.ditamap"),
        artifact_type="map",
        confidence=0.7,
    )

    assert artifact.classification is None
    assert artifact.confidence is None
    assert artifact.evidence == []


def test_discovery_artifact_invariant_evidence_without_classification() -> None:
    """
    Evidence cannot exist without classification.
    """
    artifact = DiscoveryArtifact(
        path=Path("Map1.ditamap"),
        artifact_type="map",
        evidence=["bad"],
    )

    assert artifact.classification is None
    assert artifact.confidence is None
    assert artifact.evidence == []


def test_inventory_add_artifact() -> None:
    """
    DiscoveryInventory should store added artifacts.
    """
    inventory = DiscoveryInventory()
    artifact = DiscoveryArtifact(
        path=Path("Main.ditamap"),
        artifact_type="map",
    )

    inventory.add_artifact(artifact)

    assert len(inventory.artifacts) == 1
    assert inventory.artifacts[0] is artifact
    assert inventory.artifacts[0].path == Path("Main.ditamap")


def test_inventory_filters_by_type() -> None:
    """
    DiscoveryInventory.by_type should filter artifacts by category.
    """
    inventory = DiscoveryInventory()

    inventory.add_artifact(
        DiscoveryArtifact(path=Path("Main.ditamap"), artifact_type="map")
    )
    inventory.add_artifact(
        DiscoveryArtifact(path=Path("topics/a.dita"), artifact_type="topic")
    )
    inventory.add_artifact(
        DiscoveryArtifact(path=Path("media/logo.png"), artifact_type="media")
    )

    maps = inventory.by_type("map")
    topics = inventory.by_type("topic")
    media = inventory.by_type("media")

    assert len(maps) == 1
    assert maps[0].artifact_type == "map"

    assert len(topics) == 1
    assert topics[0].artifact_type == "topic"

    assert len(media) == 1
    assert media[0].artifact_type == "media"


def test_inventory_typed_accessors() -> None:
    """
    Inventory should expose typed accessors for maps, topics, and media.
    Symmetry matters: maps(), topics(), media().
    """
    inventory = DiscoveryInventory()

    inventory.add_artifact(
        DiscoveryArtifact(path=Path("Main.ditamap"), artifact_type="map")
    )
    inventory.add_artifact(
        DiscoveryArtifact(path=Path("topics/a.dita"), artifact_type="topic")
    )
    inventory.add_artifact(
        DiscoveryArtifact(path=Path("media/image.jpg"), artifact_type="media")
    )

    maps = inventory.maps()
    topics = inventory.topics()
    media = inventory.media()

    assert len(maps) == 1
    assert maps[0].path == Path("Main.ditamap")

    assert len(topics) == 1
    assert topics[0].path == Path("topics/a.dita")

    assert len(media) == 1
    assert media[0].path == Path("media/image.jpg")