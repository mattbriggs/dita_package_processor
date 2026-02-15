"""
Tests for planning contract failure modes.

These tests prove the planning contract boundary is hostile by design.

Anything that:

- looks like discovery
- is partially formed
- is ambiguous
- violates schema intent

must fail immediately and loudly.

There are two enforcement layers:

1. Discovery → Planning normalization (raises PlanningContractError)
2. Planner input wall (rejects anything not a PlanningInput)
"""

from __future__ import annotations

import pytest

from dita_package_processor.planning.contracts.discovery_to_planning import (
    normalize_discovery_report,
)
from dita_package_processor.planning.contracts.errors import (
    PlanningContractError,
)
from dita_package_processor.planning.planner import Planner


# =============================================================================
# Discovery → Planning contract failures
# =============================================================================


def test_discovery_contract_rejects_non_object() -> None:
    """Normalization must reject non-dict discovery payloads."""
    with pytest.raises(
        PlanningContractError,
        match=r"Discovery payload must be an object",
    ):
        normalize_discovery_report("not-a-dict")  # type: ignore[arg-type]


def test_discovery_contract_rejects_artifact_not_object() -> None:
    """Artifacts must be objects; lists of strings must fail."""
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
    """Relationships must be objects; lists of strings must fail."""
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
    """Empty artifact paths must fail contract validation."""
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
        match=r"artifact\[0\] invalid",
    ):
        normalize_discovery_report(discovery)


def test_discovery_contract_rejects_invalid_artifact_type() -> None:
    """Invalid artifact types must fail normalization."""
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

    with pytest.raises(
        PlanningContractError,
        match=r"artifact\[0\]\.artifact_type invalid",
    ):
        normalize_discovery_report(discovery)


def test_discovery_contract_rejects_non_string_classification() -> None:
    """
    Non-string classification values must fail MAIN selection.
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


def test_discovery_contract_rejects_missing_main_map() -> None:
    """
    Exactly one MAIN map must exist.
    """
    discovery = {
        "artifacts": [
            {
                "path": "index.ditamap",
                "artifact_type": "map",
                "classification": None,
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


def test_planner_rejects_raw_dict_input() -> None:
    """
    Planner must reject raw dict inputs.

    The planner boundary accepts only PlanningInput.
    """
    planner = Planner()

    with pytest.raises(
        TypeError,
        match=r"Planner\.plan\(\) requires PlanningInput",
    ):
        planner.plan({"artifacts": []})  # type: ignore[arg-type]


def test_planner_rejects_none() -> None:
    """Planner must reject None."""
    planner = Planner()

    with pytest.raises(
        TypeError,
        match=r"Planner\.plan\(\) requires PlanningInput",
    ):
        planner.plan(None)  # type: ignore[arg-type]


def test_planner_rejects_discovery_like_shape() -> None:
    """
    Planner must reject discovery-shaped dicts regardless of structure.
    """
    planner = Planner()

    discovery_like = {
        "artifacts": [],
        "relationships": [],
        "summary": {},
        "graph": {"nodes": [], "edges": []},
    }

    with pytest.raises(
        TypeError,
        match=r"Planner\.plan\(\) requires PlanningInput",
    ):
        planner.plan(discovery_like)  # type: ignore[arg-type]


def test_planner_requires_planninginput_instance() -> None:
    """
    Even structurally valid dicts must be rejected.

    Only a PlanningInput object is accepted.
    """
    planner = Planner()

    structurally_valid_dict = {
        "contract_version": "1.0",
        "main_map": "index.ditamap",
        "artifacts": [],
        "relationships": [],
    }

    with pytest.raises(
        TypeError,
        match=r"Planner\.plan\(\) requires PlanningInput",
    ):
        planner.plan(structurally_valid_dict)  # type: ignore[arg-type]