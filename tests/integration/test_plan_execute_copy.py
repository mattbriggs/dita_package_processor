"""
Integration tests for execution of copy-style plans.

These tests validate the execution contract:

- Execution accepts dictionary plans only
- Dry-run produces an execution report
- Apply-mode produces an execution report
- Results are structurally valid even when handlers are not implemented
- No crashes occur at the execution boundary
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

import pytest

from dita_package_processor.execution.executors.filesystem import FilesystemExecutor
from dita_package_processor.execution.dry_run_executor import DryRunExecutor
from dita_package_processor.execution.safety.policies import MutationPolicy, OverwritePolicy


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_dita_package(tmp_path: Path) -> Path:
    """
    Minimal DITA-style filesystem.
    """
    package = tmp_path / "package"
    topics = package / "topics"
    media = package / "media"

    topics.mkdir(parents=True)
    media.mkdir(parents=True)

    (topics / "topic1.dita").write_text(
        "<topic><title>Test</title></topic>", encoding="utf-8"
    )
    (media / "image.png").write_bytes(b"\x89PNG\r\n\x1a\nfakepng")

    return package


@pytest.fixture
def execution_target(tmp_path: Path) -> Path:
    target = tmp_path / "output"
    target.mkdir()
    return target


# ---------------------------------------------------------------------------
# Execution Plan Builder
# ---------------------------------------------------------------------------


def _build_execution_plan(source: Path, target: Path) -> Dict[str, Any]:
    """
    Build a pure execution-layer plan dictionary.

    This bypasses planning models completely and asserts the
    execution contract directly.
    """
    actions: List[Dict[str, Any]] = []

    for path in source.rglob("*"):
        if path.is_file():
            rel = path.relative_to(source)
            actions.append(
                {
                    "id": f"copy-{rel}",
                    "type": "copy_file",
                    "target": str(target / rel),
                    "parameters": {
                        "source_path": str(path),
                        "target_path": str(target / rel),
                    },
                    "reason": "integration copy test",
                }
            )

    return {"actions": actions}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_dry_run_execution_produces_report(
    sample_dita_package: Path,
    execution_target: Path,
) -> None:
    """
    Dry-run execution must produce a valid execution report.
    No filesystem mutation is expected.
    """
    plan = _build_execution_plan(sample_dita_package, execution_target)

    executor = DryRunExecutor()

    report = executor.run(
        execution_id="dry-run-test",
        plan=plan,
    )

    assert report.execution_id == "dry-run-test"
    assert report.dry_run is True
    assert len(report.results) == len(plan["actions"])

    for result in report.results:
        assert result.status in {"skipped", "failed"}
        assert result.dry_run is True
        assert result.handler is not None


def test_apply_execution_produces_report_even_without_handlers(
    sample_dita_package: Path,
    execution_target: Path,
) -> None:
    """
    Apply-mode execution must still produce a report even if handlers
    are not yet implemented. No mutation is allowed because the policy
    is DENY.
    """
    plan = _build_execution_plan(sample_dita_package, execution_target)

    policy = MutationPolicy(OverwritePolicy.DENY)

    executor = FilesystemExecutor(
        sandbox_root=execution_target,
        policy=policy,
    )

    report = executor.run(
        execution_id="apply-test",
        plan=plan,
    )

    assert report.execution_id == "apply-test"
    assert report.dry_run is False
    assert len(report.results) == len(plan["actions"])

    for result in report.results:
        assert result.status in {"skipped", "failed"}
        assert result.dry_run is False


def test_execution_contract_is_future_proofed(
    sample_dita_package: Path,
    execution_target: Path,
) -> None:
    """
    This test intentionally does NOT assert files exist yet.

    Once copy handlers are implemented, this test can be extended to:

        assert copied.exists()

    For now it asserts the execution boundary is stable.
    """
    plan = _build_execution_plan(sample_dita_package, execution_target)

    policy = MutationPolicy(OverwritePolicy.DENY)

    executor = FilesystemExecutor(
        sandbox_root=execution_target,
        policy=policy,
    )

    report = executor.run(
        execution_id="future-proof-test",
        plan=plan,
    )

    assert len(report.results) == len(plan["actions"])