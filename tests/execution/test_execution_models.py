"""
Tests for execution domain models.

These tests ensure execution models:
- represent forensic reality
- serialize deterministically
- compute summaries correctly
- classify failures explicitly
"""

from __future__ import annotations

from dita_package_processor.execution.models import (
    ExecutionActionResult,
    ExecutionReport,
)


def test_execution_action_result_serialization() -> None:
    result = ExecutionActionResult(
        action_id="copy-0001",
        status="success",
        handler="FsCopyMapHandler",
        dry_run=False,
        message="Copied file successfully",
        error=None,
        failure_type=None,
        metadata={"bytes": 1024},
    )

    data = result.to_dict()

    assert data["action_id"] == "copy-0001"
    assert data["status"] == "success"
    assert data["handler"] == "FsCopyMapHandler"
    assert data["dry_run"] is False
    assert data["message"] == "Copied file successfully"
    assert data["error"] is None
    assert data["failure_type"] is None
    assert data["metadata"]["bytes"] == 1024


def test_execution_action_result_with_failure_classification() -> None:
    result = ExecutionActionResult(
        action_id="copy-0002",
        status="failed",
        handler="FsCopyMapHandler",
        dry_run=False,
        message="Write blocked by policy",
        error="Overwrite denied",
        failure_type="policy_violation",
    )

    data = result.to_dict()

    assert data["status"] == "failed"
    assert data["error"] == "Overwrite denied"
    assert data["failure_type"] == "policy_violation"


def test_execution_report_summary_computation() -> None:
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
            failure_type="policy_violation",
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


def test_execution_report_with_failed_action_contains_failure_type() -> None:
    results = [
        ExecutionActionResult(
            action_id="bad-0001",
            status="failed",
            handler="FsDeleteHandler",
            dry_run=False,
            message="Target path outside sandbox",
            error="Sandbox violation",
            failure_type="sandbox_violation",
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
    assert action["failure_type"] == "sandbox_violation"
    assert action["error"] == "Sandbox violation"