"""
Tests for PlanningInput loader.

This module verifies the hard filesystem → contract boundary.

Responsibilities tested
-----------------------
- Reads valid planning_input.json
- Hydrates PlanningInput model
- Fails loudly on:
    - missing file
    - invalid JSON
    - malformed contract structure

No planner logic is exercised here.
This suite tests only transport + hydration.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dita_package_processor.planning.contracts.loader import (
    PlanningInputLoadError,
    load_planning_input,
)
from dita_package_processor.planning.contracts.planning_input import PlanningInput


# =============================================================================
# Helpers
# =============================================================================


def _write(path: Path, payload: dict) -> Path:
    """Write JSON payload to path."""
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _valid_contract() -> dict:
    """Return minimal valid PlanningInput contract payload."""
    return {
        "contract_version": "planning.input.v1",
        "main_map": "index.ditamap",
        "artifacts": [
            {
                "path": "index.ditamap",
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
                "source": "index.ditamap",
                "target": "topics/a.dita",
                "type": "topicref",
                "pattern_id": "p1",
            }
        ],
    }


# =============================================================================
# Happy path
# =============================================================================


def test_load_valid_planning_input(tmp_path: Path) -> None:
    """Valid contract hydrates to PlanningInput instance."""
    path = _write(tmp_path / "planning_input.json", _valid_contract())

    model = load_planning_input(path)

    assert isinstance(model, PlanningInput)
    assert model.main_map == "index.ditamap"
    assert len(model.artifacts) == 2
    assert len(model.relationships) == 1


# =============================================================================
# Filesystem failures
# =============================================================================


def test_missing_file_fails(tmp_path: Path) -> None:
    """Missing file must raise PlanningInputLoadError."""
    missing = tmp_path / "nope.json"

    with pytest.raises(PlanningInputLoadError):
        load_planning_input(missing)


def test_invalid_json_fails(tmp_path: Path) -> None:
    """Malformed JSON must raise PlanningInputLoadError."""
    path = tmp_path / "planning_input.json"
    path.write_text("{ broken json", encoding="utf-8")

    with pytest.raises(PlanningInputLoadError):
        load_planning_input(path)


# =============================================================================
# Contract violations
# =============================================================================


def test_missing_required_keys_fail(tmp_path: Path) -> None:
    """Missing contract fields must fail hydration."""
    bad = {"artifacts": []}

    path = _write(tmp_path / "planning_input.json", bad)

    with pytest.raises(PlanningInputLoadError):
        load_planning_input(path)


def test_artifacts_wrong_type_fail(tmp_path: Path) -> None:
    """Artifacts must be list."""
    bad = _valid_contract()
    bad["artifacts"] = {}

    path = _write(tmp_path / "planning_input.json", bad)

    with pytest.raises(PlanningInputLoadError):
        load_planning_input(path)


def test_relationships_wrong_type_fail(tmp_path: Path) -> None:
    """Relationships must be list."""
    bad = _valid_contract()
    bad["relationships"] = {}

    path = _write(tmp_path / "planning_input.json", bad)

    with pytest.raises(PlanningInputLoadError):
        load_planning_input(path)


def test_missing_relationship_fields_fail(tmp_path: Path) -> None:
    """Malformed relationship record must fail."""
    bad = _valid_contract()
    bad["relationships"] = [{"source": "a"}]

    path = _write(tmp_path / "planning_input.json", bad)

    with pytest.raises(PlanningInputLoadError):
        load_planning_input(path)


def test_missing_artifact_fields_fail(tmp_path: Path) -> None:
    """Malformed artifact record must fail."""
    bad = _valid_contract()
    bad["artifacts"] = [{"path": "a.dita"}]

    path = _write(tmp_path / "planning_input.json", bad)

    with pytest.raises(PlanningInputLoadError):
        load_planning_input(path)