"""
Tests for discovery → planning input normalization contract.

This module enforces the architectural wall between discovery and planning.

Philosophy
----------
Planning only distinguishes:

- MAIN
- not MAIN

All other classifications are deterministically collapsed to None.
"""

from __future__ import annotations

import pytest

from dita_package_processor.planning.contracts.discovery_to_planning import (
    normalize_discovery_report,
)
from dita_package_processor.planning.contracts.errors import PlanningContractError


# =============================================================================
# Fixtures
# =============================================================================


def _minimal_discovery() -> dict:
    """Return minimal valid discovery report."""
    return {
        "artifacts": [
            {
                "path": "index.ditamap",
                "artifact_type": "map",
                "classification": "MAIN",
                "metadata": {},
            },
            {
                "path": "topics/a.dita",
                "artifact_type": "topic",
                "classification": None,
                "metadata": {},
            },
        ],
        "relationships": [
            {
                "source": "index.ditamap",
                "target": "topics/a.dita",
                "type": "topicref",
                "pattern_id": "dita_map_topicref",
            }
        ],
        "summary": {},
    }


# =============================================================================
# Positive tests
# =============================================================================


def test_normalization_produces_planning_input_shape() -> None:
    planning_input = normalize_discovery_report(_minimal_discovery())
    data = planning_input.to_dict()

    assert data["contract_version"] == "planning.input.v1"
    assert data["main_map"] == "index.ditamap"
    assert isinstance(data["artifacts"], list)
    assert isinstance(data["relationships"], list)


def test_normalization_preserves_relationship_fields() -> None:
    planning_input = normalize_discovery_report(_minimal_discovery())
    rel = planning_input.to_dict()["relationships"][0]

    assert rel == {
        "source": "index.ditamap",
        "target": "topics/a.dita",
        "type": "topicref",
        "pattern_id": "dita_map_topicref",
    }


def test_main_map_alias_normalizes() -> None:
    """MAIN_MAP must normalize to MAIN deterministically."""
    discovery = _minimal_discovery()
    discovery["artifacts"][0]["classification"] = "MAIN_MAP"

    planning = normalize_discovery_report(discovery)

    assert planning.main_map == "index.ditamap"


def test_non_main_classification_collapses_to_none() -> None:
    """
    Any non-MAIN classification must normalize to None.

    Planning intentionally ignores semantic labels like
    GLOSSARY, REFERENCE, CONCEPT, etc.
    """
    discovery = _minimal_discovery()
    discovery["artifacts"].append(
        {
            "path": "topics/glossary.dita",
            "artifact_type": "topic",
            "classification": "GLOSSARY",
            "metadata": {},
        }
    )

    planning = normalize_discovery_report(discovery)

    classes = {a.path: a.classification for a in planning.artifacts}

    assert classes["topics/glossary.dita"] is None


# =============================================================================
# Contract wall tests
# =============================================================================


def test_fails_without_required_top_level_keys() -> None:
    with pytest.raises(PlanningContractError):
        normalize_discovery_report({})


def test_fails_on_non_list_artifacts() -> None:
    with pytest.raises(PlanningContractError, match="must be a list"):
        normalize_discovery_report(
            {"artifacts": {}, "relationships": [], "summary": {}}
        )


def test_fails_on_non_list_relationships() -> None:
    with pytest.raises(PlanningContractError, match="must be a list"):
        normalize_discovery_report(
            {"artifacts": [], "relationships": {}, "summary": {}}
        )


def test_fails_when_no_main_map_present() -> None:
    bad = _minimal_discovery()
    bad["artifacts"][0]["classification"] = None

    with pytest.raises(
        PlanningContractError,
        match="Exactly one artifact must be classified as MAIN map",
    ):
        normalize_discovery_report(bad)


def test_fails_when_multiple_main_maps_present() -> None:
    bad = _minimal_discovery()
    bad["artifacts"].append(
        {
            "path": "other.ditamap",
            "artifact_type": "map",
            "classification": "MAIN",
            "metadata": {},
        }
    )

    with pytest.raises(
        PlanningContractError,
        match="Exactly one artifact must be classified as MAIN map",
    ):
        normalize_discovery_report(bad)


def test_fails_when_relationship_references_unknown_artifact() -> None:
    bad = _minimal_discovery()
    bad["relationships"][0]["target"] = "missing.dita"

    with pytest.raises(
        PlanningContractError,
        match="Relationships reference unknown artifacts",
    ):
        normalize_discovery_report(bad)


def test_fails_missing_pattern_id() -> None:
    bad = _minimal_discovery()
    bad["relationships"][0].pop("pattern_id")

    with pytest.raises(PlanningContractError):
        normalize_discovery_report(bad)