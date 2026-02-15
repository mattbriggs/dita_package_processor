"""
Unit tests for the Pipeline orchestrator.

These tests validate:

- run() performs discovery → planning → materialization → execution
- execute_plan() skips discovery/planning
- Dry-run selects noop executor
- Apply mode selects filesystem executor
- Materialization preflight failure aborts execution
- Pipeline does not perform execution logic itself

All phases are mocked. Pipeline is orchestration only.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
from typing import Any, Dict

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
from dita_package_processor.knowledge.map_types import MapType


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
            classification=MapType.MAIN,
            confidence=1.0,
        )
    )

    inv.graph = DependencyGraph(nodes=[], edges=[])
    return inv


def _minimal_plan() -> Dict[str, Any]:
    """
    Return minimal plan dict matching planner contract.
    """
    return {
        "plan_version": 1,
        "generated_at": "2026-01-30T00:00:00+00:00",
        "source_discovery": {
            "path": "discovery.json",
            "schema_version": 1,
            "artifact_count": 1,
        },
        "intent": {},
        "actions": [],
        "invariants": [],
    }


def _fake_report(*, dry_run: bool) -> ExecutionReport:
    result = ExecutionActionResult(
        action_id="a1",
        status="skipped" if dry_run else "success",
        handler="DryRunExecutor" if dry_run else "FilesystemExecutor",
        dry_run=dry_run,
        message="simulated",
    )

    return ExecutionReport.create(
        execution_id="pipeline-execution",
        dry_run=dry_run,
        results=[result],
    )


# =============================================================================
# run() tests
# =============================================================================


def test_pipeline_run_full_dry_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
        apply=False,
    )

    report = pipeline.run()

    assert isinstance(report, ExecutionReport)
    assert report.dry_run is True

    orchestrator.preflight.assert_called_once()
    executor.run.assert_called_once()
    orchestrator.finalize.assert_called_once()


def test_pipeline_run_apply_mode_selects_filesystem_executor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    monkeypatch.setattr(
        pipeline_module,
        "MaterializationOrchestrator",
        lambda **_: MagicMock(),
    )

    executor = MagicMock()
    executor.run.return_value = _fake_report(dry_run=False)

    selected_modes: list[str] = []

    def fake_get_executor(name: str, **_: Any):
        selected_modes.append(name)
        return executor

    monkeypatch.setattr(
        pipeline_module,
        "get_executor",
        fake_get_executor,
    )

    pipeline = Pipeline(
        package_path=tmp_path,
        docx_stem="Doc",
        target_path=tmp_path / "out",
        apply=True,
    )

    pipeline.run()

    assert selected_modes == ["filesystem"]


def test_pipeline_preflight_failure_aborts_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    orchestrator.preflight.side_effect = (
        MaterializationOrchestrationError("boom")
    )

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
# execute_plan() tests
# =============================================================================


def test_execute_plan_skips_discovery_and_planning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
        lambda **_: pytest.fail("discovery must not run"),
    )

    monkeypatch.setattr(
        pipeline_module,
        "run_planning",
        lambda **_: pytest.fail("planning must not run"),
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

    assert isinstance(report, ExecutionReport)
    assert report.dry_run is True

    orchestrator.preflight.assert_called_once()
    executor.run.assert_called_once()
    orchestrator.finalize.assert_called_once()


def test_execute_plan_requires_target_path(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    plan_path.write_text("{}")

    pipeline = Pipeline(
        package_path=None,
        docx_stem=None,
        target_path=None,
    )

    with pytest.raises(ValueError):
        pipeline.execute_plan(plan_path=plan_path)