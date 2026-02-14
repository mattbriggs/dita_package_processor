"""
Unit tests for materialization orchestrator.

These tests validate orchestration behavior:

- preflight runs builder -> validator -> collision detector -> manifest writer
- preflight aborts on failure
- finalize calls manifest writer
- lifecycle logging occurs

All collaborators are injected so the tests remain deterministic and
independent of filesystem or builder signature changes.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from dita_package_processor.materialization.orchestrator import (
    MaterializationOrchestrator,
    MaterializationOrchestrationError,
)
from dita_package_processor.planning.models import Plan, PlanAction, ActionType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_plan(tmp_path: Path) -> Plan:
    """
    Create a minimal realistic Plan.

    NOTE:
    Orchestrator now derives artifacts from action targets,
    so we include one trivial action.
    """
    return Plan(
        plan_version=1,
        generated_at="2026-01-30T00:00:00+00:00",
        source_discovery={},
        intent={},
        actions=[
            PlanAction(
                id="a1",
                type=ActionType.COPY_MAP.value,
                target=str(tmp_path / "dummy.ditamap"),
                reason="test",
                parameters={},
                derived_from_evidence=[],
            )
        ],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_orchestrator_preflight_runs_all_steps(tmp_path: Path) -> None:
    """
    Preflight should invoke builder → validator → collision → manifest.
    """
    builder = MagicMock()
    validator = MagicMock()
    collision_detector = MagicMock()
    manifest_writer = MagicMock()

    orchestrator = MaterializationOrchestrator(
        plan=_minimal_plan(tmp_path),
        target_root=tmp_path / "target",
        builder=builder,
        validator=validator,
        collision_detector=collision_detector,
        manifest_writer=manifest_writer,
    )

    orchestrator.preflight()

    builder.build.assert_called_once()
    validator.validate_preflight.assert_called_once()
    collision_detector.detect.assert_called_once()
    manifest_writer.write_preflight.assert_called_once()


def test_orchestrator_preflight_stops_on_failure(tmp_path: Path) -> None:
    """
    Any collaborator failure must abort preflight and bubble up as
    MaterializationOrchestrationError.
    """
    builder = MagicMock()
    validator = MagicMock()
    validator.validate_preflight.side_effect = ValueError("boom")

    orchestrator = MaterializationOrchestrator(
        plan=_minimal_plan(tmp_path),
        target_root=tmp_path / "target",
        builder=builder,
        validator=validator,
        collision_detector=MagicMock(),
        manifest_writer=MagicMock(),
    )

    with pytest.raises(MaterializationOrchestrationError):
        orchestrator.preflight()

    builder.build.assert_called_once()
    validator.validate_preflight.assert_called_once()


def test_orchestrator_finalize_calls_manifest_writer(tmp_path: Path) -> None:
    """
    Finalize must call manifest writer final hook exactly once.
    """
    manifest_writer = MagicMock()

    orchestrator = MaterializationOrchestrator(
        plan=_minimal_plan(tmp_path),
        target_root=tmp_path / "target",
        builder=MagicMock(),
        validator=MagicMock(),
        collision_detector=MagicMock(),
        manifest_writer=manifest_writer,
    )

    fake_report = MagicMock()
    orchestrator.finalize(execution_report=fake_report)

    manifest_writer.write_final.assert_called_once_with(
        execution_report=fake_report
    )


def test_orchestrator_emits_lifecycle_logs(caplog, tmp_path: Path) -> None:
    """
    Preflight should emit start/complete lifecycle logs for observability.
    """
    orchestrator = MaterializationOrchestrator(
        plan=_minimal_plan(tmp_path),
        target_root=tmp_path / "target",
        builder=MagicMock(),
        validator=MagicMock(),
        collision_detector=MagicMock(),
        manifest_writer=MagicMock(),
    )

    with caplog.at_level("INFO"):
        orchestrator.preflight()

    messages = [r.message.lower() for r in caplog.records]

    assert any("materialization preflight start" in m for m in messages)
    assert any("materialization preflight complete" in m for m in messages)