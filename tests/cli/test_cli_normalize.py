"""
Tests for the ``normalize`` CLI subcommand.

The normalize command is strictly transport:

    discovery.json → PlanningInput → planning_input.json

It must NOT:
- perform planning
- execute actions
- mutate discovery data
- infer missing fields
- apply defaults

It only validates and converts contracts.

These tests verify:
- correct exit codes
- correct file creation
- correct failure behavior
- strict contract boundaries
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pytest


# =============================================================================
# Helpers
# =============================================================================


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    """
    Execute the CLI as a subprocess.

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
def discovery_file(tmp_path: Path) -> Path:
    """
    Create a minimal valid discovery.json file.

    This mirrors the expected discovery contract shape.
    """
    discovery: Dict[str, Any] = {
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

    path = tmp_path / "discovery.json"
    path.write_text(json.dumps(discovery, indent=2), encoding="utf-8")
    return path


@pytest.fixture
def output_path(tmp_path: Path) -> Path:
    """Return output planning_input.json path."""
    return tmp_path / "planning_input.json"


# =============================================================================
# Success cases
# =============================================================================


def test_normalize_writes_planning_input_file(
    discovery_file: Path,
    output_path: Path,
) -> None:
    """CLI should write planning_input.json successfully."""
    result = _run_cli(
        [
            "normalize",
            "--input",
            str(discovery_file),
            "--output",
            str(output_path),
        ]
    )

    assert result.returncode == 0, result.stderr
    assert output_path.exists()


def test_normalize_output_is_valid_contract(
    discovery_file: Path,
    output_path: Path,
) -> None:
    """Output must be valid PlanningInput JSON."""
    result = _run_cli(
        [
            "normalize",
            "--input",
            str(discovery_file),
            "--output",
            str(output_path),
        ]
    )

    assert result.returncode == 0

    payload = json.loads(output_path.read_text())

    assert isinstance(payload, dict)
    assert payload["contract_version"] == "planning.input.v1"
    assert "main_map" in payload
    assert isinstance(payload["artifacts"], list)
    assert isinstance(payload["relationships"], list)


def test_normalize_prints_success_message(
    discovery_file: Path,
    output_path: Path,
) -> None:
    """CLI prints confirmation message to stdout."""
    result = _run_cli(
        [
            "normalize",
            "--input",
            str(discovery_file),
            "--output",
            str(output_path),
        ]
    )

    assert result.returncode == 0
    assert "PlanningInput written to:" in result.stdout


# =============================================================================
# Failure modes
# =============================================================================


def test_missing_input_fails(output_path: Path) -> None:
    """Missing discovery.json should fail with exit code 2."""
    result = _run_cli(
        [
            "normalize",
            "--input",
            "missing.json",
            "--output",
            str(output_path),
        ]
    )

    assert result.returncode == 2
    assert "not found" in result.stderr.lower()


def test_invalid_json_fails(tmp_path: Path, output_path: Path) -> None:
    """Malformed JSON should fail with exit code 2."""
    bad = tmp_path / "discovery.json"
    bad.write_text("{ broken json", encoding="utf-8")

    result = _run_cli(
        [
            "normalize",
            "--input",
            str(bad),
            "--output",
            str(output_path),
        ]
    )

    assert result.returncode == 2
    assert "invalid" in result.stderr.lower()


def test_invalid_contract_fails(tmp_path: Path, output_path: Path) -> None:
    """
    Discovery that violates contract must fail.

    This ensures normalize does not guess or repair.
    """
    bad = tmp_path / "discovery.json"
    bad.write_text(json.dumps({"foo": "bar"}), encoding="utf-8")

    result = _run_cli(
        [
            "normalize",
            "--input",
            str(bad),
            "--output",
            str(output_path),
        ]
    )

    assert result.returncode == 2
    assert "normalization" in result.stderr.lower() or "contract" in result.stderr.lower()