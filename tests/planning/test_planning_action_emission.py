"""
Tests for planner action emission.

These tests validate that the Planner emits explicit, schema-aligned
copy actions from a dependency-ordered contract input. The planner must:

- Emit deterministic action order
- Use correct action types
- Store operational fields inside parameters
- Avoid inference or transformation logic
- Accept only PlanningInput contract objects
"""

from pathlib import Path

from dita_package_processor.planning.planner import Planner
from dita_package_processor.planning.contracts import (
    PlanningInput,
    PlanningArtifact,
    PlanningRelationship,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _minimal_planning_input() -> PlanningInput:
    """
    Construct a minimal PlanningInput:

        A.ditamap (MAIN)
            └── topics/B.dita
    """

    artifacts = [
        PlanningArtifact(
            path="A.ditamap",
            artifact_type="map",
            classification="MAIN",
        ),
        PlanningArtifact(
            path="topics/B.dita",
            artifact_type="topic",
        ),
    ]

    relationships = [
        PlanningRelationship(
            source="A.ditamap",
            target="topics/B.dita",
            rel_type="contains",
            pattern_id="map_contains_topicref",
        )
    ]

    return PlanningInput(
        contract_version="1.0",
        main_map="A.ditamap",
        artifacts=artifacts,
        relationships=relationships,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_planner_emits_copy_actions() -> None:
    planner = Planner()
    plan = planner.plan(_minimal_planning_input())

    actions = plan["actions"]

    assert len(actions) == 2
    assert actions[0]["type"] == "copy_map"
    assert actions[1]["type"] == "copy_topic"


def test_planner_emits_parameters_with_paths() -> None:
    planner = Planner()
    plan = planner.plan(_minimal_planning_input())

    for action in plan["actions"]:
        assert "parameters" in action
        params = action["parameters"]

        assert "source_path" in params
        assert "target_path" in params

        assert isinstance(params["source_path"], str)
        assert isinstance(params["target_path"], str)

        assert params["source_path"]
        assert params["target_path"]


def test_planner_uses_layout_rules_for_target_paths() -> None:
    planner = Planner()
    plan = planner.plan(_minimal_planning_input())

    for action in plan["actions"]:
        params = action["parameters"]
        src = Path(params["source_path"])
        tgt = Path(params["target_path"])

        assert src != tgt


def test_planner_emits_deterministic_action_ids() -> None:
    planner = Planner()

    plan1 = planner.plan(_minimal_planning_input())
    plan2 = planner.plan(_minimal_planning_input())

    ids1 = [a["id"] for a in plan1["actions"]]
    ids2 = [a["id"] for a in plan2["actions"]]

    assert ids1 == ids2


def test_planner_includes_reason_field() -> None:
    planner = Planner()
    plan = planner.plan(_minimal_planning_input())

    for action in plan["actions"]:
        assert "reason" in action
        assert isinstance(action["reason"], str)
        assert action["reason"].strip()


def test_planner_outputs_dispatchable_actions_only() -> None:
    planner = Planner()
    plan = planner.plan(_minimal_planning_input())

    forbidden = {
        "status",
        "dry_run",
        "handler",
        "result",
        "execution",
    }

    for action in plan["actions"]:
        for key in forbidden:
            assert key not in action