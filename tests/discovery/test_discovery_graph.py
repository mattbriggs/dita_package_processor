"""
Tests for dependency graph construction and serialization.

These tests enforce the contract boundary:

- Discovery JSON uses relationships with source/target/type/pattern_id
- DependencyGraph is derived from discovery
- Graph serialization uses source/target/type/pattern_id
- Graph never invents nodes
- Graph rejects unknown references
- Graph navigation helpers behave deterministically
"""

from __future__ import annotations

import pytest

from dita_package_processor.discovery.graph import DependencyGraph, DependencyEdge


# ---------------------------------------------------------------------------
# DependencyEdge
# ---------------------------------------------------------------------------


def test_edge_from_relationship_style_keys() -> None:
    """
    Discovery relationships use source/target keys.
    """
    edge = DependencyEdge.from_relationship(
        {
            "source": "index.ditamap",
            "target": "topics/a.dita",
            "type": "topicref",
            "pattern_id": "map_contains_topicref",
        }
    )

    assert edge.source == "index.ditamap"
    assert edge.target == "topics/a.dita"
    assert edge.edge_type == "topicref"
    assert edge.pattern_id == "map_contains_topicref"


def test_edge_from_graph_dict_style_keys() -> None:
    """
    Graph serialization uses source/target keys.
    """
    edge = DependencyEdge.from_dict(
        {
            "source": "index.ditamap",
            "target": "topics/a.dita",
            "type": "topicref",
            "pattern_id": "map_contains_topicref",
        }
    )

    assert edge.source == "index.ditamap"
    assert edge.target == "topics/a.dita"
    assert edge.edge_type == "topicref"
    assert edge.pattern_id == "map_contains_topicref"


def test_edge_serialization_roundtrip() -> None:
    """
    Edge must serialize and deserialize without mutation.
    """
    edge = DependencyEdge(
        source="a",
        target="b",
        edge_type="xref",
        pattern_id="p",
    )

    data = edge.to_dict()
    loaded = DependencyEdge.from_dict(data)

    assert loaded == edge


# ---------------------------------------------------------------------------
# DependencyGraph.from_discovery
# ---------------------------------------------------------------------------


def test_graph_from_discovery_builds_nodes_and_edges() -> None:
    artifacts = [
        {"path": "index.ditamap", "artifact_type": "map"},
        {"path": "topics/a.dita", "artifact_type": "topic"},
        {"path": "media/logo.png", "artifact_type": "media"},
    ]

    relationships = [
        {
            "source": "index.ditamap",
            "target": "topics/a.dita",
            "type": "topicref",
            "pattern_id": "map_contains_topicref",
        },
        {
            "source": "topics/a.dita",
            "target": "media/logo.png",
            "type": "image",
            "pattern_id": "topic_image",
        },
    ]

    graph = DependencyGraph.from_discovery(
        artifacts=artifacts,
        relationships=relationships,
    )

    # ------------------------------------------------------------------
    # Structural integrity
    # ------------------------------------------------------------------

    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2

    # ------------------------------------------------------------------
    # Serialization contract
    # ------------------------------------------------------------------

    out = graph.to_dict()
    assert "nodes" in out
    assert "edges" in out
    assert len(out["edges"]) == 2

    edge_types = {e["type"] for e in out["edges"]}
    assert edge_types == {"topicref", "image"}


def test_graph_from_discovery_rejects_unknown_source() -> None:
    """
    Graph must fail fast if a relationship references an unknown source.
    """
    artifacts = [{"path": "index.ditamap", "artifact_type": "map"}]

    relationships = [
        {
            "source": "missing.ditamap",
            "target": "index.ditamap",
            "type": "topicref",
            "pattern_id": "x",
        }
    ]

    with pytest.raises(ValueError):
        DependencyGraph.from_discovery(
            artifacts=artifacts,
            relationships=relationships,
        )


def test_graph_from_discovery_rejects_unknown_target() -> None:
    """
    Graph must fail fast if a relationship references an unknown target.
    """
    artifacts = [{"path": "index.ditamap", "artifact_type": "map"}]

    relationships = [
        {
            "source": "index.ditamap",
            "target": "topics/missing.dita",
            "type": "topicref",
            "pattern_id": "x",
        }
    ]

    with pytest.raises(ValueError):
        DependencyGraph.from_discovery(
            artifacts=artifacts,
            relationships=relationships,
        )


def test_graph_handles_empty_relationships() -> None:
    """
    Graph with no relationships should still contain nodes.
    """
    artifacts = [
        {"path": "a.dita", "artifact_type": "topic"},
        {"path": "b.dita", "artifact_type": "topic"},
    ]

    graph = DependencyGraph.from_discovery(
        artifacts=artifacts,
        relationships=[],
    )

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 0


# ---------------------------------------------------------------------------
# Navigation helpers
# ---------------------------------------------------------------------------


def test_graph_navigation_helpers() -> None:
    artifacts = [
        {"path": "map.ditamap", "artifact_type": "map"},
        {"path": "a.dita", "artifact_type": "topic"},
        {"path": "b.dita", "artifact_type": "topic"},
    ]

    relationships = [
        {
            "source": "map.ditamap",
            "target": "a.dita",
            "type": "topicref",
            "pattern_id": "x",
        },
        {
            "source": "map.ditamap",
            "target": "b.dita",
            "type": "topicref",
            "pattern_id": "y",
        },
    ]

    graph = DependencyGraph.from_discovery(
        artifacts=artifacts,
        relationships=relationships,
    )

    outgoing = graph.outgoing("map.ditamap")
    incoming = graph.incoming("a.dita")

    assert len(outgoing) == 2
    assert len(incoming) == 1
    assert incoming[0].target == "a.dita"


# ---------------------------------------------------------------------------
# Serialization Roundtrip
# ---------------------------------------------------------------------------


def test_graph_roundtrip_serialization() -> None:
    artifacts = [
        {"path": "index.ditamap", "artifact_type": "map"},
        {"path": "topics/a.dita", "artifact_type": "topic"},
    ]

    relationships = [
        {
            "source": "index.ditamap",
            "target": "topics/a.dita",
            "type": "topicref",
            "pattern_id": "x",
        }
    ]

    graph = DependencyGraph.from_discovery(
        artifacts=artifacts,
        relationships=relationships,
    )

    data = graph.to_dict()
    loaded = DependencyGraph.from_dict(data)

    assert sorted(loaded.nodes) == sorted(graph.nodes)
    assert len(loaded.edges) == 1
    assert loaded.edges[0].edge_type == "topicref"