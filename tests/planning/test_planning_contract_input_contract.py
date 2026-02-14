"""
Unit tests for the planning input contract models.

These tests verify that:
- PlanningArtifact serializes deterministically
- PlanningRelationship serializes deterministically
- PlanningInput serializes deterministically
- No implicit behavior, guessing, or mutation occurs
- The contract surface is schema-stable and explicit
"""

from __future__ import annotations

from dita_package_processor.planning.contracts.planning_input import (
    PlanningArtifact,
    PlanningRelationship,
    PlanningInput,
)


# ---------------------------------------------------------------------------
# PlanningArtifact
# ---------------------------------------------------------------------------


def test_planning_artifact_to_dict_basic() -> None:
    artifact = PlanningArtifact(
        path="maps/index.ditamap",
        artifact_type="map",
        classification="MAIN",
        metadata={"root_element": "map"},
    )

    data = artifact.to_dict()

    assert data == {
        "path": "maps/index.ditamap",
        "artifact_type": "map",
        "classification": "MAIN",
        "metadata": {"root_element": "map"},
    }


def test_planning_artifact_metadata_is_copied() -> None:
    metadata = {"a": 1, "b": 2}
    artifact = PlanningArtifact(
        path="topics/a.dita",
        artifact_type="topic",
        classification=None,
        metadata=metadata,
    )

    data = artifact.to_dict()

    # Must be a shallow copy, not the same object
    assert data["metadata"] == metadata
    assert data["metadata"] is not metadata


# ---------------------------------------------------------------------------
# PlanningRelationship
# ---------------------------------------------------------------------------


def test_planning_relationship_to_dict() -> None:
    relationship = PlanningRelationship(
        source="maps/index.ditamap",
        target="topics/a.dita",
        rel_type="topicref",
        pattern_id="dita_map_topicref",
    )

    data = relationship.to_dict()

    assert data == {
        "source": "maps/index.ditamap",
        "target": "topics/a.dita",
        "type": "topicref",
        "pattern_id": "dita_map_topicref",
    }


# ---------------------------------------------------------------------------
# PlanningInput
# ---------------------------------------------------------------------------


def test_planning_input_to_dict() -> None:
    artifacts = [
        PlanningArtifact(
            path="maps/index.ditamap",
            artifact_type="map",
            classification="MAIN",
            metadata={},
        ),
        PlanningArtifact(
            path="topics/a.dita",
            artifact_type="topic",
            classification=None,
            metadata={},
        ),
    ]

    relationships = [
        PlanningRelationship(
            source="maps/index.ditamap",
            target="topics/a.dita",
            rel_type="topicref",
            pattern_id="dita_map_topicref",
        )
    ]

    planning_input = PlanningInput(
        contract_version="planning.input.v1",
        main_map="maps/index.ditamap",
        artifacts=artifacts,
        relationships=relationships,
    )

    data = planning_input.to_dict()

    assert data == {
        "contract_version": "planning.input.v1",
        "main_map": "maps/index.ditamap",
        "artifacts": [
            {
                "path": "maps/index.ditamap",
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
                "source": "maps/index.ditamap",
                "target": "topics/a.dita",
                "type": "topicref",
                "pattern_id": "dita_map_topicref",
            }
        ],
    }


def test_planning_input_does_not_mutate_inputs() -> None:
    artifacts = [
        PlanningArtifact(
            path="maps/index.ditamap",
            artifact_type="map",
            classification="MAIN",
            metadata={"x": 1},
        )
    ]

    relationships = [
        PlanningRelationship(
            source="maps/index.ditamap",
            target="topics/a.dita",
            rel_type="topicref",
            pattern_id="dita_map_topicref",
        )
    ]

    planning_input = PlanningInput(
        contract_version="planning.input.v1",
        main_map="maps/index.ditamap",
        artifacts=artifacts,
        relationships=relationships,
    )

    data = planning_input.to_dict()

    # Mutate output
    data["artifacts"][0]["metadata"]["x"] = 999

    # Original must remain untouched
    assert artifacts[0].metadata["x"] == 1


def test_contract_surface_is_minimal_and_explicit() -> None:
    """
    This test locks the public contract surface. If this fails,
    a breaking contract change was introduced.
    """
    artifact = PlanningArtifact(
        path="file.dita",
        artifact_type="topic",
        classification=None,
        metadata={},
    )

    relationship = PlanningRelationship(
        source="a",
        target="b",
        rel_type="image",
        pattern_id="dita_topic_image",
    )

    planning_input = PlanningInput(
        contract_version="planning.input.v1",
        main_map="file.dita",
        artifacts=[artifact],
        relationships=[relationship],
    )

    data = planning_input.to_dict()

    assert set(data.keys()) == {
        "contract_version",
        "main_map",
        "artifacts",
        "relationships",
    }

    assert set(data["artifacts"][0].keys()) == {
        "path",
        "artifact_type",
        "classification",
        "metadata",
    }

    assert set(data["relationships"][0].keys()) == {
        "source",
        "target",
        "type",
        "pattern_id",
    }