"""
Tests for planning contract failure modes.

These tests exist to prove the planning contract boundary is *hostile by
design*. Anything that:

- looks like discovery
- is partially formed
- is ambiguous
- violates schema intent

must fail immediately and loudly.

There are two enforcement layers:

1. Discovery → Planning normalization (raises :class:`PlanningContractError`)
2. Planner input wall (rejects anything not a :class:`PlanningInput`)
"""

from __future__ import annotations

import pytest

from dita_package_processor.planning.contracts.discovery_to_planning import (
    normalize_discovery_report,
)
from dita_package_processor.planning.contracts.errors import PlanningContractError
from dita_package_processor.planning.planner import Planner


# =============================================================================
# Discovery → Planning contract failures
# =============================================================================


def test_discovery_contract_rejects_non_object() -> None:
    """
    Normalization must reject non-dict discovery payloads.
    """
    with pytest.raises(PlanningContractError):
        normalize_discovery_report("not-a-dict")  # type: ignore[arg-type]


def test_discovery_contract_rejects_artifact_not_object() -> None:
    """
    Artifacts must be objects; lists of strings must fail.
    """
    discovery = {
        "artifacts": ["not-an-object"],
        "relationships": [],
        "summary": {},
    }

    with pytest.raises(
        PlanningContractError,
        match=r"artifact\[0\] must be an object",
    ):
        normalize_discovery_report(discovery)


def test_discovery_contract_rejects_relationship_not_object() -> None:
    """
    Relationships must be objects; lists of strings must fail.
    """
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
    """
    Empty artifact paths must fail contract validation.

    Current behavior:
    - The MAIN map selection will use the empty string as ``main_map``.
    - JSON Schema validation rejects ``main_map`` due to ``minLength``.
    """
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

    with pytest.raises(
        PlanningContractError,
        match=r"PlanningInput schema violation: .*non-empty",
    ):
        normalize_discovery_report(discovery)


def test_discovery_contract_rejects_invalid_artifact_type() -> None:
    """
    Invalid artifact types must fail normalization.
    """
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

    with pytest.raises(PlanningContractError, match=r"artifact_type invalid"):
        normalize_discovery_report(discovery)


def test_discovery_contract_rejects_non_string_classification() -> None:
    """
    Non-string classification values must fail normalization.

    Current behavior:
    - A non-string classification prevents MAIN map selection.
    - The normalizer fails with MAIN map selection error.
    """
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
        match=r"Exactly one artifact must be classified as MAIN map",
    ):
        normalize_discovery_report(discovery)


# =============================================================================
# Planner input wall failures
# =============================================================================


def test_planner_rejects_discovery_shaped_input() -> None:
    """
    Planner must reject raw discovery-like dict inputs.

    The planner boundary accepts only :class:`PlanningInput`.
    """
    planner = Planner()

    discovery_like = {
        "artifacts": [],
        "relationships": [],
        "summary": {},
    }

    with pytest.raises(
        TypeError,
        match=r"Planner\.plan\(\) requires PlanningInput, not raw dict",
    ):
        planner.plan(discovery_like)  # type: ignore[arg-type]


def test_planner_rejects_missing_graph_key() -> None:
    """
    Planner must reject dict inputs regardless of internal shape.
    """
    planner = Planner()

    bad = {
        "artifacts": [],
    }

    with pytest.raises(
        TypeError,
        match=r"Planner\.plan\(\) requires PlanningInput, not raw dict",
    ):
        planner.plan(bad)  # type: ignore[arg-type]


def test_planner_rejects_missing_artifacts_key() -> None:
    """
    Planner must reject dict inputs regardless of internal shape.
    """
    planner = Planner()

    bad = {
        "graph": {"nodes": [], "edges": []},
    }

    with pytest.raises(
        TypeError,
        match=r"Planner\.plan\(\) requires PlanningInput, not raw dict",
    ):
        planner.plan(bad)  # type: ignore[arg-type]


def test_planner_rejects_graph_without_nodes_and_edges() -> None:
    """
    Planner must reject dict inputs regardless of internal shape.
    """
    planner = Planner()

    bad = {
        "artifacts": [],
        "graph": {},
    }

    with pytest.raises(
        TypeError,
        match=r"Planner\.plan\(\) requires PlanningInput, not raw dict",
    ):
        planner.plan(bad)  # type: ignore[arg-type]


def test_planner_rejects_non_list_nodes() -> None:
    """
    Planner must reject dict inputs regardless of internal shape.
    """
    planner = Planner()

    bad = {
        "artifacts": [],
        "graph": {
            "nodes": {},
            "edges": [],
        },
    }

    with pytest.raises(
        TypeError,
        match=r"Planner\.plan\(\) requires PlanningInput, not raw dict",
    ):
        planner.plan(bad)  # type: ignore[arg-type]


def test_planner_rejects_non_list_edges() -> None:
    """
    Planner must reject dict inputs regardless of internal shape.
    """
    planner = Planner()

    bad = {
        "artifacts": [],
        "graph": {
            "nodes": [],
            "edges": {},
        },
    }

    with pytest.raises(
        TypeError,
        match=r"Planner\.plan\(\) requires PlanningInput, not raw dict",
    ):
        planner.plan(bad)  # type: ignore[arg-type]