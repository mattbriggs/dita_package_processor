"""
Tests for the `discover` CLI subcommand.

These tests validate that the discovery CLI:
- scans a DITA package directory
- emits human-readable summaries by default
- emits JSON output with --json
- writes JSON to --output
- respects --quiet
- fails cleanly on invalid input
- exposes invariant validation results
- includes media artifacts in both summary and JSON output

Discovery logic itself is tested elsewhere. This module
verifies CLI wiring and output contracts only.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    """
    Run the dita_package_processor CLI with the given arguments.
    """
    return subprocess.run(
        [sys.executable, "-m", "dita_package_processor", *args],
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def dita_package(tmp_path: Path) -> Path:
    """
    Create a minimal fake DITA package directory including media.
    """
    package_dir = tmp_path / "dita"
    package_dir.mkdir()

    # DITA files
    (package_dir / "index.ditamap").write_text("<map></map>", encoding="utf-8")
    (package_dir / "topic.dita").write_text("<topic></topic>", encoding="utf-8")

    # Media file
    media_dir = package_dir / "media"
    media_dir.mkdir()
    (media_dir / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    return package_dir


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_discover_runs_successfully(dita_package: Path) -> None:
    result = _run_cli(["discover", "--package", str(dita_package)])
    assert result.returncode == 0


def test_discover_emits_human_summary(dita_package: Path) -> None:
    """
    Summary must reflect the *true* schema:
        Map, Topic, Media only.
    """
    result = _run_cli(["discover", "--package", str(dita_package)])

    assert result.returncode == 0
    assert "Discovery summary" in result.stdout
    assert "Map" in result.stdout
    assert "Topic" in result.stdout
    assert "Media" in result.stdout

    # These must NOT exist anymore
    assert "Total Artifacts" not in result.stdout
    assert "Relationship Count" not in result.stdout


def test_discover_json_flag_emits_json_with_media(dita_package: Path) -> None:
    """
    --json prints the discovery contract + invariants to stdout.
    """
    result = _run_cli(["discover", "--package", str(dita_package), "--json"])
    assert result.returncode == 0

    parsed = json.loads(result.stdout)

    # Root contract
    assert "artifacts" in parsed
    assert "relationships" in parsed
    assert "summary" in parsed
    assert "invariants" in parsed

    # Summary schema
    summary = parsed["summary"]
    assert summary == {
        "map": 1,
        "topic": 1,
        "media": 1,
    }

    # Media artifact must be serialized
    media = [
        a for a in parsed["artifacts"]
        if a["artifact_type"] == "media"
    ]
    assert len(media) == 1

    media = media[0]
    assert media["path"] == "media/logo.png"
    assert media["artifact_type"] == "media"
    assert media["classification"] is None
    assert media["confidence"] is None
    assert "size_bytes" in media["metadata"]
    assert "extension" in media["metadata"]

    # Invariants block
    invariants = parsed["invariants"]
    assert "violations" in invariants
    assert "passed" in invariants
    assert isinstance(invariants["passed"], bool)


def test_discover_output_file_written(
    dita_package: Path,
    tmp_path: Path,
) -> None:
    """
    --output writes discovery JSON exactly as --json would emit.
    """
    output_path = tmp_path / "discovery.json"

    result = _run_cli(
        [
            "discover",
            "--package",
            str(dita_package),
            "--output",
            str(output_path),
        ]
    )

    assert result.returncode == 0
    assert output_path.exists()

    parsed = json.loads(output_path.read_text(encoding="utf-8"))

    assert "artifacts" in parsed
    assert "relationships" in parsed
    assert "summary" in parsed
    assert "invariants" in parsed

    assert any(
        a["artifact_type"] == "media"
        for a in parsed["artifacts"]
    )


def test_discover_quiet_suppresses_stdout(dita_package: Path) -> None:
    result = _run_cli(
        [
            "discover",
            "--package",
            str(dita_package),
            "--quiet",
        ]
    )

    assert result.returncode == 0
    assert result.stdout == ""


def test_discover_missing_package_fails() -> None:
    result = _run_cli(
        [
            "discover",
            "--package",
            "does-not-exist",
        ]
    )

    assert result.returncode != 0
    assert result.stderr != ""


def test_discover_non_directory_fails(tmp_path: Path) -> None:
    fake_file = tmp_path / "not_a_dir"
    fake_file.write_text("nope", encoding="utf-8")

    result = _run_cli(
        [
            "discover",
            "--package",
            str(fake_file),
        ]
    )

    assert result.returncode != 0
    assert "directory" in result.stderr.lower()