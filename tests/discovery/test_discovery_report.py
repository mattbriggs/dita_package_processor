"""
Tests for discovery report generation.

DiscoveryReport is a presentation-only layer over a DiscoveryInventory.
It must not perform classification, inference, or mutation.
It must emit schema-valid discovery contracts.
"""

from pathlib import Path

from dita_package_processor.discovery.report import DiscoveryReport
from dita_package_processor.discovery.models import DiscoveryArtifact, DiscoveryInventory
from dita_package_processor.discovery.graph import DependencyGraph, DependencyEdge
from dita_package_processor.knowledge.map_types import MapType


# =============================================================================
# Helpers
# =============================================================================


def _make_inventory(artifacts, edges=None):
    """
    Helper to construct a DiscoveryInventory with a populated dependency graph.

    Relationship contract must use:
        source / target / type / pattern_id
    """
    inventory = DiscoveryInventory()

    for artifact in artifacts:
        inventory.add_artifact(artifact)

    artifact_dicts = [
        {
            "path": str(a.path),
            "artifact_type": a.artifact_type,
        }
        for a in artifacts
        if a.artifact_type in {"map", "topic"}  # media excluded from graph
    ]

    relationship_dicts = []
    if edges:
        for edge in edges:
            relationship_dicts.append(
                {
                    "source": edge.source,
                    "target": edge.target,
                    "type": edge.edge_type,
                    "pattern_id": edge.pattern_id,
                }
            )

    graph = DependencyGraph.from_discovery(
        artifacts=artifact_dicts,
        relationships=relationship_dicts,
    )

    inventory.graph = graph
    return inventory


# =============================================================================
# Artifacts
# =============================================================================


def test_report_exposes_artifacts() -> None:
    """
    DiscoveryReport must expose artifacts exactly as discovered.
    """
    artifacts = [
        DiscoveryArtifact(
            path=Path("Main.ditamap"),
            artifact_type="map",
            classification=MapType.MAIN,
            confidence=0.9,
        ),
        DiscoveryArtifact(
            path=Path("topics/a.dita"),
            artifact_type="topic",
        ),
    ]

    inventory = _make_inventory(artifacts)
    report = DiscoveryReport(inventory)

    data = report.to_dict()

    assert "artifacts" in data
    assert len(data["artifacts"]) == 2

    main = data["artifacts"][0]
    assert main["path"] == "Main.ditamap"
    assert main["artifact_type"] == "map"
    assert main["classification"] == "MAIN"
    assert main["confidence"] == 0.9


# =============================================================================
# Relationships
# =============================================================================


def test_report_supports_relationships() -> None:
    """
    DiscoveryReport must serialize relationships using the
    stable discovery contract (source/target).
    """
    artifacts = [
        DiscoveryArtifact(Path("Main.ditamap"), "map"),
        DiscoveryArtifact(Path("topics/a.dita"), "topic"),
    ]

    edges = [
        DependencyEdge(
            source="Main.ditamap",
            target="topics/a.dita",
            edge_type="topicref",
            pattern_id="dita_map_topicref",
        )
    ]

    inventory = _make_inventory(artifacts, edges)
    report = DiscoveryReport(inventory)

    data = report.to_dict()

    assert "relationships" in data
    assert len(data["relationships"]) == 1

    edge = data["relationships"][0]

    assert edge == {
        "source": "Main.ditamap",
        "target": "topics/a.dita",
        "type": "topicref",
        "pattern_id": "dita_map_topicref",
    }


# =============================================================================
# Summary
# =============================================================================


def test_summary_only_counts_artifact_types() -> None:
    """
    Summary must only include artifact-type counts.
    No suffixes. No relationship_count. No total_artifacts. No magic.
    """
    artifacts = [
        DiscoveryArtifact(Path("Main.ditamap"), "map"),
        DiscoveryArtifact(Path("media/logo.png"), "media"),
        DiscoveryArtifact(Path("topics/a.dita"), "topic"),
    ]

    inventory = _make_inventory(artifacts)
    report = DiscoveryReport(inventory)
    summary = report.summary()

    assert summary == {
        "map": 1,
        "media": 1,
        "topic": 1,
    }


# =============================================================================
# Media serialization
# =============================================================================


def test_report_serializes_media_artifact() -> None:
    """
    Media artifacts must serialize using the standard artifact schema.
    """
    artifacts = [
        DiscoveryArtifact(
            path=Path("media/logo.png"),
            artifact_type="media",
            metadata={
                "size_bytes": 12421,
                "extension": "png",
            },
        )
    ]

    inventory = _make_inventory(artifacts)
    report = DiscoveryReport(inventory)
    data = report.to_dict()

    media = [a for a in data["artifacts"] if a["artifact_type"] == "media"]
    assert len(media) == 1

    media_entry = media[0]
    assert media_entry["path"] == "media/logo.png"
    assert media_entry["artifact_type"] == "media"
    assert media_entry["classification"] is None
    assert media_entry["confidence"] is None
    assert media_entry["evidence"] == []
    assert media_entry["metadata"]["size_bytes"] == 12421
    assert media_entry["metadata"]["extension"] == "png"


# =============================================================================
# Structure
# =============================================================================


def test_report_structure() -> None:
    """
    JSON output must expose:
    - artifacts
    - relationships
    - summary
    """
    artifacts = [
        DiscoveryArtifact(Path("Main.ditamap"), "map"),
        DiscoveryArtifact(Path("topics/a.dita"), "topic"),
    ]

    inventory = _make_inventory(artifacts)
    report = DiscoveryReport(inventory)
    data = report.to_dict()

    assert set(data.keys()) == {"artifacts", "relationships", "summary"}

    assert isinstance(data["artifacts"], list)
    assert isinstance(data["relationships"], list)
    assert isinstance(data["summary"], dict)