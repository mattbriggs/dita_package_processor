"""
Tests for planning target layout resolution.

These tests validate that layout rules:

- Produce deterministic target paths
- Respect artifact type
- Preserve filenames
- Prevent source-path mirroring unless explicitly allowed
- Contain no filesystem or discovery logic
"""

from pathlib import Path

import pytest

from dita_package_processor.planning.layout_rules import LayoutRuleError, resolve_target_path


def test_map_target_layout() -> None:
    """
    Maps should be placed at the root of the target structure.
    """
    source = Path("index.ditamap")
    target_root = Path("target")

    target = resolve_target_path(
        artifact_type="map",
        source_path=source,
        target_root=target_root,
    )

    assert target == Path("target/index.ditamap")


def test_topic_target_layout() -> None:
    """
    Topics should be placed under a topics directory.
    """
    source = Path("topics/a.dita")
    target_root = Path("target")

    target = resolve_target_path(
        artifact_type="topic",
        source_path=source,
        target_root=target_root,
    )

    assert target == Path("target/topics/a.dita")


def test_media_target_layout() -> None:
    """
    Media files should be placed under a media directory.
    """
    source = Path("images/logo.png")
    target_root = Path("target")

    target = resolve_target_path(
        artifact_type="media",
        source_path=source,
        target_root=target_root,
    )

    assert target == Path("target/media/logo.png")


def test_filename_is_preserved() -> None:
    """
    Layout rules must preserve the original filename.
    """
    source = Path("topics/subdir/example.dita")
    target_root = Path("target")

    target = resolve_target_path(
        artifact_type="topic",
        source_path=source,
        target_root=target_root,
    )

    assert target.name == "example.dita"


def test_target_differs_from_source() -> None:
    """
    Target paths must not equal source paths.
    """
    source = Path("topics/a.dita")
    target_root = Path("target")

    target = resolve_target_path(
        artifact_type="topic",
        source_path=source,
        target_root=target_root,
    )

    assert target != source


def test_invalid_artifact_type_fails() -> None:
    """
    Unknown artifact types must fail loudly with a LayoutRuleError.
    """
    with pytest.raises(LayoutRuleError):
        resolve_target_path(
            artifact_type="unknown",
            source_path=Path("file.xyz"),
            target_root=Path("target"),
        )