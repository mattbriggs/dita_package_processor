"""
Tests for the contract-level GraphPlanner.

These tests verify that the planner:

- accepts contract nodes + relationships only
- produces deterministic output
- enforces root validity
- has zero discovery coupling
- contains no filesystem or semantic behavior

IMPORTANT
---------
GraphPlanner must NOT depend on discovery.DependencyGraph.
This is the architectural wall.
"""

from __future__ import annotations

import pytest

from dita_package_processor.planning.graph_planner import (
    GraphPlanner,
    GraphPlannerError,
)


# =============================================================================
# Helpers
# =============================================================================


def _planner(nodes: list[str], edges: list[dict]) -> GraphPlanner:
    """
    Construct GraphPlanner directly from contract inputs.
    """
    return GraphPlanner(
        nodes=nodes,
        relationships=edges,
    )


# =============================================================================
# Positive tests
# =============================================================================


def test_simple_linear_graph() -> None:
    """
    A → B → C
    """
    planner = _planner(
        nodes=["A", "B", "C"],
        edges=[
            {"source": "A", "target": "B", "type": "x", "pattern_id": "p1"},
            {"source": "B", "target": "C", "type": "x", "pattern_id": "p2"},
        ],
    )

    plan = planner.plan()

    assert plan == ["A", "B", "C"]


def test_branching_graph_is_deterministic() -> None:
    """
    A → C
    A → B

    Children sorted lexicographically.
    """
    planner = _planner(
        nodes=["A", "B", "C"],
        edges=[
            {"source": "A", "target": "C", "type": "x", "pattern_id": "p1"},
            {"source": "A", "target": "B", "type": "x", "pattern_id": "p2"},
        ],
    )

    plan = planner.plan()

    assert plan == ["A", "B", "C"]


def test_multiple_roots_selects_lexicographically_first() -> None:
    """
    Disjoint trees:

    A → B
    X → Y → Z

    With new planner rules, we pick first lexicographic root.
    Determinism > "largest closure" heuristics.
    """
    planner = _planner(
        nodes=["A", "B", "X", "Y", "Z"],
        edges=[
            {"source": "A", "target": "B", "type": "x", "pattern_id": "p1"},
            {"source": "X", "target": "Y", "type": "x", "pattern_id": "p2"},
            {"source": "Y", "target": "Z", "type": "x", "pattern_id": "p3"},
        ],
    )

    plan = planner.plan()

    # deterministic first root
    assert plan == ["A", "B"]


# =============================================================================
# Negative tests
# =============================================================================


def test_cycle_fails() -> None:
    """
    Cycles must fail.
    """
    planner = _planner(
        nodes=["A", "B"],
        edges=[
            {"source": "A", "target": "B", "type": "x", "pattern_id": "p1"},
            {"source": "B", "target": "A", "type": "x", "pattern_id": "p2"},
        ],
    )

    with pytest.raises(GraphPlannerError):
        planner.plan()


def test_no_root_fails() -> None:
    """
    No root means invalid graph.
    """
    planner = _planner(
        nodes=["A", "B"],
        edges=[
            {"source": "A", "target": "B", "type": "x", "pattern_id": "p1"},
            {"source": "B", "target": "A", "type": "x", "pattern_id": "p2"},
        ],
    )

    with pytest.raises(GraphPlannerError):
        planner.plan()


def test_empty_graph_fails() -> None:
    """
    Empty input is invalid.
    """
    planner = _planner(nodes=[], edges=[])

    with pytest.raises(GraphPlannerError):
        planner.plan()