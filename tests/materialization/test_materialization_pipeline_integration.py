"""
Integration tests for the materialization phase within the pipeline.

These tests validate cross-module contracts:

- Materialization preflight failure blocks execution
- Materialization manifests are deterministic
- Target preparation is not invoked on materialization failure

These are integration-level tests:
- real Pipeline
- real MaterializationOrchestrator (behavior mocked, not replaced)
- execution layer observed but not executed
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import dita_package_processor.pipeline as pipeline_module
from dita_package_processor.pipeline import Pipeline
from dita_package_processor.materialization.orchestrator import (
    MaterializationOrchestrationError,
    MaterializationOrchestrator,
)
from dita_package_processor.execution.models import ExecutionReport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_minimal_package(root: Path) -> None:
    """Create a minimal valid DITA package."""
    (root / "index.ditamap").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<map>
  <mapref href="main.ditamap"/>
</map>
""",
        encoding="utf-8",
    )

    (root / "main.ditamap").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<map>
  <title>Main</title>
</map>
""",
        encoding="utf-8",
    )



def _fake_inventory():
    """
    Minimal DiscoveryInventory-shaped object that satisfies
    Pipeline MAIN_MAP invariant.

    Pipeline requires exactly one artifact where:
        artifact_type == "map"
        classification == "MAIN_MAP"
    """
    main_map = SimpleNamespace(
        artifact_type="map",
        classification="MAIN_MAP",
        path="main.ditamap",
    )

    return SimpleNamespace(
        artifacts=[main_map],
        graph=None,
    )


def _fake_report(*, dry_run: bool) -> ExecutionReport:
    """Deterministic fake execution report."""
    return ExecutionReport.create(
        execution_id="test",
        dry_run=dry_run,
        results=[],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_materialization_preflight_blocks_execution(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """
    If materialization preflight fails, execution MUST NOT run.
    """
    _write_minimal_package(tmp_path)
    target = tmp_path / "out"

    monkeypatch.setattr(
        pipeline_module,
        "run_discovery",
        lambda package_path: _fake_inventory(),
    )

    monkeypatch.setattr(
        pipeline_module,
        "run_planning",
        lambda **kwargs: MagicMock(actions=[]),
    )

    orchestrator = MagicMock()
    orchestrator.preflight.side_effect = MaterializationOrchestrationError(
        "collision detected"
    )

    monkeypatch.setattr(
        pipeline_module,
        "MaterializationOrchestrator",
        lambda **kwargs: orchestrator,
    )

    executor = MagicMock()

    monkeypatch.setattr(
        pipeline_module,
        "get_executor",
        lambda *args, **kwargs: executor,
    )

    pipeline = Pipeline(
        package_path=tmp_path,
        docx_stem="TestDoc",
        target_path=target,
    )

    with pytest.raises(MaterializationOrchestrationError):
        pipeline.run()

    executor.run.assert_not_called()


# ---------------------------------------------------------------------------


def test_materialization_manifest_is_deterministic(tmp_path: Path) -> None:
    """
    Identical inputs must produce identical manifests.

    We use the real orchestrator here because manifest generation is internal
    and deterministic.
    """
    plan = MagicMock(actions=[])

    o1 = MaterializationOrchestrator(
        plan=plan,
        target_root=tmp_path,
    )

    o2 = MaterializationOrchestrator(
        plan=plan,
        target_root=tmp_path,
    )

    # Compare simple structural properties instead of legacy to_dict()
    assert o1.manifest.target_root == o2.manifest.target_root
    assert o1.manifest.artifacts == o2.manifest.artifacts


# ---------------------------------------------------------------------------


def test_builder_not_invoked_on_materialization_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """
    Target preparation must not occur if materialization fails.

    Observable contract:
    - materialization finalize is not called
    - execution is not invoked
    """
    _write_minimal_package(tmp_path)
    target = tmp_path / "out"

    monkeypatch.setattr(
        pipeline_module,
        "run_discovery",
        lambda package_path: _fake_inventory(),
    )

    monkeypatch.setattr(
        pipeline_module,
        "run_planning",
        lambda **kwargs: MagicMock(actions=[]),
    )

    orchestrator = MagicMock()
    orchestrator.preflight.side_effect = MaterializationOrchestrationError(
        "collision detected"
    )

    monkeypatch.setattr(
        pipeline_module,
        "MaterializationOrchestrator",
        lambda **kwargs: orchestrator,
    )

    executor = MagicMock()

    monkeypatch.setattr(
        pipeline_module,
        "get_executor",
        lambda *args, **kwargs: executor,
    )

    pipeline = Pipeline(
        package_path=tmp_path,
        docx_stem="TestDoc",
        target_path=target,
    )

    with pytest.raises(MaterializationOrchestrationError):
        pipeline.run()

    # 🔒 Critical guarantees
    orchestrator.finalize.assert_not_called()
    executor.run.assert_not_called()