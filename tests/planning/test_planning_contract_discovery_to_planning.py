"""
Tests for discovery → planning contract normalization.

Locks the contract boundary between discovery and planning.

Rules enforced here:

- No optional behavior
- No guessing
- Fail fast on ambiguity
- Deterministic normalization only
- PlanningInput must be schema-valid
"""

from __future__ import annotations

import pytest

from dita_package_processor.planning.contracts.discovery_to_planning import (
    normalize_discovery_report,
)
from dita_package_processor.planning.contracts.errors import PlanningContractError


# =============================================================================
# Happy path
# =============================================================================


def test_normalize_discovery_report_happy_path() -> None:
    """Valid discovery report should normalize successfully."""
    discovery = {
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
            {
                "path": "media/logo.png",
                "artifact_type": "media",
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

    planning = normalize_discovery_report(discovery)
    data = planning.to_dict()

    assert data["contract_version"] == "planning.input.v1"
    assert data["main_map"] == "index.ditamap"
    assert len(data["artifacts"]) == 3
    assert len(data["relationships"]) == 1


# =============================================================================
# Classification normalization (UPDATED)
# =============================================================================


def test_main_map_alias_normalizes() -> None:
    """MAIN_MAP alias must normalize deterministically to MAIN."""
    discovery = {
        "artifacts": [
            {
                "path": "index.ditamap",
                "artifact_type": "map",
                "classification": "MAIN_MAP",
                "metadata": {},
            }
        ],
        "relationships": [],
        "summary": {},
    }

    planning = normalize_discovery_report(discovery)

    assert planning.main_map == "index.ditamap"


def test_non_main_classifications_are_coerced_to_none() -> None:
    """
    Any non-MAIN classification must collapse to None.

    Planning only cares about MAIN vs everything else.
    """
    discovery = {
        "artifacts": [
            {
                "path": "index.ditamap",
                "artifact_type": "map",
                "classification": "MAIN",
                "metadata": {},
            },
            {
                "path": "topics/glossary.dita",
                "artifact_type": "topic",
                "classification": "GLOSSARY",
                "metadata": {},
            },
        ],
        "relationships": [],
        "summary": {},
    }

    planning = normalize_discovery_report(discovery)

    artifacts = {a.path: a.classification for a in planning.artifacts}

    assert artifacts["topics/glossary.dita"] is None


# =============================================================================
# Discovery shape validation
# =============================================================================


def test_missing_required_discovery_keys() -> None:
    with pytest.raises(PlanningContractError, match="missing required keys"):
        normalize_discovery_report({"artifacts": [], "relationships": []})


def test_artifacts_must_be_list() -> None:
    with pytest.raises(PlanningContractError, match="must be a list"):
        normalize_discovery_report(
            {"artifacts": {}, "relationships": [], "summary": {}}
        )


def test_relationships_must_be_list() -> None:
    with pytest.raises(PlanningContractError, match="must be a list"):
        normalize_discovery_report(
            {"artifacts": [], "relationships": {}, "summary": {}}
        )


# =============================================================================
# Artifact normalization
# =============================================================================


def test_artifact_missing_required_fields() -> None:
    with pytest.raises(PlanningContractError):
        normalize_discovery_report(
            {
                "artifacts": [{"path": "index.ditamap"}],
                "relationships": [],
                "summary": {},
            }
        )


def test_artifact_invalid_type() -> None:
    with pytest.raises(PlanningContractError):
        normalize_discovery_report(
            {
                "artifacts": [
                    {
                        "path": "bad.txt",
                        "artifact_type": "weird",
                        "metadata": {},
                    }
                ],
                "relationships": [],
                "summary": {},
            }
        )


# =============================================================================
# MAIN map selection (hard invariant)
# =============================================================================


def test_no_main_map_fails() -> None:
    with pytest.raises(
        PlanningContractError,
        match="Exactly one artifact must be classified as MAIN map",
    ):
        normalize_discovery_report(
            {
                "artifacts": [
                    {
                        "path": "a.ditamap",
                        "artifact_type": "map",
                        "classification": None,
                        "metadata": {},
                    }
                ],
                "relationships": [],
                "summary": {},
            }
        )


def test_multiple_main_maps_fail() -> None:
    with pytest.raises(
        PlanningContractError,
        match="Exactly one artifact must be classified as MAIN map",
    ):
        normalize_discovery_report(
            {
                "artifacts": [
                    {
                        "path": "a.ditamap",
                        "artifact_type": "map",
                        "classification": "MAIN",
                        "metadata": {},
                    },
                    {
                        "path": "b.ditamap",
                        "artifact_type": "map",
                        "classification": "MAIN",
                        "metadata": {},
                    },
                ],
                "relationships": [],
                "summary": {},
            }
        )


# =============================================================================
# Relationship normalization
# =============================================================================


def test_relationship_missing_fields() -> None:
    with pytest.raises(PlanningContractError):
        normalize_discovery_report(
            {
                "artifacts": [
                    {
                        "path": "index.ditamap",
                        "artifact_type": "map",
                        "classification": "MAIN",
                        "metadata": {},
                    }
                ],
                "relationships": [{"source": "index.ditamap"}],
                "summary": {},
            }
        )


def test_relationship_unknown_endpoint_fails() -> None:
    with pytest.raises(
        PlanningContractError,
        match="Relationships reference unknown artifacts",
    ):
        normalize_discovery_report(
            {
                "artifacts": [
                    {
                        "path": "index.ditamap",
                        "artifact_type": "map",
                        "classification": "MAIN",
                        "metadata": {},
                    }
                ],
                "relationships": [
                    {
                        "source": "missing",
                        "target": "index.ditamap",
                        "type": "topicref",
                        "pattern_id": "p",
                    }
                ],
                "summary": {},
            }
        )