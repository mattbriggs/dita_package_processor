"""
End-to-end integration tests for the `run` CLI command.

These tests validate semantic pipeline execution via the `run` command.

They assert:
- CLI argument parsing
- Discovery → Planning → Execution wiring
- Execution report generation
- Safe execution behavior in absence of handlers

They do NOT assert filesystem mutation semantics yet.
"""

from __future__ import annotations

import json
from pathlib import Path

from dita_package_processor.cli import main as cli_main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_file(path: Path, content: str) -> None:
    """
    Write text content to a file, ensuring parent directories exist.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_run_end_to_end_pipeline_contract(tmp_path: Path, monkeypatch) -> None:
    """
    Validate the full pipeline contract via `run`.

    This test asserts:
    - CLI argument parsing
    - Discovery and planning complete
    - Execution is bound correctly
    - An execution report is generated when requested
    - Actions are represented in the report
    - Safety behavior is enforced
    """
    package_dir = tmp_path / "package"
    topics_dir = package_dir / "topics"
    topics_dir.mkdir(parents=True)

    # ------------------------------------------------------------
    # Minimal valid package structure
    # ------------------------------------------------------------

    _write_file(
        package_dir / "index.ditamap",
        """<?xml version="1.0" encoding="UTF-8"?>
<map>
  <mapref href="Main.ditamap"/>
</map>
""",
    )

    _write_file(
        package_dir / "Main.ditamap",
        """<?xml version="1.0" encoding="UTF-8"?>
<map>
  <title>Main</title>
  <topicref href="topics/a.dita"/>
</map>
""",
    )

    _write_file(
        topics_dir / "a.dita",
        """<?xml version="1.0" encoding="UTF-8"?>
<concept id="a">
  <title>A</title>
  <conbody/>
</concept>
""",
    )

    # ------------------------------------------------------------
    # Run CLI with explicit report output
    # ------------------------------------------------------------

    report_path = package_dir / "execution_report.json"

    argv = [
        "dita_package_processor",
        "run",
        "--apply",
        "--package",
        str(package_dir),
        "--docx-stem",
        "OutputDoc",
        "--report",
        str(report_path),
    ]

    monkeypatch.setattr("sys.argv", argv)
    exit_code = cli_main()

    assert exit_code == 0

    # ------------------------------------------------------------
    # Contract assertions
    # ------------------------------------------------------------

    assert report_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))

    # ExecutionReport contract
    assert "execution_id" in report
    assert "results" in report
    assert "summary" in report

    assert isinstance(report["results"], list)
    assert report["summary"]["total"] >= 1

    for result in report["results"]:
        assert "action_id" in result
        assert "status" in result
        assert "handler" in result
        assert "dry_run" in result

        # Because --apply was used, this must not be marked as dry-run
        assert result["dry_run"] is False

    # With handlers not implemented yet, FilesystemExecutor currently
    # returns skipped results. Safety failures are also acceptable.
    allowed_statuses = {"skipped", "failed"}
    assert all(r["status"] in allowed_statuses for r in report["results"])