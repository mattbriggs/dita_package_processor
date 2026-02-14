"""
Tests for planning input contract models.

Locks serialization keys and naming.
"""

from __future__ import annotations

from dita_package_processor.planning.contracts.planning_input import (
    PlanningArtifact,
    PlanningInput,
    PlanningRelationship,
)


def test_planning_relationship_to_dict_keys() -> None:
    rel = PlanningRelationship(
        source="a",
        target="b",
        rel_type="topicref",
        pattern_id="p",
    )
    data = rel.to_dict()
    assert set(data.keys()) == {"source", "target", "type", "pattern_id"}


def test_planning_input_to_dict_keys() -> None:
    inp = PlanningInput(
        contract_version="planning.input.v1",
        main_map="index.ditamap",
        artifacts=[PlanningArtifact(path="index.ditamap", artifact_type="map", classification="MAIN")],
        relationships=[],
    )
    data = inp.to_dict()
    assert set(data.keys()) == {"contract_version", "main_map", "artifacts", "relationships"}