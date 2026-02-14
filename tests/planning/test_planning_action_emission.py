"""
Tests for planner action emission.

These tests validate that the Planner emits explicit, schema-aligned
copy actions from a dependency-ordered graph. The planner must:

- Emit deterministic action order
- Use correct action types
- Store operational fields inside parameters
- Avoid inference or transformation logic
- Accept only discovery payloads that satisfy the graph contract
"""

from pathlib import Path

from dita_package_processor.planning.planner import Planner


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _minimal_discovery() -> dict:
    """
    Construct a minimal discovery payload containing:

        A → B

    Where:
    - A is a map
    - B is a topic

    This fixture MUST obey the DependencyGraph schema contract.
    Every edge requires:
        - source
        - target
        - type
        - pattern_id
    """
    return {
        "artifacts": [
            {
                "path": "A.ditamap",
                "artifact_type": "map",
            },
            {
                "path": "topics/B.dita",
                "artifact_type": "topic",
            },
        ],
        "graph": {
            "nodes": ["A.ditamap", "topics/B.dita"],
            "edges": [
                {
                    "source": "A.ditamap",
                    "target": "topics/B.dita",
                    "type": "contains",  # REQUIRED by DependencyEdge.from_dict
                    "pattern_id": "map_contains_topicref",
                }
            ],
        },
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_planner_emits_copy_actions() -> None:
    """
    Planner must emit one copy action per artifact in graph order.
    """
    planner = Planner()
    plan = planner.plan(_minimal_discovery())

    actions = plan["actions"]

    assert len(actions) == 2
    assert actions[0]["type"] == "copy_map"
    assert actions[1]["type"] == "copy_topic"


def test_planner_emits_parameters_with_paths() -> None:
    """
    Each action must contain a parameters object with
    explicit source_path and target_path fields.
    """
    planner = Planner()
    plan = planner.plan(_minimal_discovery())

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
    """
    Target paths should be derived from layout rules and must differ
    from source paths unless explicitly mapped otherwise.
    """
    planner = Planner()
    plan = planner.plan(_minimal_discovery())

    for action in plan["actions"]:
        params = action["parameters"]
        src = Path(params["source_path"])
        tgt = Path(params["target_path"])

        assert src != tgt


def test_planner_emits_deterministic_action_ids() -> None:
    """
    Action IDs must be stable and deterministic across runs.
    """
    planner = Planner()

    plan1 = planner.plan(_minimal_discovery())
    plan2 = planner.plan(_minimal_discovery())

    ids1 = [a["id"] for a in plan1["actions"]]
    ids2 = [a["id"] for a in plan2["actions"]]

    assert ids1 == ids2


def test_planner_includes_reason_field() -> None:
    """
    All actions must include a human-readable reason.
    """
    planner = Planner()
    plan = planner.plan(_minimal_discovery())

    for action in plan["actions"]:
        assert "reason" in action
        assert isinstance(action["reason"], str)
        assert action["reason"].strip()


def test_planner_outputs_dispatchable_actions_only() -> None:
    """
    Planning must not emit execution state.

    No:
    - status
    - dry_run
    - handler
    - result fields
    """
    planner = Planner()
    plan = planner.plan(_minimal_discovery())

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