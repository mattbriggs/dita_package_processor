"""
Unit tests for MaterializationOrchestrator.

These tests validate orchestration behavior:

- preflight runs builder -> validator -> collision detector -> manifest writer
- preflight aborts on failure and wraps errors
- finalize calls manifest writer final hook
- lifecycle logging occurs

All collaborators are injected so tests remain deterministic and
independent of filesystem or builder signature changes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from dita_package_processor.materialization.orchestrator import (
    MaterializationOrchestrator,
    MaterializationOrchestrationError,
)
from dita_package_processor.planning.models import (
    Plan,
    PlanAction,
    ActionType,
)


# =============================================================================
# Helpers
# =============================================================================


def _minimal_plan(tmp_path: Path) -> Plan:
    """
    Create a minimal realistic Plan.

    Plan now requires:
    - generated_at: datetime (UTC-aware)
    - valid action list
    """
    return Plan(
        plan_version=1,
        generated_at=datetime.now(timezone.utc),
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


# =============================================================================
# Tests
# =============================================================================


def test_preflight_runs_all_collaborators(tmp_path: Path) -> None:
    """
    Preflight must invoke collaborators.

    Expected:
        builder.build()
        validator.validate_preflight(...)
        collision_detector.detect(...)
        manifest_writer.write_preflight(...)
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


def test_preflight_aborts_and_wraps_failure(tmp_path: Path) -> None:
    """
    Any collaborator failure must abort preflight and raise
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


def test_finalize_calls_manifest_writer(tmp_path: Path) -> None:
    """
    Finalize must call manifest_writer.write_final exactly once.
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


def test_preflight_emits_lifecycle_logs(caplog, tmp_path: Path) -> None:
    """
    Preflight must emit lifecycle observability logs.
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

    messages = [record.message.lower() for record in caplog.records]

    assert any("preflight start" in m for m in messages)
    assert any("preflight complete" in m for m in messages)