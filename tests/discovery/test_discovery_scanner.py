"""
Tests for the DiscoveryScanner.

These tests validate that the scanner:

- Detects artifacts (maps, topics, media)
- Extracts explicit XML relationships
- Builds a valid dependency graph
- Annotates structural node_count
- Selects exactly one MAIN map using deterministic logic
"""

from pathlib import Path

from dita_package_processor.discovery.scanner import DiscoveryScanner
from dita_package_processor.knowledge.map_types import MapType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_main_maps(inventory):
    """Return all artifacts classified as MapType.MAIN."""
    return [
        a
        for a in inventory.artifacts
        if a.artifact_type == "map"
        and a.classification == MapType.MAIN
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_scanner_detects_artifacts(tmp_path: Path) -> None:
    """Scanner must detect artifacts even when no relationships exist."""

    (tmp_path / "Main.ditamap").write_text("<map/>", encoding="utf-8")
    (tmp_path / "topic.dita").write_text("<topic/>", encoding="utf-8")

    scanner = DiscoveryScanner(tmp_path)
    inventory = scanner.scan()

    assert len(inventory.artifacts) == 2

    paths = {str(a.path) for a in inventory.artifacts}
    assert "Main.ditamap" in paths
    assert "topic.dita" in paths

    # MAIN normalization
    main_maps = _get_main_maps(inventory)
    assert len(main_maps) == 1
    assert str(main_maps[0].path) == "Main.ditamap"

    # Graph integrity
    assert inventory.graph is not None
    assert len(inventory.graph.nodes) == 2
    assert len(inventory.graph.edges) == 0

    # node_count annotation
    assert "node_count" in main_maps[0].metadata
    assert main_maps[0].metadata["node_count"] == 1


def test_scanner_extracts_relationships_and_graph(tmp_path: Path) -> None:
    """Scanner must extract relationships and build a dependency graph."""

    (tmp_path / "media").mkdir()
    (tmp_path / "topics").mkdir()

    (tmp_path / "media" / "image.png").write_bytes(b"\x89PNG")

    (tmp_path / "topics" / "a.dita").write_text(
        """
        <topic>
            <image href="../media/image.png"/>
        </topic>
        """,
        encoding="utf-8",
    )

    (tmp_path / "Main.ditamap").write_text(
        """
        <map>
            <topicref href="topics/a.dita"/>
        </map>
        """,
        encoding="utf-8",
    )

    scanner = DiscoveryScanner(tmp_path)
    inventory = scanner.scan()

    assert len(inventory.artifacts) == 3

    paths = {str(a.path) for a in inventory.artifacts}
    assert "Main.ditamap" in paths
    assert "topics/a.dita" in paths
    assert "media/image.png" in paths

    # MAIN resolution
    main_maps = _get_main_maps(inventory)
    assert len(main_maps) == 1
    assert str(main_maps[0].path) == "Main.ditamap"

    # Graph validation
    graph = inventory.graph
    assert graph is not None

    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2

    edge_sources = {e.source for e in graph.edges}
    edge_targets = {e.target for e in graph.edges}
    edge_types = {e.edge_type for e in graph.edges}

    assert "Main.ditamap" in edge_sources
    assert "topics/a.dita" in edge_targets
    assert "topicref" in edge_types

    assert "topics/a.dita" in edge_sources
    assert "media/image.png" in edge_targets
    assert "image" in edge_types

    # node_count should reflect full reachable graph
    main_map = main_maps[0]
    assert "node_count" in main_map.metadata
    assert main_map.metadata["node_count"] == 3


def test_scanner_promotes_single_map_to_main(tmp_path: Path) -> None:
    """If exactly one map exists and none classified, it must be promoted."""

    (tmp_path / "only.ditamap").write_text("<map/>", encoding="utf-8")

    scanner = DiscoveryScanner(tmp_path)
    inventory = scanner.scan()

    main_maps = _get_main_maps(inventory)

    assert len(main_maps) == 1
    assert str(main_maps[0].path) == "only.ditamap"
    assert main_maps[0].classification == MapType.MAIN
    assert main_maps[0].metadata["node_count"] == 1


def test_scanner_selects_map_with_highest_node_count(tmp_path: Path) -> None:
    """
    If multiple maps exist and none classified MAIN,
    scanner must select the structurally richest map.
    """

    (tmp_path / "topics").mkdir()

    # Map A references a topic
    (tmp_path / "a.ditamap").write_text(
        """
        <map>
            <topicref href="topics/a.dita"/>
        </map>
        """,
        encoding="utf-8",
    )

    (tmp_path / "topics" / "a.dita").write_text(
        "<topic/>",
        encoding="utf-8",
    )

    # Map B is empty
    (tmp_path / "b.ditamap").write_text("<map/>", encoding="utf-8")

    scanner = DiscoveryScanner(tmp_path)
    inventory = scanner.scan()

    main_maps = _get_main_maps(inventory)

    assert len(main_maps) == 1
    assert str(main_maps[0].path) == "a.ditamap"
    assert main_maps[0].classification == MapType.MAIN

    # Ensure structural difference is reflected
    assert main_maps[0].metadata["node_count"] == 2