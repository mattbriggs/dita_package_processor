"""
Tests for the ``plan`` CLI subcommand.

The CLI is intentionally thin and performs only:

    read contract → hydrate contract → call Planner → write plan.json

It must NOT:
- normalize relationships
- mutate data
- interpret discovery
- perform business logic

These tests enforce that the CLI is strictly transport only.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


# =============================================================================
# Helpers
# =============================================================================


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    """
    Execute the dita_package_processor CLI as a subprocess.

    Parameters
    ----------
    args : list[str]
        CLI arguments following module name.

    Returns
    -------
    subprocess.CompletedProcess[str]
    """
    return subprocess.run(
        [sys.executable, "-m", "dita_package_processor", *args],
        capture_output=True,
        text=True,
    )


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def planning_input_file(tmp_path: Path) -> Path:
    """
    Create a valid PlanningInput contract file.

    Important
    ---------
    Use the real normalization path so the CLI is tested with
    a legitimate contract, not fake JSON.
    """
    from dita_package_processor.planning.contracts.discovery_to_planning import (
        normalize_discovery_report,
    )

    discovery = {
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
                "pattern_id": "dita_map_topicref",
            }
        ],
        "summary": {},
    }

    planning_input = normalize_discovery_report(discovery)

    path = tmp_path / "planning_input.json"
    path.write_text(
        json.dumps(planning_input.to_dict(), indent=2),
        encoding="utf-8",
    )

    return path


@pytest.fixture
def output_plan_path(tmp_path: Path) -> Path:
    """Return output plan path."""
    return tmp_path / "plan.json"


# =============================================================================
# Success cases
# =============================================================================


def test_plan_writes_plan_file(
    planning_input_file: Path,
    output_plan_path: Path,
) -> None:
    """CLI should write plan.json successfully."""
    result = _run_cli(
        ["plan", "--input", str(planning_input_file), "--output", str(output_plan_path)]
    )

    assert result.returncode == 0, result.stderr
    assert output_plan_path.exists()


def test_plan_output_is_valid_json(
    planning_input_file: Path,
    output_plan_path: Path,
) -> None:
    """Generated file must be valid JSON with expected structure."""
    result = _run_cli(
        ["plan", "--input", str(planning_input_file), "--output", str(output_plan_path)]
    )

    assert result.returncode == 0

    plan = json.loads(output_plan_path.read_text())

    assert isinstance(plan, dict)
    assert "plan_version" in plan
    assert isinstance(plan["actions"], list)


def test_plan_prints_success_message(
    planning_input_file: Path,
    output_plan_path: Path,
) -> None:
    """CLI prints confirmation message to stdout."""
    result = _run_cli(
        ["plan", "--input", str(planning_input_file), "--output", str(output_plan_path)]
    )

    assert result.returncode == 0
    assert "plan written to" in result.stdout.lower()


# =============================================================================
# Failure modes (transport only)
# =============================================================================


def test_plan_missing_input_fails(output_plan_path: Path) -> None:
    """Missing input should return setup error (exit code 2)."""
    result = _run_cli(
        ["plan", "--input", "missing.json", "--output", str(output_plan_path)]
    )

    assert result.returncode == 2
    assert "not found" in result.stderr.lower()


def test_plan_invalid_json_fails(
    tmp_path: Path,
    output_plan_path: Path,
) -> None:
    """Malformed JSON should return setup error (exit code 2)."""
    bad = tmp_path / "planning_input.json"
    bad.write_text("{ broken json", encoding="utf-8")

    result = _run_cli(
        ["plan", "--input", str(bad), "--output", str(output_plan_path)]
    )

    assert result.returncode == 2
    assert "invalid" in result.stderr.lower()


def test_plan_rejects_non_contract_json(
    tmp_path: Path,
    output_plan_path: Path,
) -> None:
    """
    Non-contract JSON must be rejected.

    This enforces the architectural boundary:
    CLI only accepts PlanningInput contracts.
    """
    bad = tmp_path / "not_contract.json"
    bad.write_text(json.dumps({"artifacts": []}), encoding="utf-8")

    result = _run_cli(
        ["plan", "--input", str(bad), "--output", str(output_plan_path)]
    )

    assert result.returncode == 2
    assert "contract" in result.stderr.lower()