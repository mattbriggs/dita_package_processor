"""
Tests for planning contract failure modes.

These tests exist to prove the planning contract boundary is *hostile by design*.

Anything that:
- looks like discovery
- is partially formed
- is ambiguous
- violates schema intent

must fail immediately and loudly.
"""

from __future__ import annotations

import pytest

from dita_package_processor.planning.contracts.discovery_to_planning import (
    normalize_discovery_report,
)
from dita_package_processor.planning.contracts.errors import PlanningContractError
from dita_package_processor.planning.planner import Planner


# ---------------------------------------------------------------------------
# Discovery → Planning contract failures
# ---------------------------------------------------------------------------


def test_discovery_contract_rejects_non_object() -> None:
    with pytest.raises(PlanningContractError):
        normalize_discovery_report("not-a-dict")  # type: ignore[arg-type]


def test_discovery_contract_rejects_artifact_not_object() -> None:
    discovery = {
        "artifacts": ["not-an-object"],
        "relationships": [],
        "summary": {},
    }

    with pytest.raises(PlanningContractError, match="artifact\\[0\\] must be an object"):
        normalize_discovery_report(discovery)


def test_discovery_contract_rejects_relationship_not_object() -> None:
    discovery = {
        "artifacts": [
            {
                "path": "index.ditamap",
                "artifact_type": "map",
                "classification": "MAIN",
            }
        ],
        "relationships": ["not-an-object"],
        "summary": {},
    }

    with pytest.raises(
        PlanningContractError,
        match=r"relationship\[0\] must be an object",
    ):
        normalize_discovery_report(discovery)


def test_discovery_contract_rejects_empty_path() -> None:
    discovery = {
        "artifacts": [
            {
                "path": "",
                "artifact_type": "map",
                "classification": "MAIN",
            }
        ],
        "relationships": [],
        "summary": {},
    }

    with pytest.raises(PlanningContractError, match="path must be a non-empty string"):
        normalize_discovery_report(discovery)


def test_discovery_contract_rejects_invalid_artifact_type() -> None:
    discovery = {
        "artifacts": [
            {
                "path": "index.ditamap",
                "artifact_type": "banana",
                "classification": "MAIN",
            }
        ],
        "relationships": [],
        "summary": {},
    }

    with pytest.raises(PlanningContractError, match="artifact_type invalid"):
        normalize_discovery_report(discovery)


def test_discovery_contract_rejects_non_string_classification() -> None:
    discovery = {
        "artifacts": [
            {
                "path": "index.ditamap",
                "artifact_type": "map",
                "classification": 123,
            }
        ],
        "relationships": [],
        "summary": {},
    }

    with pytest.raises(
        PlanningContractError,
        match="classification must be string|null",
    ):
        normalize_discovery_report(discovery)


# ---------------------------------------------------------------------------
# Planner input wall failures
# ---------------------------------------------------------------------------


def test_planner_rejects_discovery_shaped_input() -> None:
    """
    Raw discovery has 'relationships' and 'summary', not 'graph'.
    Planner must reject this.
    """
    planner = Planner()

    discovery_like = {
        "artifacts": [],
        "relationships": [],
        "summary": {},
    }

    with pytest.raises(ValueError, match="missing required keys"):
        planner.plan(discovery_like)


def test_planner_rejects_missing_graph_key() -> None:
    planner = Planner()

    bad = {
        "artifacts": [],
    }

    with pytest.raises(ValueError, match="missing required keys"):
        planner.plan(bad)


def test_planner_rejects_missing_artifacts_key() -> None:
    planner = Planner()

    bad = {
        "graph": {"nodes": [], "edges": []},
    }

    with pytest.raises(ValueError, match="missing required keys"):
        planner.plan(bad)


def test_planner_rejects_graph_without_nodes_and_edges() -> None:
    planner = Planner()

    bad = {
        "artifacts": [],
        "graph": {},
    }

    with pytest.raises(ValueError, match="must contain 'nodes' and 'edges'"):
        planner.plan(bad)


def test_planner_rejects_non_list_nodes() -> None:
    planner = Planner()

    bad = {
        "artifacts": [],
        "graph": {
            "nodes": {},
            "edges": [],
        },
    }

    with pytest.raises(ValueError, match="graph.nodes must be a list"):
        planner.plan(bad)


def test_planner_rejects_non_list_edges() -> None:
    planner = Planner()

    bad = {
        "artifacts": [],
        "graph": {
            "nodes": [],
            "edges": {},
        },
    }

    with pytest.raises(ValueError, match="graph.edges must be a list"):
        planner.plan(bad)