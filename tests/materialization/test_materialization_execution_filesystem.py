"""
Filesystem execution integration test.

This test validates the FULL chain:

    Plan → Dispatcher → FilesystemExecutor → Registry → Handler → Disk

No mocks are used.

If this test passes:
    ✔ registry wiring works
    ✔ dispatcher works
    ✔ handler resolution works
    ✔ filesystem writes occur
    ✔ execution report is correct

If this test fails:
    something structural is still broken.
"""

from __future__ import annotations

from pathlib import Path

from dita_package_processor.execution.executors.filesystem import (
    FilesystemExecutor,
)
from dita_package_processor.execution.safety.policies import (
    MutationPolicy,
    OverwritePolicy,
)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _make_copy_plan(source: Path, target: Path) -> dict:
    """
    Minimal execution plan containing a single copy action.
    """
    return {
        "actions": [
            {
                "id": "copy-test",
                "type": "copy_file",  # semantic handler
                "target": str(target),
                "parameters": {
                    "source_path": str(source),
                    "target_path": str(target),
                },
                "reason": "unit test copy",
            }
        ]
    }


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


def test_filesystem_executor_copies_file(tmp_path: Path) -> None:
    """
    FilesystemExecutor should physically copy a file using handlers.

    This verifies:
        registry → handler → filesystem mutation
    """
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    source = sandbox / "source.txt"
    target = sandbox / "out" / "target.txt"

    source.write_text("hello world", encoding="utf-8")

    executor = FilesystemExecutor(
        sandbox_root=sandbox,
        policy=MutationPolicy(OverwritePolicy.REPLACE),
    )

    plan = _make_copy_plan(source, target)

    report = executor.run(
        execution_id="test-run",
        plan=plan,
    )

    # ------------------------------------------------------------------
    # File actually exists (this is the important part)
    # ------------------------------------------------------------------

    assert target.exists()
    assert target.read_text(encoding="utf-8") == "hello world"

    # ------------------------------------------------------------------
    # Execution report sanity
    # ------------------------------------------------------------------

    assert len(report.results) == 1

    result = report.results[0]

    assert result.status == "success"
    assert result.action_id == "copy-test"
    assert result.handler is not None