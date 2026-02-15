"""
Tests for discovery data models.

These tests validate structural behavior only.

Discovery models:
- enforce invariants
- perform no inference
- perform no classification logic
"""

from pathlib import Path

import pytest

from dita_package_processor.discovery.models import (
    DiscoveryArtifact,
    DiscoveryInventory,
)
from dita_package_processor.discovery.patterns import Evidence
from dita_package_processor.knowledge.map_types import MapType


# =============================================================================
# DiscoveryArtifact Defaults
# =============================================================================


def test_discovery_artifact_defaults() -> None:
    """
    DiscoveryArtifact should initialize with minimal required state.
    """
    artifact = DiscoveryArtifact(
        path=Path("Map1.ditamap"),
        artifact_type="map",
    )

    assert artifact.path == Path("Map1.ditamap")
    assert artifact.artifact_type == "map"

    assert artifact.metadata == {}
    assert artifact.classification is None
    assert artifact.confidence is None
    assert artifact.evidence == []
    assert artifact.notes == []


# =============================================================================
# Media Invariants
# =============================================================================


def test_discovery_media_artifact_invariants() -> None:
    """
    Media artifacts must never retain semantic state.
    """
    artifact = DiscoveryArtifact(
        path=Path("images/logo.png"),
        artifact_type="media",
        classification="not-allowed",
        confidence=0.5,
        evidence=[
            Evidence(
                pattern_id="x",
                artifact_path=Path("images/logo.png"),
                asserted_role="X",
                confidence=0.5,
                rationale=[],
            )
        ],
    )

    assert artifact.artifact_type == "media"
    assert artifact.classification is None
    assert artifact.confidence is None
    assert artifact.evidence == []


# =============================================================================
# Invariant Enforcement
# =============================================================================


def test_confidence_without_classification_is_cleared() -> None:
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


def test_evidence_without_classification_is_cleared() -> None:
    """
    Evidence cannot exist without classification.
    """
    artifact = DiscoveryArtifact(
        path=Path("Map1.ditamap"),
        artifact_type="map",
        evidence=[
            Evidence(
                pattern_id="x",
                artifact_path=Path("Map1.ditamap"),
                asserted_role="X",
                confidence=0.8,
                rationale=[],
            )
        ],
    )

    assert artifact.classification is None
    assert artifact.confidence is None
    assert artifact.evidence == []


# =============================================================================
# Inventory Behavior
# =============================================================================


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
    DiscoveryInventory.by_type must filter by artifact type.
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

    assert len(inventory.by_type("map")) == 1
    assert len(inventory.by_type("topic")) == 1
    assert len(inventory.by_type("media")) == 1


def test_inventory_typed_accessors() -> None:
    """
    Inventory typed accessors must behave symmetrically.
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


# =============================================================================
# MAIN Map Resolution
# =============================================================================


def test_resolve_main_map_raises_when_none_present() -> None:
    """
    resolve_main_map must fail if no MAIN classification exists.
    """
    inventory = DiscoveryInventory()

    inventory.add_artifact(
        DiscoveryArtifact(path=Path("A.ditamap"), artifact_type="map")
    )

    with pytest.raises(ValueError):
        inventory.resolve_main_map()


def test_resolve_main_map_raises_when_multiple_present() -> None:
    """
    resolve_main_map must fail if multiple MAIN classifications exist.
    """
    inventory = DiscoveryInventory()

    a = DiscoveryArtifact(
        path=Path("A.ditamap"),
        artifact_type="map",
        classification=MapType.MAIN,
        confidence=1.0,
    )
    b = DiscoveryArtifact(
        path=Path("B.ditamap"),
        artifact_type="map",
        classification=MapType.MAIN,
        confidence=1.0,
    )

    inventory.add_artifact(a)
    inventory.add_artifact(b)

    with pytest.raises(ValueError):
        inventory.resolve_main_map()


def test_resolve_main_map_success() -> None:
    """
    resolve_main_map must return the single MAIN map.
    """
    inventory = DiscoveryInventory()

    main = DiscoveryArtifact(
        path=Path("Main.ditamap"),
        artifact_type="map",
        classification=MapType.MAIN,
        confidence=1.0,
    )

    inventory.add_artifact(main)

    assert inventory.resolve_main_map() == Path("Main.ditamap")