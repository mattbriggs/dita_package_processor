"""
Tests for PlanningInputNormalizer (legacy discovery compatibility layer).

These tests enforce that:
- Planning never consumes raw discovery directly
- Media artifacts never participate in planning topology
- Graph structure is validated strictly
- Paths are canonicalized
- No guessing or inference is permitted
"""

from __future__ import annotations

import pytest

from dita_package_processor.planning.input_normalizer import (
    PlanningInputNormalizer,
    normalize,
)


# ---------------------------------------------------------------------------
# Positive normalization behavior
# ---------------------------------------------------------------------------


def test_normalizer_drops_media_nodes() -> None:
    discovery = {
        "artifacts": [
            {"path": "index.ditamap", "artifact_type": "map"},
            {"path": "topics/a.dita", "artifact_type": "topic"},
            {
                "path": "media/logo.png",
                "artifact_type": "media",
                "size_bytes": 100,
                "extension": "png",
            },
        ],
        "graph": {
            "nodes": [
                "index.ditamap",
                "topics/a.dita",
                "media/logo.png",
            ],
            "edges": [],
        },
    }

    normalized = PlanningInputNormalizer.normalize(discovery)

    nodes = normalized["graph"]["nodes"]
    assert "index.ditamap" in nodes
    assert "topics/a.dita" in nodes
    assert "media/logo.png" not in nodes


def test_normalizer_drops_media_edges() -> None:
    discovery = {
        "artifacts": [
            {"path": "index.ditamap", "artifact_type": "map"},
            {"path": "topics/a.dita", "artifact_type": "topic"},
            {"path": "media/logo.png", "artifact_type": "media"},
        ],
        "graph": {
            "nodes": [
                "index.ditamap",
                "topics/a.dita",
                "media/logo.png",
            ],
            "edges": [
                {
                    "source": "index.ditamap",
                    "target": "media/logo.png",
                    "type": "image",
                    "pattern_id": "img",
                },
                {
                    "source": "index.ditamap",
                    "target": "topics/a.dita",
                    "type": "topicref",
                    "pattern_id": "tr",
                },
            ],
        },
    }

    normalized = PlanningInputNormalizer.normalize(discovery)

    edges = normalized["graph"]["edges"]
    assert len(edges) == 1
    assert edges[0]["target"] == "topics/a.dita"


def test_normalizer_preserves_semantic_edges() -> None:
    discovery = {
        "artifacts": [
            {"path": "index.ditamap", "artifact_type": "map"},
            {"path": "topics/a.dita", "artifact_type": "topic"},
        ],
        "graph": {
            "nodes": [
                "index.ditamap",
                "topics/a.dita",
            ],
            "edges": [
                {
                    "source": "index.ditamap",
                    "target": "topics/a.dita",
                    "type": "topicref",
                    "pattern_id": "x",
                }
            ],
        },
    }

    normalized = PlanningInputNormalizer.normalize(discovery)
    assert normalized["graph"]["edges"] == discovery["graph"]["edges"]


def test_normalizer_normalizes_paths() -> None:
    discovery = {
        "artifacts": [
            {"path": "./index.ditamap", "artifact_type": "map"},
        ],
        "graph": {
            "nodes": [
                "./index.ditamap",
            ],
            "edges": [],
        },
    }

    normalized = PlanningInputNormalizer.normalize(discovery)

    assert normalized["graph"]["nodes"] == ["index.ditamap"]
    assert normalized["artifacts"][0]["path"] == "index.ditamap"


def test_functional_alias_matches_class_method() -> None:
    discovery = {
        "artifacts": [
            {"path": "index.ditamap", "artifact_type": "map"},
        ],
        "graph": {
            "nodes": ["index.ditamap"],
            "edges": [],
        },
    }

    a = PlanningInputNormalizer.normalize(discovery)
    b = normalize(discovery)
    assert a == b


# ---------------------------------------------------------------------------
# Structural validation
# ---------------------------------------------------------------------------


def test_normalizer_fails_on_non_mapping_input() -> None:
    with pytest.raises(ValueError, match="Discovery input must be an object"):
        PlanningInputNormalizer.normalize("not a dict")  # type: ignore[arg-type]


def test_normalizer_fails_when_artifacts_not_list() -> None:
    with pytest.raises(ValueError, match="discovery.artifacts must be a list"):
        PlanningInputNormalizer.normalize(
            {"artifacts": {}, "graph": {"nodes": [], "edges": []}}
        )


def test_normalizer_fails_when_graph_not_object() -> None:
    with pytest.raises(ValueError, match="discovery.graph must be an object"):
        PlanningInputNormalizer.normalize(
            {"artifacts": [], "graph": []}
        )


def test_normalizer_fails_when_nodes_not_list() -> None:
    with pytest.raises(ValueError, match="discovery.graph.nodes must be a list"):
        PlanningInputNormalizer.normalize(
            {"artifacts": [], "graph": {"nodes": {}, "edges": []}}
        )


def test_normalizer_fails_when_edges_not_list() -> None:
    with pytest.raises(ValueError, match="discovery.graph.edges must be a list"):
        PlanningInputNormalizer.normalize(
            {"artifacts": [], "graph": {"nodes": [], "edges": {}}}
        )


def test_normalizer_fails_on_orphan_node() -> None:
    discovery = {
        "artifacts": [
            {"path": "index.ditamap", "artifact_type": "map"},
        ],
        "graph": {
            "nodes": [
                "index.ditamap",
                "missing/topic.dita",
            ],
            "edges": [],
        },
    }

    with pytest.raises(ValueError, match="missing/topic.dita"):
        PlanningInputNormalizer.normalize(discovery)


def test_normalizer_fails_on_orphan_edge() -> None:
    discovery = {
        "artifacts": [
            {"path": "index.ditamap", "artifact_type": "map"},
        ],
        "graph": {
            "nodes": ["index.ditamap"],
            "edges": [
                {
                    "source": "index.ditamap",
                    "target": "missing/topic.dita",
                    "type": "topicref",
                    "pattern_id": "x",
                }
            ],
        },
    }

    with pytest.raises(ValueError, match="missing/topic.dita"):
        PlanningInputNormalizer.normalize(discovery)


def test_normalizer_fails_on_invalid_artifact_shape() -> None:
    discovery = {
        "artifacts": [
            {"artifact_type": "map"},  # missing path
        ],
        "graph": {
            "nodes": [],
            "edges": [],
        },
    }

    with pytest.raises(ValueError, match="missing required fields"):
        PlanningInputNormalizer.normalize(discovery)


def test_normalizer_fails_on_invalid_path_type() -> None:
    discovery = {
        "artifacts": [
            {"path": None, "artifact_type": "map"},  # type: ignore[arg-type]
        ],
        "graph": {
            "nodes": [],
            "edges": [],
        },
    }

    with pytest.raises(ValueError, match="Invalid artifact path"):
        PlanningInputNormalizer.normalize(discovery)