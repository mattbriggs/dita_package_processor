"""
Tests for target layout rule resolution.

These tests verify that:
- Artifact types map to deterministic target paths
- No filesystem access is required
- Unsupported artifact types fail loudly
"""

from pathlib import Path

import pytest

from dita_package_processor.planning.layout_rules import (
    LayoutRuleError,
    resolve_target_path,
)


def test_map_layout_rule() -> None:
    """
    Maps must be placed directly under the target root.
    """
    result = resolve_target_path(
        artifact_type="map",
        source_path=Path("Main.ditamap"),
        target_root=Path("/out"),
    )

    assert result == Path("/out/Main.ditamap")


def test_topic_layout_rule() -> None:
    """
    Topics must be placed under ``topics/``.
    """
    result = resolve_target_path(
        artifact_type="topic",
        source_path=Path("topics/a.dita"),
        target_root=Path("/out"),
    )

    assert result == Path("/out/topics/a.dita")


def test_media_layout_rule() -> None:
    """
    Media must be placed under ``media/``.
    """
    result = resolve_target_path(
        artifact_type="media",
        source_path=Path("images/foo.png"),
        target_root=Path("/out"),
    )

    assert result == Path("/out/media/foo.png")


def test_layout_rule_preserves_filename_only() -> None:
    """
    Directory structure from the source path is ignored.
    Only the filename is preserved.
    """
    result = resolve_target_path(
        artifact_type="topic",
        source_path=Path("nested/deep/thing.dita"),
        target_root=Path("/out"),
    )

    assert result == Path("/out/topics/thing.dita")


def test_unknown_artifact_type_fails() -> None:
    """
    Unsupported artifact types must raise LayoutRuleError.
    """
    with pytest.raises(LayoutRuleError):
        resolve_target_path(
            artifact_type="nonsense",
            source_path=Path("x.txt"),
            target_root=Path("/out"),
        )