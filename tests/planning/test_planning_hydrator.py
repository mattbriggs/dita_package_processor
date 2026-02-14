"""
Tests for plan hydration.

These tests validate the JSON → Plan boundary enforced by
dita_package_processor.planning.hydrator.

Hydration is responsible for:
- converting JSON-compatible primitives into domain models
- enforcing required fields
- performing type coercion (e.g. str → datetime, str → Path)
- failing loudly and deterministically on invalid input
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pytest

from dita_package_processor.planning.hydrator import (
    PlanHydrationError,
    hydrate_plan,
)
from dita_package_processor.planning.models import (
    Plan,
    PlanAction,
    PlanIntent,
    PlanSourceDiscovery,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_plan_payload() -> Dict[str, Any]:
    """
    Return a minimal, valid plan payload as parsed from JSON.

    This fixture represents the canonical on-disk shape of plan.json.
    """
    return {
        "plan_version": 1,
        "generated_at": "2026-01-05T20:28:34.399100+00:00",
        "source_discovery": {
            "path": "discovery.json",
            "schema_version": 1,
            "artifact_count": 58,
        },
        "intent": {
            "target": "analysis_only",
            "description": "Auto-generated plan",
        },
        "actions": [
            {
                "id": "copy-main-map",
                "type": "copy_map",  # must be a valid ActionType
                "target": "index.ditamap",
                "reason": "Single MAIN map detected",
                "derived_from_evidence": ["main_map_by_index"],
            }
        ],
        "invariants": [],
    }


# ---------------------------------------------------------------------------
# Positive cases
# ---------------------------------------------------------------------------


def test_hydrate_plan_returns_plan(valid_plan_payload: Dict[str, Any]) -> None:
    """
    A valid payload must hydrate into a Plan instance.
    """
    plan = hydrate_plan(valid_plan_payload)

    assert isinstance(plan, Plan)
    assert plan.plan_version == 1
    assert isinstance(plan.generated_at, datetime)
    assert plan.generated_at.tzinfo is not None


def test_hydrate_plan_hydrates_nested_models(
    valid_plan_payload: Dict[str, Any],
) -> None:
    """
    Nested objects must be hydrated into their respective model types.
    """
    plan = hydrate_plan(valid_plan_payload)

    assert isinstance(plan.source_discovery, PlanSourceDiscovery)
    assert isinstance(plan.intent, PlanIntent)
    assert isinstance(plan.actions, list)
    assert all(isinstance(a, PlanAction) for a in plan.actions)


def test_hydrate_plan_converts_path_and_datetime(
    valid_plan_payload: Dict[str, Any],
) -> None:
    """
    Hydration must coerce JSON primitives into rich Python types.
    """
    plan = hydrate_plan(valid_plan_payload)

    assert isinstance(plan.source_discovery.path, Path)
    assert plan.source_discovery.path.name == "discovery.json"

    assert isinstance(plan.generated_at, datetime)
    assert plan.generated_at.tzinfo is not None


def test_hydrate_plan_defaults_optional_fields(
    valid_plan_payload: Dict[str, Any],
) -> None:
    """
    Optional fields such as action parameters must default correctly.
    """
    plan = hydrate_plan(valid_plan_payload)

    action = plan.actions[0]

    assert action.parameters == {}
    assert action.derived_from_evidence == ["main_map_by_index"]


# ---------------------------------------------------------------------------
# Negative cases
# ---------------------------------------------------------------------------


def test_hydrate_plan_missing_required_field_fails(
    valid_plan_payload: Dict[str, Any],
) -> None:
    """
    Missing required top-level fields must raise PlanHydrationError.
    """
    payload = dict(valid_plan_payload)
    payload.pop("plan_version")

    with pytest.raises(PlanHydrationError):
        hydrate_plan(payload)


def test_hydrate_plan_invalid_datetime_fails(
    valid_plan_payload: Dict[str, Any],
) -> None:
    """
    Invalid datetime formats must fail explicitly.
    """
    payload = dict(valid_plan_payload)
    payload["generated_at"] = "not-a-datetime"

    with pytest.raises(PlanHydrationError):
        hydrate_plan(payload)


def test_hydrate_plan_missing_action_field_fails(
    valid_plan_payload: Dict[str, Any],
) -> None:
    """
    Missing required action fields must fail hydration.
    """
    payload = dict(valid_plan_payload)
    payload["actions"] = [
        {
            "id": "broken-action",
            # missing type
            "target": "index.ditamap",
            "reason": "Broken test",
        }
    ]

    with pytest.raises(PlanHydrationError):
        hydrate_plan(payload)