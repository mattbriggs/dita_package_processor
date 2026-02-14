"""
Tests for dependency closure behavior in planning.

These tests ensure that:

- The planner walks the full dependency graph starting from the root.
- All reachable artifacts are included.
- No unreachable artifacts are included.
- Nodes are not duplicated.
- Traversal order is deterministic.

These tests operate strictly through the public graph construction API
(DependencyGraph.from_dict). No mutation is allowed.
"""

from __future__ import annotations

from dita_package_processor.discovery.graph import DependencyGraph
from dita_package_processor.planning.graph_planner import GraphPlanner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_graph(edges: list[tuple[str, str]]) -> DependencyGraph:
    """
    Build a DependencyGraph using the real serialized schema.

    Every edge requires:
      - source
      - target
      - type
      - pattern_id
    """
    return DependencyGraph.from_dict(
        {
            "nodes": sorted({n for e in edges for n in e}),
            "edges": [
                {
                    "source": src,
                    "target": tgt,
                    "type": "contains",
                    "pattern_id": "test",
                }
                for src, tgt in edges
            ],
        }
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_dependency_closure_simple_chain() -> None:
    """
    A → B → C should include all three in order.
    """
    graph = make_graph([
        ("A", "B"),
        ("B", "C"),
    ])

    planner = GraphPlanner(graph)
    result = planner.plan()

    assert result == ["A", "B", "C"]


def test_dependency_closure_branching_graph() -> None:
    """
    A → B
    A → C
    B → D
    C → E

    Deterministic depth-first:
    A → B → D → C → E
    """
    graph = make_graph([
        ("A", "B"),
        ("A", "C"),
        ("B", "D"),
        ("C", "E"),
    ])

    planner = GraphPlanner(graph)
    result = planner.plan()

    assert result == ["A", "B", "D", "C", "E"]


def test_dependency_closure_deduplicates_nodes() -> None:
    """
    Multiple paths to the same node must not cause duplicates.

    A → B
    A → C
    B → C
    """
    graph = make_graph([
        ("A", "B"),
        ("A", "C"),
        ("B", "C"),
    ])

    planner = GraphPlanner(graph)
    result = planner.plan()

    assert result == ["A", "B", "C"]
    assert len(result) == len(set(result))


def test_dependency_closure_excludes_unreachable_nodes() -> None:
    """
    Nodes not reachable from the root must not appear.

    Rooted graph:
        A → B

    Disconnected subgraph:
        X → Y
    """
    graph = make_graph([
        ("A", "B"),
        ("X", "Y"),
    ])

    planner = GraphPlanner(graph)
    result = planner.plan()

    assert result == ["A", "B"]
    assert "X" not in result
    assert "Y" not in result


def test_dependency_closure_order_is_stable() -> None:
    """
    Order must not change between runs for the same graph.
    """
    graph = make_graph([
        ("Root", "b"),
        ("Root", "a"),
        ("a", "c"),
        ("b", "d"),
    ])

    planner = GraphPlanner(graph)

    first = planner.plan()
    second = planner.plan()

    assert first == second