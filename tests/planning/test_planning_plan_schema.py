"""
Tests for the DITA processing Plan schema.

These tests validate the *contract* between discovery, planning,
and execution. No planner or executor logic is exercised here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

import jsonschema
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_schema_and_plan(
    schema_path: Path,
    plan_path: Path,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Load a JSON Schema and a plan instance from disk.

    :param schema_path: Path to plan.schema.json
    :param plan_path: Path to a plan fixture JSON file
    :return: Tuple of (schema, plan)
    """
    with schema_path.open(encoding="utf-8") as fh:
        schema = json.load(fh)

    with plan_path.open(encoding="utf-8") as fh:
        plan = json.load(fh)

    return schema, plan


def _schema_path() -> Path:
    """
    Resolve the absolute path to the plan schema.

    :return: Path to plan.schema.json
    """
    project_root = Path(__file__).parents[2]
    return (
        project_root
        / "dita_package_processor"
        / "planning"
        / "schema"
        / "plan.schema.json"
    )


def _fixture_path(name: str) -> Path:
    """
    Resolve a plan fixture path by filename.

    :param name: Fixture filename
    :return: Path to fixture file
    """
    return Path(__file__).parent / "fixtures" / name


# ---------------------------------------------------------------------------
# Positive tests
# ---------------------------------------------------------------------------


def test_minimal_plan_conforms_to_schema() -> None:
    """
    A minimal, hand-written plan JSON should validate
    against the plan schema.

    This test freezes the planning contract and ensures
    backward compatibility.
    """
    schema, plan = _load_schema_and_plan(
        _schema_path(),
        _fixture_path("plan_minimal.json"),
    )

    jsonschema.validate(instance=plan, schema=schema)


def test_plan_with_multiple_actions_conforms_to_schema() -> None:
    """
    A plan with multiple actions and invariants should
    validate successfully.
    """
    schema, plan = _load_schema_and_plan(
        _schema_path(),
        _fixture_path("plan_with_actions.json"),
    )

    jsonschema.validate(instance=plan, schema=schema)


# ---------------------------------------------------------------------------
# Negative tests
# ---------------------------------------------------------------------------


def test_plan_missing_actions_fails_validation() -> None:
    """
    Plans without an actions array must be rejected.
    """
    schema, plan = _load_schema_and_plan(
        _schema_path(),
        _fixture_path("plan_missing_actions.json"),
    )

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=plan, schema=schema)


def test_plan_with_unknown_action_type_fails_validation() -> None:
    """
    Plans containing unsupported action types must be rejected.
    """
    schema, plan = _load_schema_and_plan(
        _schema_path(),
        _fixture_path("plan_unknown_action.json"),
    )

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=plan, schema=schema)


def test_plan_with_wrong_version_fails_validation() -> None:
    """
    Plans with unsupported plan_version values must be rejected.
    """
    schema, plan = _load_schema_and_plan(
        _schema_path(),
        _fixture_path("plan_wrong_version.json"),
    )

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=plan, schema=schema)