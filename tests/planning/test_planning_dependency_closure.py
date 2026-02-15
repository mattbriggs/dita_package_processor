"""
Tests for dependency closure behavior in planning.

These tests verify that the :class:`GraphPlanner`:

- Walks the full dependency graph starting from the root node.
- Includes all reachable artifacts.
- Excludes unreachable artifacts.
- Does not duplicate nodes.
- Produces deterministic traversal order.

Tests operate strictly through the public graph construction API
(:meth:`DependencyGraph.from_dict`). No internal mutation is permitted.
"""

from __future__ import annotations

from typing import Iterable, Tuple

from dita_package_processor.discovery.graph import DependencyGraph
from dita_package_processor.planning.graph_planner import GraphPlanner


# =============================================================================
# Helpers
# =============================================================================


def make_graph(edges: Iterable[Tuple[str, str]]) -> DependencyGraph:
    """
    Construct a :class:`DependencyGraph` using the serialized schema format.

    Parameters
    ----------
    edges:
        Iterable of (source, target) tuples.

    Returns
    -------
    DependencyGraph
        Fully constructed graph instance.
    """
    return DependencyGraph.from_dict(
        {
            "nodes": sorted({node for edge in edges for node in edge}),
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


def make_planner(graph: DependencyGraph) -> GraphPlanner:
    """
    Construct :class:`GraphPlanner` using serialized relationship dictionaries.

    The planner layer must not depend on discovery model classes.
    """
    return GraphPlanner(
        nodes=graph.nodes,
        relationships=[edge.to_dict() for edge in graph.edges],
    )


# =============================================================================
# Tests
# =============================================================================


def test_dependency_closure_simple_chain() -> None:
    """
    A → B → C must include all three nodes in order.
    """
    graph = make_graph(
        [
            ("A", "B"),
            ("B", "C"),
        ]
    )

    planner = make_planner(graph)
    result = planner.plan()

    assert result == ["A", "B", "C"]


def test_dependency_closure_branching_graph() -> None:
    """
    Branching graph must produce deterministic depth-first traversal.

    Graph:

        A → B
        A → C
        B → D
        C → E

    Expected:

        A → B → D → C → E
    """
    graph = make_graph(
        [
            ("A", "B"),
            ("A", "C"),
            ("B", "D"),
            ("C", "E"),
        ]
    )

    planner = make_planner(graph)
    result = planner.plan()

    assert result == ["A", "B", "D", "C", "E"]


def test_dependency_closure_deduplicates_nodes() -> None:
    """
    Multiple paths to the same node must not produce duplicates.

    Graph:

        A → B
        A → C
        B → C
    """
    graph = make_graph(
        [
            ("A", "B"),
            ("A", "C"),
            ("B", "C"),
        ]
    )

    planner = make_planner(graph)
    result = planner.plan()

    assert result == ["A", "B", "C"]
    assert len(result) == len(set(result))


def test_dependency_closure_excludes_unreachable_nodes() -> None:
    """
    Nodes not reachable from the root must be excluded.

    Graph:

        A → B
        X → Y   (disconnected)
    """
    graph = make_graph(
        [
            ("A", "B"),
            ("X", "Y"),
        ]
    )

    planner = make_planner(graph)
    result = planner.plan()

    assert result == ["A", "B"]
    assert "X" not in result
    assert "Y" not in result


def test_dependency_closure_order_is_stable() -> None:
    """
    Traversal order must be stable across multiple invocations.
    """
    graph = make_graph(
        [
            ("Root", "b"),
            ("Root", "a"),
            ("a", "c"),
            ("b", "d"),
        ]
    )

    planner = make_planner(graph)

    first = planner.plan()
    second = planner.plan()

    assert first == second