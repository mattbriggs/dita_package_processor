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
    something structural is broken.
"""

from __future__ import annotations

from pathlib import Path

from dita_package_processor.execution.executors.filesystem import (
    FilesystemExecutor,
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
                "type": "copy_file",
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
    source_root = tmp_path / "src"
    sandbox_root = tmp_path / "out"

    source_root.mkdir()
    sandbox_root.mkdir()

    source = source_root / "source.txt"
    target = sandbox_root / "target.txt"

    source.write_text("hello world", encoding="utf-8")

    executor = FilesystemExecutor(
        source_root=source_root,
        sandbox_root=sandbox_root,
        apply=True,  # allow mutation
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
    assert report.dry_run is False