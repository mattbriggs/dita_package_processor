"""
Tests for planning data models.

Planning models are pure data containers produced by the plan loader
after schema validation. They must:

- store values without mutation
- expose attributes directly
- contain no inference or execution logic

Execution-layer models live in dita_package_processor.execution.models
and are NOT part of planning.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from dita_package_processor.planning.models import (
    ActionType,
    Plan,
    PlanAction,
    PlanIntent,
    PlanSourceDiscovery,
)


# ---------------------------------------------------------------------------
# PlanSourceDiscovery
# ---------------------------------------------------------------------------


def test_plan_source_discovery_fields_with_path() -> None:
    src = PlanSourceDiscovery(
        path=Path("discovery.json"),
        schema_version=1,
        artifact_count=42,
    )

    assert src.path == Path("discovery.json")
    assert src.schema_version == 1
    assert src.artifact_count == 42


def test_plan_source_discovery_fields_with_string_path() -> None:
    src = PlanSourceDiscovery(
        path="discovery.json",
        schema_version=1,
        artifact_count=42,
    )

    assert src.path == "discovery.json"


# ---------------------------------------------------------------------------
# PlanIntent
# ---------------------------------------------------------------------------


def test_plan_intent_fields() -> None:
    intent = PlanIntent(
        target="analysis_only",
        description="Dry-run plan",
    )

    assert intent.target == "analysis_only"
    assert intent.description == "Dry-run plan"


# ---------------------------------------------------------------------------
# PlanAction
# ---------------------------------------------------------------------------


def test_plan_action_minimal_fields() -> None:
    action = PlanAction(
        id="noop-001",
        type="noop",
        target="index.ditamap",
        reason="Testing only",
    )

    assert action.type == "noop"
    assert action.parameters == {}
    assert action.derived_from_evidence == []


def test_plan_action_copy_map_factory() -> None:
    action = PlanAction.copy_map(
        id="copy-map-1",
        source_path="index.ditamap",
        target_path="target/index.ditamap",
        reason="Root map copy",
    )

    assert action.type == ActionType.COPY_MAP.value
    assert action.parameters["source_path"] == "index.ditamap"
    assert action.parameters["target_path"] == "target/index.ditamap"


def test_plan_action_copy_topic_factory() -> None:
    action = PlanAction.copy_topic(
        id="copy-topic-1",
        source_path="topics/a.dita",
        target_path="target/topics/a.dita",
        reason="Topic dependency",
    )

    assert action.type == ActionType.COPY_TOPIC.value


def test_plan_action_copy_media_factory() -> None:
    action = PlanAction.copy_media(
        id="copy-media-1",
        source_path="images/a.png",
        target_path="target/media/a.png",
        reason="Media dependency",
    )

    assert action.type == ActionType.COPY_MEDIA.value


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------


def test_plan_fields() -> None:
    src = PlanSourceDiscovery(
        path=Path("discovery.json"),
        schema_version=1,
        artifact_count=10,
    )

    intent = PlanIntent(
        target="dita_normalization",
        description="Normalize package for CCMS",
    )

    action = PlanAction(
        id="noop-001",
        type="noop",
        target="index.ditamap",
        reason="Placeholder",
    )

    generated_at = datetime.fromisoformat("2026-01-01T00:00:00+00:00")

    plan = Plan(
        plan_version=1,
        generated_at=generated_at,
        source_discovery=src,
        intent=intent,
        actions=[action],
        invariants=[],
    )

    assert plan.plan_version == 1
    assert plan.generated_at == generated_at
    assert plan.source_discovery is src
    assert plan.intent is intent
    assert plan.actions == [action]
    assert plan.invariants == []


def test_plan_is_frozen() -> None:
    src = PlanSourceDiscovery(
        path="discovery.json",
        schema_version=1,
        artifact_count=1,
    )

    intent = PlanIntent(
        target="analysis_only",
        description="Immutability test",
    )

    plan = Plan(
        plan_version=1,
        generated_at=datetime.now(UTC),
        source_discovery=src,
        intent=intent,
        actions=[],
        invariants=[],
    )

    with pytest.raises(Exception):
        plan.plan_version = 2


# ---------------------------------------------------------------------------
# Action Type Boundary Protection
# ---------------------------------------------------------------------------


def test_valid_action_type_is_accepted() -> None:
    action = PlanAction(
        id="noop-1",
        type="noop",
        target="index.ditamap",
        reason="Test",
    )
    assert action.type == ActionType.NOOP.value


def test_enum_action_type_is_accepted() -> None:
    action = PlanAction(
        id="copy-1",
        type=ActionType.COPY_MAP,
        target="index.ditamap",
        reason="Test",
    )
    assert action.type == ActionType.COPY_MAP.value


def test_invalid_action_type_fails() -> None:
    with pytest.raises(ValueError):
        PlanAction(
            id="bad-1",
            type="copy_mpa",
            target="index.ditamap",
            reason="Typo",
        )