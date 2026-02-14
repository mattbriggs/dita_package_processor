"""
Tests for the target materialization builder.

These tests validate that the builder:

- creates the target directory deterministically
- is idempotent with respect to the filesystem
- fails loudly when the target is invalid or unusable
- emits observable lifecycle log messages
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dita_package_processor.materialization.builder import (
    TargetMaterializationBuilder,
    MaterializationError,
)
from dita_package_processor.materialization.orchestrator import (
    MaterializationManifest,
)
from dita_package_processor.materialization.collision import TargetArtifact


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _manifest(target_root: Path) -> MaterializationManifest:
    """
    Create a minimal valid manifest.

    Builder only needs target_root. Artifacts list may be empty.
    """
    return MaterializationManifest(
        target_root=target_root,
        artifacts=[],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_creates_target_directory(tmp_path: Path) -> None:
    """Builder should create the target directory if it does not exist."""
    target = tmp_path / "target"

    builder = TargetMaterializationBuilder(
        manifest=_manifest(target),
    )

    builder.build()

    assert target.exists()
    assert target.is_dir()


def test_idempotent_if_target_already_exists(tmp_path: Path) -> None:
    """Running the builder multiple times must be safe and idempotent."""
    target = tmp_path / "target"
    target.mkdir()

    builder = TargetMaterializationBuilder(
        manifest=_manifest(target),
    )

    builder.build()
    builder.build()  # should not raise

    assert target.exists()
    assert target.is_dir()


def test_fails_if_target_is_a_file(tmp_path: Path) -> None:
    """Builder must fail if the target path exists but is not a directory."""
    target = tmp_path / "target"
    target.write_text("not a directory", encoding="utf-8")

    builder = TargetMaterializationBuilder(
        manifest=_manifest(target),
    )

    with pytest.raises(MaterializationError):
        builder.build()


def test_fails_if_target_is_not_writable(tmp_path: Path) -> None:
    """
    Builder must fail if the target directory is not writable.

    Note: chmod-based permission tests can be flaky on CI,
    but are reliable locally.
    """
    target = tmp_path / "target"
    target.mkdir()
    target.chmod(0o400)  # read-only

    builder = TargetMaterializationBuilder(
        manifest=_manifest(target),
    )

    try:
        with pytest.raises(MaterializationError):
            builder.build()
    finally:
        target.chmod(0o700)


def test_logs_materialization_steps(caplog, tmp_path: Path) -> None:
    """Builder should emit lifecycle log messages."""
    target = tmp_path / "target"

    builder = TargetMaterializationBuilder(
        manifest=_manifest(target),
    )

    with caplog.at_level("INFO"):
        builder.build()

    messages = [r.message.lower() for r in caplog.records]

    assert any("materialization" in m for m in messages)
    assert any("target" in m for m in messages)