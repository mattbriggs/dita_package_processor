"""
Tests for execution domain models.

These tests ensure execution models:

- represent forensic reality
- serialize deterministically
- compute summaries correctly
- classify failures explicitly
- enforce canonical failure taxonomy
"""

from __future__ import annotations

import pytest

from dita_package_processor.execution.models import (
    ExecutionActionResult,
    ExecutionReport,
)


# =============================================================================
# ExecutionActionResult
# =============================================================================


def test_execution_action_result_serialization() -> None:
    """
    Action results must serialize deterministically and preserve fields.
    """
    result = ExecutionActionResult(
        action_id="copy-0001",
        status="success",
        handler="FsCopyMapHandler",
        dry_run=False,
        message="Copied file successfully",
        error=None,
        error_type=None,
        metadata={"bytes": 1024},
    )

    data = result.to_dict()

    assert data["action_id"] == "copy-0001"
    assert data["status"] == "success"
    assert data["handler"] == "FsCopyMapHandler"
    assert data["dry_run"] is False
    assert data["message"] == "Copied file successfully"

    # Success must not carry error metadata
    assert data["error"] is None
    assert data["error_type"] is None

    assert data["metadata"]["bytes"] == 1024


def test_execution_action_result_with_failure_classification() -> None:
    """
    Failed actions must carry structured error classification.
    """
    result = ExecutionActionResult(
        action_id="copy-0002",
        status="failed",
        handler="FsCopyMapHandler",
        dry_run=False,
        message="Write blocked by policy",
        error="Overwrite denied",
        error_type="policy_violation",
    )

    data = result.to_dict()

    assert data["status"] == "failed"
    assert data["error"] == "Overwrite denied"
    assert data["error_type"] == "policy_violation"


# =============================================================================
# ExecutionReport
# =============================================================================


def test_execution_report_summary_computation() -> None:
    """
    ExecutionReport.create must compute summary counts correctly.
    """
    results = [
        ExecutionActionResult(
            action_id="a1",
            status="success",
            handler="H1",
            dry_run=False,
            message="ok",
        ),
        ExecutionActionResult(
            action_id="a2",
            status="failed",
            handler="H2",
            dry_run=False,
            message="failed",
            error="Permission denied",
            error_type="policy_violation",
        ),
        ExecutionActionResult(
            action_id="a3",
            status="skipped",
            handler="H3",
            dry_run=True,
            message="skipped",
        ),
    ]

    report = ExecutionReport.create(
        execution_id="exec-001",
        dry_run=False,
        results=results,
    )

    assert report.summary["success"] == 1
    assert report.summary["failed"] == 1
    assert report.summary["skipped"] == 1
    assert report.summary["total"] == 3


def test_execution_report_serialization() -> None:
    """
    ExecutionReport serialization must be JSON-safe and deterministic.
    """
    results = [
        ExecutionActionResult(
            action_id="copy-0001",
            status="success",
            handler="FsCopyTopicHandler",
            dry_run=True,
            message="Dry-run copy",
        )
    ]

    report = ExecutionReport.create(
        execution_id="exec-xyz",
        dry_run=True,
        results=results,
    )

    data = report.to_dict()

    assert data["execution_id"] == "exec-xyz"
    assert data["dry_run"] is True
    assert len(data["results"]) == 1
    assert data["summary"]["total"] == 1
    assert data["summary"]["success"] == 1
    assert data["results"][0]["error_type"] is None


def test_execution_report_with_failed_action_contains_error_type() -> None:
    """
    Failed actions must preserve error_type in serialized output.
    """
    results = [
        ExecutionActionResult(
            action_id="bad-0001",
            status="failed",
            handler="FsDeleteHandler",
            dry_run=False,
            message="Policy denied mutation",
            error="Overwrite denied",
            error_type="policy_violation",
        )
    ]

    report = ExecutionReport.create(
        execution_id="exec-fail-001",
        dry_run=False,
        results=results,
    )

    data = report.to_dict()
    action = data["results"][0]

    assert action["status"] == "failed"
    assert action["error_type"] == "policy_violation"
    assert action["error"] == "Overwrite denied"


def test_execution_report_rejects_invalid_status() -> None:
    """
    ExecutionReport must reject invalid execution statuses.
    """
    results = [
        ExecutionActionResult(
            action_id="bad",
            status="exploded",  # type: ignore[arg-type]
            handler="H",
            dry_run=False,
            message="invalid",
        )
    ]

    with pytest.raises(ValueError):
        ExecutionReport.create(
            execution_id="exec-invalid",
            dry_run=False,
            results=results,
        )