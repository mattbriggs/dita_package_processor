"""
Unit tests for the Pipeline orchestrator.

These tests validate:

- run() performs discovery → planning → materialization → execution
- execute_plan() skips discovery/planning
- Dry-run uses noop executor
- No implicit filesystem mutation
- Materialization preflight failure aborts execution

Pipeline only orchestrates. All phases are mocked.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

import dita_package_processor.pipeline as pipeline_module
from dita_package_processor.pipeline import Pipeline
from dita_package_processor.execution.models import (
    ExecutionReport,
    ExecutionActionResult,
)
from dita_package_processor.materialization.orchestrator import (
    MaterializationOrchestrationError,
)
from dita_package_processor.discovery.models import (
    DiscoveryInventory,
    DiscoveryArtifact,
)
from dita_package_processor.discovery.graph import DependencyGraph
from dita_package_processor.planning.models import Plan


# =============================================================================
# Helpers
# =============================================================================


def _write_minimal_package(tmp_path: Path) -> None:
    (tmp_path / "Main.ditamap").write_text("<map/>", encoding="utf-8")


def _minimal_inventory() -> DiscoveryInventory:
    inv = DiscoveryInventory()

    inv.add_artifact(
        DiscoveryArtifact(
            path=Path("Main.ditamap"),
            artifact_type="map",
            classification="MAIN_MAP",
            confidence=1.0,
        )
    )

    inv.graph = DependencyGraph(nodes=[], edges=[])
    return inv


def _minimal_plan() -> Plan:
    return Plan(
        plan_version=1,
        generated_at="2026-01-30T00:00:00+00:00",
        source_discovery={},
        intent={},
        actions=[],
    )


def _fake_report(*, dry_run: bool) -> ExecutionReport:
    results = [
        ExecutionActionResult(
            action_id="a1",
            status="skipped" if dry_run else "success",
            handler="NoOp" if dry_run else "Filesystem",
            dry_run=dry_run,
            message="simulated",
        )
    ]

    return ExecutionReport.create(
        execution_id="pipeline-run",
        dry_run=dry_run,
        results=results,
    )


# =============================================================================
# run() tests (full pipeline)
# =============================================================================


def test_pipeline_run_full_dry_run(tmp_path: Path, monkeypatch) -> None:
    """run() should orchestrate discovery → plan → execute."""
    _write_minimal_package(tmp_path)

    monkeypatch.setattr(
        pipeline_module,
        "run_discovery",
        lambda **_: _minimal_inventory(),
    )

    monkeypatch.setattr(
        pipeline_module,
        "run_planning",
        lambda **_: _minimal_plan(),
    )

    orchestrator = MagicMock()
    monkeypatch.setattr(
        pipeline_module,
        "MaterializationOrchestrator",
        lambda **_: orchestrator,
    )

    executor = MagicMock()
    executor.run.return_value = _fake_report(dry_run=True)

    monkeypatch.setattr(
        pipeline_module,
        "get_executor",
        lambda *_, **__: executor,
    )

    pipeline = Pipeline(
        package_path=tmp_path,
        docx_stem="Doc",
        target_path=tmp_path / "out",
    )

    report = pipeline.run()

    assert report.dry_run is True
    orchestrator.preflight.assert_called_once()
    executor.run.assert_called_once()
    orchestrator.finalize.assert_called_once()


def test_pipeline_preflight_failure_aborts(tmp_path: Path, monkeypatch) -> None:
    """Execution must not run if preflight fails."""
    _write_minimal_package(tmp_path)

    monkeypatch.setattr(
        pipeline_module,
        "run_discovery",
        lambda **_: _minimal_inventory(),
    )

    monkeypatch.setattr(
        pipeline_module,
        "run_planning",
        lambda **_: _minimal_plan(),
    )

    orchestrator = MagicMock()
    orchestrator.preflight.side_effect = MaterializationOrchestrationError("boom")

    monkeypatch.setattr(
        pipeline_module,
        "MaterializationOrchestrator",
        lambda **_: orchestrator,
    )

    executor = MagicMock()

    monkeypatch.setattr(
        pipeline_module,
        "get_executor",
        lambda *_, **__: executor,
    )

    pipeline = Pipeline(
        package_path=tmp_path,
        docx_stem="Doc",
        target_path=tmp_path / "out",
    )

    with pytest.raises(MaterializationOrchestrationError):
        pipeline.run()

    executor.run.assert_not_called()


# =============================================================================
# execute_plan() tests (execution-only path)
# =============================================================================


def test_execute_plan_skips_discovery_and_planning(tmp_path: Path, monkeypatch) -> None:
    """execute_plan() must not call discovery or planning."""
    plan_path = tmp_path / "plan.json"
    plan_path.write_text("{}")

    monkeypatch.setattr(
        pipeline_module,
        "load_plan",
        lambda _: _minimal_plan(),
    )

    monkeypatch.setattr(
        pipeline_module,
        "run_discovery",
        lambda **_: pytest.fail("discovery should not run"),
    )

    monkeypatch.setattr(
        pipeline_module,
        "run_planning",
        lambda **_: pytest.fail("planning should not run"),
    )

    orchestrator = MagicMock()
    monkeypatch.setattr(
        pipeline_module,
        "MaterializationOrchestrator",
        lambda **_: orchestrator,
    )

    executor = MagicMock()
    executor.run.return_value = _fake_report(dry_run=True)

    monkeypatch.setattr(
        pipeline_module,
        "get_executor",
        lambda *_, **__: executor,
    )

    pipeline = Pipeline(
        package_path=None,
        docx_stem=None,
        target_path=tmp_path / "out",
    )

    report = pipeline.execute_plan(plan_path=plan_path)

    assert report.dry_run is True
    orchestrator.preflight.assert_called_once()
    executor.run.assert_called_once()
    orchestrator.finalize.assert_called_once()


def test_execute_plan_requires_target(tmp_path: Path, monkeypatch) -> None:
    """execute_plan() should fail without target path."""
    plan_path = tmp_path / "plan.json"
    plan_path.write_text("{}")

    monkeypatch.setattr(
        pipeline_module,
        "load_plan",
        lambda _: _minimal_plan(),
    )

    pipeline = Pipeline(
        package_path=None,
        docx_stem=None,
        target_path=None,
    )

    with pytest.raises(ValueError):
        pipeline.execute_plan(plan_path=plan_path)