"""
Unit tests for the planning input contract models.

These tests verify that:

- ``PlanningArtifact`` serializes deterministically.
- ``PlanningRelationship`` serializes deterministically.
- ``PlanningInput`` serializes deterministically.
- No implicit behavior, guessing, or mutation occurs.
- The public contract surface is minimal, explicit, and stable.

The contract layer represents a hard architectural boundary between
discovery and planning. These tests intentionally lock that boundary.
"""

from __future__ import annotations

from dita_package_processor.planning.contracts import (
    PlanningArtifact,
    PlanningRelationship,
    PlanningInput,
)


# =============================================================================
# PlanningArtifact
# =============================================================================


def test_planning_artifact_to_dict_basic() -> None:
    """
    ``PlanningArtifact.to_dict()`` must serialize deterministically and
    preserve explicit fields without coercion.
    """
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
    """
    Metadata must be copied during serialization.

    The returned dictionary must not expose internal mutable state.
    """
    metadata = {"a": 1, "b": 2}

    artifact = PlanningArtifact(
        path="topics/a.dita",
        artifact_type="topic",
        classification=None,
        metadata=metadata,
    )

    data = artifact.to_dict()

    assert data["metadata"] == metadata
    assert data["metadata"] is not metadata


# =============================================================================
# PlanningRelationship
# =============================================================================


def test_planning_relationship_to_dict() -> None:
    """
    ``PlanningRelationship.to_dict()`` must serialize deterministically
    and use schema-aligned field names.
    """
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


# =============================================================================
# PlanningInput
# =============================================================================


def test_planning_input_to_dict() -> None:
    """
    ``PlanningInput.to_dict()`` must produce the canonical wire format.

    The serialized structure must exactly match the contract schema.
    """
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
    """
    Serializing ``PlanningInput`` must not mutate original contract objects.

    Mutating the serialized output must not alter the original artifact
    metadata stored in the contract object.
    """
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

    # Mutate serialized output
    data["artifacts"][0]["metadata"]["x"] = 999

    # Original contract object must remain unchanged
    assert artifacts[0].metadata["x"] == 1


def test_contract_surface_is_minimal_and_explicit() -> None:
    """
    Lock the public contract surface.

    If this test fails, a breaking contract change was introduced.
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