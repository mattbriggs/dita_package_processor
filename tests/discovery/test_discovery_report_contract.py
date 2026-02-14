"""
Tests for the stable discovery report contract.

These tests ensure discovery JSON is a guaranteed API, not an accident.

Contract invariants
-------------------
- top-level keys are fixed
- relationships use source/target (not from/to)
- media never appears in relationships
- summary only counts artifact types
"""

from pathlib import Path

from dita_package_processor.discovery.graph import DependencyGraph
from dita_package_processor.discovery.models import DiscoveryArtifact, DiscoveryInventory
from dita_package_processor.discovery.report import DiscoveryReport


def test_discovery_report_contract_shape() -> None:
    # ------------------------------------------------------------------
    # Artifacts
    # ------------------------------------------------------------------

    artifacts = [
        DiscoveryArtifact(path=Path("index.ditamap"), artifact_type="map"),
        DiscoveryArtifact(path=Path("topics/a.dita"), artifact_type="topic"),
        DiscoveryArtifact(
            path=Path("media/logo.png"),
            artifact_type="media",
            metadata={"size_bytes": 1234, "extension": ".png"},
        ),
    ]

    inventory = DiscoveryInventory()
    for artifact in artifacts:
        inventory.add_artifact(artifact)

    # ------------------------------------------------------------------
    # Dependency Graph (internal only)
    # ------------------------------------------------------------------

    artifact_dicts = [
        {"path": "index.ditamap", "artifact_type": "map"},
        {"path": "topics/a.dita", "artifact_type": "topic"},
    ]

    # UPDATED: discovery relationship contract is source/target
    relationship_dicts = [
        {
            "source": "index.ditamap",
            "target": "topics/a.dita",
            "type": "topicref",
            "pattern_id": "map_contains_topicref",
        }
    ]

    graph = DependencyGraph.from_discovery(
        artifacts=artifact_dicts,
        relationships=relationship_dicts,
    )

    inventory.graph = graph

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    report = DiscoveryReport(inventory)
    data = report.to_dict()

    # ------------------------------------------------------------------
    # Top-level contract
    # ------------------------------------------------------------------

    # Public API surface: graph is NOT exposed
    assert set(data.keys()) == {"artifacts", "relationships", "summary"}
    assert len(data["relationships"]) == 1

    # ------------------------------------------------------------------
    # Relationship schema
    # ------------------------------------------------------------------

    edge = data["relationships"][0]

    assert set(edge.keys()) == {"source", "target", "type", "pattern_id"}
    assert edge["source"] == "index.ditamap"
    assert edge["target"] == "topics/a.dita"

    # ------------------------------------------------------------------
    # Media behavior
    # ------------------------------------------------------------------

    media_paths = [
        a["path"]
        for a in data["artifacts"]
        if a["artifact_type"] == "media"
    ]
    assert "media/logo.png" in media_paths

    relationship_paths = {
        r["source"] for r in data["relationships"]
    } | {
        r["target"] for r in data["relationships"]
    }

    # Media must never appear in edges
    assert "media/logo.png" not in relationship_paths

    # ------------------------------------------------------------------
    # Summary contract (type counts only)
    # ------------------------------------------------------------------

    summary = data["summary"]

    assert summary == {
        "map": 1,
        "topic": 1,
        "media": 1,
    }