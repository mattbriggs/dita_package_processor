"""
Tests for the deterministic Planner using the PlanningInput contract.

Planner responsibilities
------------------------
- accepts ONLY PlanningInput
- emits deterministic copy actions
- ignores relationships entirely
- performs no normalization
- fails fast on wrong types
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dita_package_processor.planning.contracts.planning_input import (
    PlanningArtifact,
    PlanningInput,
)
from dita_package_processor.planning.planner import Planner


# =============================================================================
# Fixtures
# =============================================================================


def _minimal_planning_input() -> PlanningInput:
    """
    Construct a minimal valid PlanningInput instance.

    This mirrors the strict contract boundary.

    Relationships exist but planner does not use them.
    """
    return PlanningInput(
        contract_version="planning.input.v1",
        main_map="Main.ditamap",
        artifacts=[
            PlanningArtifact(
                path="Main.ditamap",
                artifact_type="map",
            ),
            PlanningArtifact(
                path="topics/a.dita",
                artifact_type="topic",
            ),
        ],
        relationships=[],  # planner intentionally ignores
    )


# =============================================================================
# Positive tests
# =============================================================================


def test_planner_emits_copy_actions() -> None:
    planner = Planner()

    plan = planner.plan(_minimal_planning_input())

    actions = plan["actions"]

    assert len(actions) == 2
    assert {a["type"] for a in actions} == {"copy_map", "copy_topic"}


def test_planner_action_schema_shape() -> None:
    planner = Planner()

    plan = planner.plan(_minimal_planning_input())

    action = plan["actions"][0]

    assert "id" in action
    assert "type" in action
    assert "target" in action
    assert "reason" in action
    assert "parameters" in action

    params = action["parameters"]

    assert "source_path" in params
    assert "target_path" in params
    assert action["target"] == params["target_path"]


def test_planner_targets_rooted_in_target_directory() -> None:
    planner = Planner()

    plan = planner.plan(_minimal_planning_input())

    for action in plan["actions"]:
        target = Path(action["target"])
        assert target.parts[0] == "target"


def test_plan_structure() -> None:
    planner = Planner()

    plan = planner.plan(_minimal_planning_input())

    assert plan["plan_version"] == 1
    assert "generated_at" in plan
    assert "source_discovery" in plan
    assert "intent" in plan
    assert isinstance(plan["actions"], list)
    assert isinstance(plan["invariants"], list)


# =============================================================================
# Contract wall tests (architectural enforcement)
# =============================================================================


def test_planner_rejects_raw_dict() -> None:
    """
    Planner must refuse raw dictionaries.

    Only PlanningInput objects are allowed.
    """
    planner = Planner()

    with pytest.raises(TypeError):
        planner.plan({"artifacts": []})


def test_planner_requires_planning_input_type() -> None:
    planner = Planner()

    with pytest.raises(TypeError):
        planner.plan([])


def test_planner_deterministic_ordering() -> None:
    """
    Artifact ordering must be stable and path-sorted.
    """
    planner = Planner()

    inp = PlanningInput(
        contract_version="planning.input.v1",
        main_map="z.ditamap",
        artifacts=[
            PlanningArtifact(path="b.dita", artifact_type="topic"),
            PlanningArtifact(path="a.dita", artifact_type="topic"),
        ],
        relationships=[],
    )

    plan = planner.plan(inp)

    targets = [a["parameters"]["source_path"] for a in plan["actions"]]

    assert targets == ["a.dita", "b.dita"]