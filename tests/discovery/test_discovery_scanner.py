"""
Tests for the DiscoveryScanner.

These tests validate that the scanner:

- Detects artifacts (maps, topics, media)
- Extracts explicit XML relationships
- Normalizes relationships into graph edges
- Builds a valid dependency graph
- Guarantees exactly one MAIN_MAP

The dependency graph is the sole source of relationship truth.
"""

from pathlib import Path

from dita_package_processor.discovery.scanner import DiscoveryScanner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_main_maps(inventory):
    """Return all artifacts classified as MAIN_MAP."""
    return [
        a
        for a in inventory.artifacts
        if a.artifact_type == "map"
        and str(a.classification).upper() == "MAIN_MAP"
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_scanner_detects_artifacts(tmp_path: Path) -> None:
    """
    Scanner must detect artifacts even when no relationships exist.
    """

    (tmp_path / "Main.ditamap").write_text("<map/>", encoding="utf-8")
    (tmp_path / "topic.dita").write_text("<topic/>", encoding="utf-8")

    scanner = DiscoveryScanner(tmp_path)
    inventory = scanner.scan()

    # ------------------------------------------------------------------
    # Artifact inventory
    # ------------------------------------------------------------------

    assert len(inventory.artifacts) == 2

    paths = {str(a.path) for a in inventory.artifacts}
    assert "Main.ditamap" in paths
    assert "topic.dita" in paths

    # ------------------------------------------------------------------
    # MAIN_MAP normalization (new behavior)
    # ------------------------------------------------------------------

    main_maps = _get_main_maps(inventory)
    assert len(main_maps) == 1
    assert str(main_maps[0].path) == "Main.ditamap"

    # ------------------------------------------------------------------
    # Graph
    # ------------------------------------------------------------------

    assert inventory.graph is not None
    assert len(inventory.graph.nodes) == 2
    assert len(inventory.graph.edges) == 0


def test_scanner_extracts_relationships_and_graph(tmp_path: Path) -> None:
    """
    Scanner must extract relationships and build a dependency graph.
    """

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

    # ------------------------------------------------------------------
    # Artifacts
    # ------------------------------------------------------------------

    assert len(inventory.artifacts) == 3

    paths = {str(a.path) for a in inventory.artifacts}
    assert "Main.ditamap" in paths
    assert "topics/a.dita" in paths
    assert "media/image.png" in paths

    # MAIN_MAP normalization
    main_maps = _get_main_maps(inventory)
    assert len(main_maps) == 1
    assert str(main_maps[0].path) == "Main.ditamap"

    # ------------------------------------------------------------------
    # Graph
    # ------------------------------------------------------------------

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


def test_scanner_promotes_single_map_to_main(tmp_path: Path) -> None:
    """
    If exactly one map exists and none classified,
    it must be promoted to MAIN_MAP.
    """

    (tmp_path / "only.ditamap").write_text("<map/>", encoding="utf-8")

    scanner = DiscoveryScanner(tmp_path)
    inventory = scanner.scan()

    main_maps = _get_main_maps(inventory)

    assert len(main_maps) == 1
    assert str(main_maps[0].path) == "only.ditamap"


def test_scanner_fallback_selects_deterministic_map(tmp_path: Path) -> None:
    """
    If multiple maps exist and none classified,
    scanner must deterministically promote the first path alphabetically.
    """

    (tmp_path / "b.ditamap").write_text("<map/>", encoding="utf-8")
    (tmp_path / "a.ditamap").write_text("<map/>", encoding="utf-8")

    scanner = DiscoveryScanner(tmp_path)
    inventory = scanner.scan()

    main_maps = _get_main_maps(inventory)

    assert len(main_maps) == 1
    assert str(main_maps[0].path) == "a.ditamap"