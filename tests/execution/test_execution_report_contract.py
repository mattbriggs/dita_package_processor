"""
Execution report contract tests.

These tests lock the execution report schema and validate that:

- A golden execution report payload conforms to the schema.
- The schema rejects malformed payloads.
- The execution report is a strict forensic artifact.
- The report is internally self-consistent.

This is the final contract surface of the execution layer.
Nothing downstream is allowed to reinterpret it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import jsonschema
import pytest

from dita_package_processor.execution.models import (
    ExecutionActionResult,
    ExecutionReport,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_schema() -> Dict[str, Any]:
    """
    Load execution_report.schema.json from the execution schema directory.
    """
    schema_path = (
        Path(__file__).parents[2]
        / "dita_package_processor"
        / "execution"
        / "schema"
        / "execution_report.schema.json"
    )

    assert schema_path.exists(), f"Missing execution report schema: {schema_path}"

    return json.loads(schema_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def golden_execution_report_dict() -> Dict[str, Any]:
    """
    Golden execution report payload.

    This payload represents a canonical, minimal valid execution report.
    It must remain stable unless the execution contract is intentionally changed.
    """
    results = [
        ExecutionActionResult(
            action_id="copy-0001",
            status="success",
            handler="FsCopyMapHandler",
            dry_run=False,
            message="Map copied successfully",
        ),
        ExecutionActionResult(
            action_id="copy-0002",
            status="skipped",
            handler="FsCopyMediaHandler",
            dry_run=True,
            message="Dry-run: media copy skipped",
        ),
    ]

    report = ExecutionReport.create(
        execution_id="exec-2026-01",
        dry_run=False,
        results=results,
    )

    return report.to_dict()


@pytest.fixture
def execution_report_schema() -> Dict[str, Any]:
    """
    Load the execution report JSON schema.
    """
    return _load_schema()


# ---------------------------------------------------------------------------
# Contract tests
# ---------------------------------------------------------------------------


def test_golden_execution_report_matches_schema(
    golden_execution_report_dict: Dict[str, Any],
    execution_report_schema: Dict[str, Any],
) -> None:
    """
    The golden execution report must validate against the schema.
    This is the primary contract lock.
    """
    jsonschema.validate(
        instance=golden_execution_report_dict,
        schema=execution_report_schema,
    )


def test_execution_report_summary_is_consistent(
    golden_execution_report_dict: Dict[str, Any],
) -> None:
    """
    Summary counters must match the contents of results.
    """
    summary = golden_execution_report_dict["summary"]
    results = golden_execution_report_dict["results"]

    assert summary["total"] == len(results)
    assert summary["success"] == 1
    assert summary["failed"] == 0
    assert summary["skipped"] == 1


def test_schema_rejects_missing_required_fields(
    golden_execution_report_dict: Dict[str, Any],
    execution_report_schema: Dict[str, Any],
) -> None:
    """
    The schema must reject reports missing required top-level fields.
    """
    broken = dict(golden_execution_report_dict)
    broken.pop("results")

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=broken, schema=execution_report_schema)


def test_schema_rejects_invalid_action_status(
    golden_execution_report_dict: Dict[str, Any],
    execution_report_schema: Dict[str, Any],
) -> None:
    """
    The schema must reject invalid execution statuses.
    """
    broken = dict(golden_execution_report_dict)
    broken["results"] = list(broken["results"])
    broken["results"][0] = dict(broken["results"][0])
    broken["results"][0]["status"] = "maybe"  # invalid

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=broken, schema=execution_report_schema)


def test_schema_rejects_missing_summary_fields(
    golden_execution_report_dict: Dict[str, Any],
    execution_report_schema: Dict[str, Any],
) -> None:
    """
    Summary must contain the required counters.
    """
    broken = dict(golden_execution_report_dict)
    broken["summary"] = {"success": 2}

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=broken, schema=execution_report_schema)


def test_schema_rejects_non_array_results(
    golden_execution_report_dict: Dict[str, Any],
    execution_report_schema: Dict[str, Any],
) -> None:
    """
    results must be an array.
    """
    broken = dict(golden_execution_report_dict)
    broken["results"] = "not-a-list"

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=broken, schema=execution_report_schema)


def test_schema_rejects_additional_top_level_fields(
    golden_execution_report_dict: Dict[str, Any],
    execution_report_schema: Dict[str, Any],
) -> None:
    """
    The schema must reject unexpected top-level fields.
    """
    broken = dict(golden_execution_report_dict)
    broken["hacked"] = True

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=broken, schema=execution_report_schema)


def test_schema_rejects_additional_action_fields(
    golden_execution_report_dict: Dict[str, Any],
    execution_report_schema: Dict[str, Any],
) -> None:
    """
    Each action result must reject unknown properties.
    """
    broken = dict(golden_execution_report_dict)
    broken["results"] = list(broken["results"])
    broken["results"][0] = dict(broken["results"][0])
    broken["results"][0]["extra"] = "illegal"

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=broken, schema=execution_report_schema)