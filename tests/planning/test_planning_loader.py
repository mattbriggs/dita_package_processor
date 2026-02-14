"""
Tests for the planning plan loader.

The loader is a hard boundary layer responsible for:
- reading a plan JSON file from disk
- parsing JSON strictly
- delegating validation and typing to the hydrator
- normalizing all failures into PlanLoadError

The loader:
- does NOT perform semantic validation
- does NOT guess or repair malformed input
- must fail fast and loudly
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from dita_package_processor.planning.loader import PlanLoadError, load_plan
from dita_package_processor.planning.models import Plan


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_plan_dict() -> Dict[str, Any]:
    """
    Minimal syntactically valid plan payload.

    This is assumed to be semantically valid and is not intended
    to test planning logic. It only exercises the loader boundary.
    """
    return {
        "plan_version": 1,
        "generated_at": "2026-01-01T00:00:00",
        "source_discovery": {
            "path": "/tmp/discovery.json",
            "schema_version": 1,
            "artifact_count": 1,
        },
        "intent": {
            "target": "analysis_only",
            "description": "Loader test plan",
        },
        "actions": [
            {
                "id": "noop-001",
                "type": "noop",
                "target": "index.ditamap",
                "reason": "Test-only plan",
                "parameters": {},
                "derived_from_evidence": [],
            }
        ],
        "invariants": [],
    }


@pytest.fixture
def valid_plan_file(
    tmp_path: Path,
    valid_plan_dict: Dict[str, Any],
) -> Path:
    """
    Write a valid plan.json file to disk.
    """
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(valid_plan_dict), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Positive path
# ---------------------------------------------------------------------------


def test_loader_reads_valid_plan(valid_plan_file: Path) -> None:
    """
    A valid plan file must load and hydrate successfully.
    """
    plan = load_plan(valid_plan_file)
    assert isinstance(plan, Plan)


def test_loader_preserves_plan_fields(
    valid_plan_file: Path,
    valid_plan_dict: Dict[str, Any],
) -> None:
    """
    Loaded Plan must reflect the hydrated payload.
    """
    plan = load_plan(valid_plan_file)

    assert plan.plan_version == valid_plan_dict["plan_version"]
    assert plan.intent.target == valid_plan_dict["intent"]["target"]
    assert len(plan.actions) == 1
    assert plan.actions[0].id == "noop-001"


# ---------------------------------------------------------------------------
# File read failures
# ---------------------------------------------------------------------------


def test_loader_fails_when_file_missing(tmp_path: Path) -> None:
    """
    Missing file must raise PlanLoadError.
    """
    path = tmp_path / "missing.json"

    with pytest.raises(PlanLoadError, match="Failed to read plan file"):
        load_plan(path)


def test_loader_error_contains_filename_on_missing_file(tmp_path: Path) -> None:
    """
    Error message must include filename for diagnostics.
    """
    path = tmp_path / "missing.json"

    with pytest.raises(PlanLoadError) as exc:
        load_plan(path)

    assert str(path) in str(exc.value)


# ---------------------------------------------------------------------------
# JSON parse failures
# ---------------------------------------------------------------------------


def test_loader_fails_on_invalid_json(tmp_path: Path) -> None:
    """
    Invalid JSON must raise PlanLoadError.
    """
    path = tmp_path / "invalid.json"
    path.write_text("{ not valid json", encoding="utf-8")

    with pytest.raises(PlanLoadError, match="Invalid JSON in plan file"):
        load_plan(path)


def test_loader_error_contains_filename_on_invalid_json(tmp_path: Path) -> None:
    """
    Error message must include filename when JSON parsing fails.
    """
    path = tmp_path / "invalid.json"
    path.write_text("{ not valid json", encoding="utf-8")

    with pytest.raises(PlanLoadError) as exc:
        load_plan(path)

    assert str(path) in str(exc.value)


# ---------------------------------------------------------------------------
# Hydration failures
# ---------------------------------------------------------------------------


def test_loader_fails_when_json_is_not_mapping(tmp_path: Path) -> None:
    """
    JSON that parses but is not an object must fail during hydration.
    """
    path = tmp_path / "not_mapping.json"
    path.write_text(json.dumps(["this", "is", "a", "list"]), encoding="utf-8")

    with pytest.raises(PlanLoadError, match="Plan hydration failed"):
        load_plan(path)


def test_loader_fails_on_hydration_error(
    tmp_path: Path,
    valid_plan_dict: Dict[str, Any],
) -> None:
    """
    Any hydrator failure must be normalized to PlanLoadError.
    """
    invalid = dict(valid_plan_dict)
    invalid.pop("intent")

    path = tmp_path / "bad_plan.json"
    path.write_text(json.dumps(invalid), encoding="utf-8")

    with pytest.raises(PlanLoadError, match="Plan hydration failed"):
        load_plan(path)


def test_loader_error_contains_filename_on_hydration_failure(
    tmp_path: Path,
    valid_plan_dict: Dict[str, Any],
) -> None:
    """
    Hydration error messages must include filename.
    """
    invalid = dict(valid_plan_dict)
    invalid.pop("intent")

    path = tmp_path / "bad_plan.json"
    path.write_text(json.dumps(invalid), encoding="utf-8")

    with pytest.raises(PlanLoadError) as exc:
        load_plan(path)

    assert str(path) in str(exc.value)